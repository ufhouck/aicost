from __future__ import annotations

from aicost.calculator import get_effective_rates, get_pricing_data

GATEWAY_KEYWORDS = {"gateway", "proxy", "governance", "observability", "sso", "audit", "audit-logs", "router"}


def _effective_sort_cost(model: dict) -> float:
    eff = get_effective_rates(model)
    for val in (eff["input_per_1m"], eff["per_unit"], eff["monthly"]):
        if val is not None:
            return val
    return float("inf")


def recommend_models(
    task_description: str,
    limit: int = 3,
    model_type: str | None = None,
    max_input_cost: float | None = None,
    include_legacy: bool = False,
) -> list[dict]:
    """
    Recommends models based on keyword/tag relevance and cost efficiency.
    Excludes legacy models and enterprise gateways by default unless explicitly requested.
    """
    if not task_description or not task_description.strip():
        return []

    models = get_pricing_data()
    task_desc_lower = task_description.lower()
    words = {
        w.strip()
        for w in task_desc_lower.replace(",", " ").replace(".", " ").replace("/", " ").split()
        if w.strip()
    }

    wants_legacy = include_legacy or ("legacy" in words)
    wants_gateway = bool(words & GATEWAY_KEYWORDS) or (model_type and model_type.lower() == "gateway")

    scored_models: list[tuple[int, float, dict]] = []

    for model in models:
        m_type = str(model.get("type", "text")).lower()
        tags = [str(t).lower() for t in model.get("tags", [])]
        desc = str(model.get("description", "")).lower()

        if not wants_legacy and "legacy" in tags:
            continue
        if m_type == "gateway" and not wants_gateway:
            continue
        if model_type and m_type != model_type.strip().lower():
            continue

        if max_input_cost is not None:
            eff = get_effective_rates(model)
            ref_cost = eff["input_per_1m"] if eff["input_per_1m"] is not None else eff["per_unit"]
            if ref_cost is None or ref_cost > max_input_cost:
                continue

        score = 0
        for word in words:
            if word in tags:
                score += 3
            elif word == m_type or word == str(model.get("provider", "")).lower():
                score += 2
            elif len(word) > 2 and word in desc:
                score += 1

        if score > 0:
            if ("cheap" in words or "budget" in words or "low-cost" in task_desc_lower) and "cheap" in tags:
                score += 5
            if "fast" in words and "fast" in tags:
                score += 2
            if ("agent" in task_desc_lower or "agentic" in words) and "agentic" in tags:
                score += 4
            if ("vision" in words or "image" in words or "ocr" in words) and (
                "vision" in tags or "image" in tags or "ocr" in tags
            ):
                score += 4

            scored_models.append((score, _effective_sort_cost(model), model))

    # Highest score first; break ties by lowest effective cost
    scored_models.sort(key=lambda item: (-item[0], item[1]))
    return [m[2] for m in scored_models[: max(1, limit)]]
