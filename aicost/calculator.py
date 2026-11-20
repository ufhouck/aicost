from __future__ import annotations

import copy
import difflib
import json
import time
from pathlib import Path
import requests

CACHE_DIR = Path.home() / ".aicost"
CACHE_FILE = CACHE_DIR / "pricing_cache.json"
LIVE_CATALOG_CACHE_FILE = CACHE_DIR / "live_catalog_cache.json"
CACHE_TTL_SECONDS = 7 * 24 * 3600       # 7 days for curated pricing.json
LIVE_CACHE_TTL_SECONDS = 24 * 3600      # 24 hours for live OpenRouter catalog

REMOTE_PRICING_URL = "https://raw.githubusercontent.com/ufhouck/aicost/main/data/pricing.json"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "x-ai": "xAI",
    "deepseek": "DeepSeek",
    "qwen": "Alibaba Qwen",
    "meta-llama": "Meta",
    "mistralai": "Mistral",
    "moonshotai": "Moonshot",
    "minimax": "MiniMax",
    "perplexity": "Perplexity",
    "amazon": "Amazon",
    "cohere": "Cohere",
    "nvidia": "NVIDIA",
    "microsoft": "Microsoft",
    "ai21": "AI21",
    "black-forest-labs": "Black Forest Labs",
}

UNIT_LABELS = {
    "1m_tokens": "1M tokens",
    "image": "image",
    "second": "sec",
    "minute": "min",
    "song": "song",
    "clip": "clip",
    "1m_chars": "1M chars",
    "month": "mo",
    "custom": "custom",
}


def format_unit_label(billing_unit: str | None, model_type: str = "text") -> str:
    if billing_unit and billing_unit in UNIT_LABELS:
        return UNIT_LABELS[billing_unit]
    if model_type == "text":
        return "1M tokens"
    if model_type == "gateway":
        return "mo"
    return "unit"


def fetch_remote_pricing() -> dict:
    """Fetches the latest curated pricing database from GitHub and updates local cache."""
    try:
        response = requests.get(REMOTE_PRICING_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or "models" not in data:
            return {}

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
    except Exception:
        return {}


def _convert_openrouter_entry(rm: dict) -> dict | None:
    """Converts a raw OpenRouter /api/v1/models object into an AICost v2 model dict."""
    or_id = str(rm.get("id") or "").strip()
    if not or_id or ":free" in or_id or ":batch" in or_id:
        return None

    pricing = rm.get("pricing") or {}
    try:
        in_cost = float(pricing.get("prompt", 0)) * 1_000_000
        out_cost = float(pricing.get("completion", 0)) * 1_000_000
    except (TypeError, ValueError):
        return None

    if in_cost <= 0 and out_cost <= 0:
        return None

    prefix = or_id.split("/", 1)[0].lower() if "/" in or_id else "openrouter"
    short_id = or_id.split("/", 1)[1] if "/" in or_id else or_id
    provider_name = PROVIDER_DISPLAY_NAMES.get(prefix, prefix.replace("-", " ").title())

    arch = rm.get("architecture") or {}
    in_mods = [str(x).lower() for x in (arch.get("input_modalities") or [])]
    ctx = int(rm.get("context_length") or 0)

    tags = ["live-catalog"]
    if "image" in in_mods:
        tags.extend(["vision", "multimodal"])
    if ctx >= 500_000:
        tags.append("long-context")
    if in_cost <= 0.35:
        tags.extend(["cheap", "fast"])

    entry: dict = {
        "id": or_id,
        "aliases": [short_id],
        "openrouter_id": or_id.lower(),
        "provider": provider_name,
        "source_type": "direct",
        "type": "text",
        "billing_unit": "1m_tokens",
        "context_window": ctx if ctx > 0 else None,
        "cost_per_1m_input_tokens": round(in_cost, 4),
        "cost_per_1m_output_tokens": round(out_cost, 4),
        "tags": tags,
        "description": str(rm.get("name") or or_id),
    }

    if pricing.get("input_cache_read") is not None:
        try:
            cache_cost = round(float(pricing["input_cache_read"]) * 1_000_000, 4)
            if cache_cost > 0:
                entry["cost_per_1m_cached_input_tokens"] = cache_cost
        except (TypeError, ValueError):
            pass

    return entry


def fetch_live_catalog() -> list[dict]:
    """Fetches 400+ live models from OpenRouter's public API and caches them locally."""
    try:
        response = requests.get(OPENROUTER_MODELS_URL, timeout=8)
        response.raise_for_status()
        raw_list = response.json().get("data", [])
        if not isinstance(raw_list, list):
            return []

        converted: list[dict] = []
        for rm in raw_list:
            if isinstance(rm, dict):
                item = _convert_openrouter_entry(rm)
                if item:
                    converted.append(item)

        if converted:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(LIVE_CATALOG_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "models": converted}, f)
        return converted
    except Exception:
        return []


def get_live_catalog(auto_fetch: bool = True) -> list[dict]:
    """Loads the 400+ live model catalog from 24h local cache or fetches on demand."""
    stale_models: list[dict] = []
    if LIVE_CATALOG_CACHE_FILE.exists():
        try:
            with open(LIVE_CATALOG_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            stale_models = cached.get("models", [])
            if stale_models and (time.time() - float(cached.get("timestamp", 0))) < LIVE_CACHE_TTL_SECONDS:
                return stale_models
        except Exception:
            pass

    if auto_fetch:
        fresh = fetch_live_catalog()
        if fresh:
            return fresh

    return stale_models


def _load_bundled_data() -> dict:
    """Loads pricing.json bundled inside the wheel or from the repository root."""
    pkg_dir = Path(__file__).resolve().parent
    potential_paths = [
        pkg_dir / "data" / "pricing.json",
        pkg_dir.parent / "data" / "pricing.json",
        Path.cwd() / "data" / "pricing.json",
    ]

    for path in potential_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "models" in data:
                    return data
            except Exception:
                continue
    return {}


def _load_cached_data() -> dict:
    """Loads cached curated pricing data if fresh (< 7 days old)."""
    if CACHE_FILE.exists():
        try:
            if (time.time() - CACHE_FILE.stat().st_mtime) < CACHE_TTL_SECONDS:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "models" in data:
                    return data
        except Exception:
            pass
    return {}


def get_all_data() -> dict:
    """
    Retrieves curated pricing data preferring the newer of fresh cache or bundled package data.
     Ensures package upgrades never serve stale cached schemas/models.
    """
    bundled = _load_bundled_data()
    cached = _load_cached_data()

    if cached and bundled:
        cached_ver = (str(cached.get("last_updated", "")), len(cached.get("models", [])))
        bundled_ver = (str(bundled.get("last_updated", "")), len(bundled.get("models", [])))
        if cached_ver >= bundled_ver:
            return cached
        return bundled

    if cached:
        return cached
    if bundled:
        return bundled

    return fetch_remote_pricing()


def get_pricing_data(include_live: bool = False) -> list[dict]:
    """Returns curated models, optionally merged with 400+ live OpenRouter models."""
    curated = get_all_data().get("models", [])
    if not include_live:
        return curated

    known_keys: set[str] = set()
    for m in curated:
        known_keys.add(str(m.get("id", "")).lower())
        if m.get("openrouter_id"):
            known_keys.add(str(m["openrouter_id"]).lower())

    merged = list(curated)
    for lm in get_live_catalog(auto_fetch=True):
        lid = str(lm.get("id", "")).lower()
        if lid not in known_keys:
            merged.append(lm)
            known_keys.add(lid)
    return merged


def get_pricing_metadata() -> dict:
    """Returns root metadata for the pricing database."""
    data = get_all_data()
    live_cached = get_live_catalog(auto_fetch=False)
    return {
        "schema_version": data.get("schema_version", "2.1"),
        "last_updated": data.get("last_updated", "Unknown"),
        "model_count": len(data.get("models", [])),
        "live_catalog_cached_count": len(live_cached),
    }


def get_effective_rates(model: dict) -> dict[str, float | None]:
    """Returns base and fee-adjusted USD rates for a model."""
    fee = float(model.get("platform_fee", 0.0) or 0.0)
    multiplier = 1.0 + fee

    in_base = model.get("cost_per_1m_input_tokens")
    cached_base = model.get("cost_per_1m_cached_input_tokens")
    out_base = model.get("cost_per_1m_output_tokens")
    unit_base = model.get("cost_per_unit")
    monthly_base = model.get("fixed_monthly_cost")

    return {
        "platform_fee": fee,
        "input_per_1m": (float(in_base) * multiplier) if in_base is not None else None,
        "cached_input_per_1m": (float(cached_base) * multiplier) if cached_base is not None else None,
        "output_per_1m": (float(out_base) * multiplier) if out_base is not None else None,
        "per_unit": (float(unit_base) * multiplier) if unit_base is not None else None,
        "monthly": float(monthly_base) if monthly_base is not None else None,
    }


def filter_models(
    provider: str | None = None,
    model_type: str | None = None,
    tag: str | None = None,
    include_legacy: bool = True,
    include_live: bool = False,
    sort_by: str | None = None,
) -> list[dict]:
    """Filters and optionally sorts models from the pricing database."""
    models = get_pricing_data(include_live=include_live)
    results: list[dict] = []

    for m in models:
        tags_lower = [str(t).lower() for t in m.get("tags", [])]
        if not include_legacy and "legacy" in tags_lower:
            continue
        if provider and m.get("provider", "").lower() != provider.strip().lower():
            continue
        if model_type and m.get("type", "text").lower() != model_type.strip().lower():
            continue
        if tag and tag.strip().lower() not in tags_lower:
            continue
        results.append(m)

    if sort_by:
        key = sort_by.strip().lower()
        if key == "id":
            results.sort(key=lambda x: x.get("id", "").lower())
        elif key == "provider":
            results.sort(key=lambda x: (x.get("provider", "").lower(), x.get("id", "").lower()))
        elif key in ("input", "cost", "price"):
            def _cost_key(x: dict) -> float:
                eff = get_effective_rates(x)
                for candidate in (eff["input_per_1m"], eff["per_unit"], eff["monthly"]):
                    if candidate is not None:
                        return candidate
                return float("inf")
            results.sort(key=_cost_key)
        elif key == "output":
            def _out_key(x: dict) -> float:
                eff = get_effective_rates(x)
                for candidate in (eff["output_per_1m"], eff["per_unit"], eff["monthly"]):
                    if candidate is not None:
                        return candidate
                return float("inf")
            results.sort(key=_out_key)

    return results


def calculate_text_cost(
    model: dict,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    batch: bool = False,
    include_fee: bool = True,
) -> float:
    """Calculates effective USD cost for text models (including platform fees by default)."""
    breakdown = calculate_cost_breakdown(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        batch=batch,
    )
    return breakdown["total_usd"] if include_fee else breakdown["base_usd"]


def calculate_image_cost(model: dict, units: float, include_fee: bool = True) -> float:
    """Calculates effective USD cost for unit-based models (image, video, audio, gateway)."""
    breakdown = calculate_cost_breakdown(model=model, units=units)
    return breakdown["total_usd"] if include_fee else breakdown["base_usd"]


def calculate_cost_breakdown(
    model: dict,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_input_tokens: int = 0,
    units: float = 0.0,
    batch: bool = False,
) -> dict:
    """
    Computes an exact, transparent cost breakdown in USD across text, multimodal unit,
    and enterprise gateway models — properly applying batch discounts and platform fees.
    """
    m_type = model.get("type", "text")
    billing_unit = model.get("billing_unit") or ("1m_tokens" if m_type == "text" else "unit")
    unit_label = format_unit_label(billing_unit, m_type)
    fee_rate = float(model.get("platform_fee", 0.0) or 0.0)
    is_custom = False

    raw_base_usd = 0.0
    batch_applied = False
    batch_discount_rate = 0.0
    batch_savings_usd = 0.0

    if m_type == "text":
        in_rate = float(model.get("cost_per_1m_input_tokens", 0.0) or 0.0)
        cached_rate = float(
            model.get("cost_per_1m_cached_input_tokens")
            if model.get("cost_per_1m_cached_input_tokens") is not None
            else in_rate
        )
        out_rate = float(model.get("cost_per_1m_output_tokens", 0.0) or 0.0)

        raw_base_usd = (
            (max(0, input_tokens) / 1_000_000) * in_rate
            + (max(0, cached_input_tokens) / 1_000_000) * cached_rate
            + (max(0, output_tokens) / 1_000_000) * out_rate
        )

        if batch and float(model.get("batch_discount", 0.0) or 0.0) > 0:
            batch_applied = True
            batch_discount_rate = float(model["batch_discount"])
            batch_savings_usd = raw_base_usd * batch_discount_rate

        parts = [f"{input_tokens:,} in"]
        if cached_input_tokens > 0:
            parts.append(f"{cached_input_tokens:,} cached-in")
        parts.append(f"{output_tokens:,} out")
        usage_summary = f"Text ({', '.join(parts)})"
        if batch_applied:
            usage_summary += f" [Batch -{batch_discount_rate * 100:.0f}%]"

    elif m_type == "gateway":
        monthly = model.get("fixed_monthly_cost")
        effective_months = float(units) if units and units > 0 else 1.0
        if monthly is None:
            is_custom = True
            raw_base_usd = 0.0
            usage_summary = "Gateway (Custom enterprise pricing)"
        else:
            raw_base_usd = effective_months * float(monthly)
            usage_summary = f"Gateway ({effective_months:g} {unit_label})"

    else:
        unit_rate = float(model.get("cost_per_unit", 0.0) or 0.0)
        raw_base_usd = max(0.0, float(units)) * unit_rate
        if batch and float(model.get("batch_discount", 0.0) or 0.0) > 0:
            batch_applied = True
            batch_discount_rate = float(model["batch_discount"])
            batch_savings_usd = raw_base_usd * batch_discount_rate
        usage_summary = f"{m_type.capitalize()}: {units:g} {unit_label}"
        if batch_applied:
            usage_summary += f" [Batch -{batch_discount_rate * 100:.0f}%]"

    base_usd = raw_base_usd - batch_savings_usd
    platform_fee_usd = base_usd * fee_rate
    total_usd = base_usd + platform_fee_usd

    return {
        "model_id": model["id"],
        "provider": model.get("provider", "Unknown"),
        "source_type": model.get("source_type", "direct"),
        "model_type": m_type,
        "billing_unit": billing_unit,
        "unit_label": unit_label,
        "is_custom_pricing": is_custom,
        "usage_summary": usage_summary,
        "raw_base_usd": raw_base_usd,
        "batch_applied": batch_applied,
        "batch_discount_rate": batch_discount_rate,
        "batch_savings_usd": batch_savings_usd,
        "base_usd": base_usd,
        "platform_fee_rate": fee_rate,
        "platform_fee_usd": platform_fee_usd,
        "total_usd": total_usd,
    }


def estimate_monthly_cost(
    model: dict,
    requests_per_day: float,
    avg_input_tokens: int = 0,
    avg_output_tokens: int = 0,
    avg_cached_input_tokens: int = 0,
    avg_units: float = 0.0,
    days: int = 30,
    batch: bool = False,
) -> dict:
    """Estimates daily, monthly (N-day), and annual API spend for a recurring workload."""
    rpd = max(0.0, float(requests_per_day))
    period_days = max(1, int(days))

    if model.get("type") == "gateway":
        monthly_fixed = float(model.get("fixed_monthly_cost") or 0.0)
        is_custom = model.get("fixed_monthly_cost") is None
        daily_usd = monthly_fixed / 30.0
        period_usd = daily_usd * period_days
        annual_usd = monthly_fixed * 12.0
        return {
            "model_id": model["id"],
            "provider": model.get("provider", "Unknown"),
            "source_type": model.get("source_type", "gateway"),
            "model_type": "gateway",
            "is_custom_pricing": is_custom,
            "requests_per_day": rpd,
            "days": period_days,
            "per_request_usd": (daily_usd / rpd) if rpd > 0 else 0.0,
            "daily_usd": daily_usd,
            "period_base_usd": period_usd,
            "period_fee_usd": 0.0,
            "period_total_usd": period_usd,
            "annual_total_usd": annual_usd,
            "period_requests": rpd * period_days,
            "period_input_tokens": 0,
            "period_cached_input_tokens": 0,
            "period_output_tokens": 0,
        }

    per_req = calculate_cost_breakdown(
        model=model,
        input_tokens=avg_input_tokens,
        output_tokens=avg_output_tokens,
        cached_input_tokens=avg_cached_input_tokens,
        units=avg_units if avg_units > 0 else 1.0,
        batch=batch,
    )

    daily_base = per_req["base_usd"] * rpd
    daily_fee = per_req["platform_fee_usd"] * rpd
    daily_total = per_req["total_usd"] * rpd

    return {
        "model_id": model["id"],
        "provider": model.get("provider", "Unknown"),
        "source_type": model.get("source_type", "direct"),
        "model_type": model.get("type", "text"),
        "is_custom_pricing": per_req["is_custom_pricing"],
        "batch_applied": per_req["batch_applied"],
        "platform_fee_rate": per_req["platform_fee_rate"],
        "requests_per_day": rpd,
        "days": period_days,
        "per_request_usd": per_req["total_usd"],
        "daily_usd": daily_total,
        "period_base_usd": daily_base * period_days,
        "period_fee_usd": daily_fee * period_days,
        "period_total_usd": daily_total * period_days,
        "annual_total_usd": daily_total * 365.0,
        "period_requests": rpd * period_days,
        "period_input_tokens": int(rpd * period_days * max(0, avg_input_tokens)),
        "period_cached_input_tokens": int(rpd * period_days * max(0, avg_cached_input_tokens)),
        "period_output_tokens": int(rpd * period_days * max(0, avg_output_tokens)),
    }


def _match_in_list(models: list[dict], query: str) -> dict | None:
    # 1. Exact ID match
    for model in models:
        if str(model.get("id", "")).lower() == query:
            return model
    # 2. Exact openrouter_id match (e.g. 'openai/gpt-6.2-astra')
    for model in models:
        if str(model.get("openrouter_id", "")).lower() == query:
            return model
    # 3. Alias match
    for model in models:
        aliases = [str(a).lower() for a in model.get("aliases", [])]
        if query in aliases:
            return model
    return None


def _synthesize_openrouter_aggregator(base_model: dict, requested_id: str) -> dict:
    """Dynamically wraps any direct text model as an OpenRouter aggregator entry (+5.5% fee)."""
    synth = copy.deepcopy(base_model)
    clean_suffix = requested_id.split("openrouter/", 1)[-1]
    synth["id"] = f"openrouter/{clean_suffix}"
    synth["provider"] = "OpenRouter"
    synth["source_type"] = "aggregator"
    synth["platform_fee"] = 0.055
    synth.pop("batch_discount", None)
    tags = [t for t in synth.get("tags", []) if t != "direct"]
    if "aggregator" not in tags:
        tags.insert(0, "aggregator")
    synth["tags"] = tags
    synth["description"] = f"{base_model.get('id')} via OpenRouter aggregator (+5.5% platform fee)."
    return synth


def get_model_by_id(model_id: str, allow_live: bool = True) -> dict | None:
    """
    Looks up a model by ID, openrouter_id, or alias.
    Supports dynamic 'openrouter/<model>' synthesis and 400+ live OpenRouter catalog fallback.
    """
    if not model_id:
        return None
    query = model_id.strip().lower()
    curated = get_pricing_data(include_live=False)

    # 1. Direct match in curated database
    found = _match_in_list(curated, query)
    if found:
        return found

    # 2. Dynamic 'openrouter/<model>' synthesis on top of curated models
    if query.startswith("openrouter/"):
        sub_query = query.split("openrouter/", 1)[1]
        base = _match_in_list(curated, sub_query)
        if base and base.get("type", "text") == "text":
            return _synthesize_openrouter_aggregator(base, query)

    # 3. Live 400+ OpenRouter catalog fallback
    if allow_live:
        live_models = get_live_catalog(auto_fetch=True)
        if query.startswith("openrouter/"):
            sub_query = query.split("openrouter/", 1)[1]
            live_base = _match_in_list(live_models, sub_query)
            if live_base:
                return _synthesize_openrouter_aggregator(live_base, query)
        else:
            live_found = _match_in_list(live_models, query)
            if live_found:
                return live_found

    return None


def suggest_similar_models(model_id: str, limit: int = 3) -> list[str]:
    """Returns close model ID suggestions from curated + cached live models."""
    if not model_id:
        return []
    query = model_id.strip().lower()
    models = get_pricing_data(include_live=False) + get_live_catalog(auto_fetch=False)
    all_ids = list(dict.fromkeys(str(m.get("id", "")) for m in models if m.get("id")))

    suggestions: list[str] = []
    for mid in all_ids:
        if query in mid.lower() or mid.lower() in query:
            suggestions.append(mid)

    close = difflib.get_close_matches(query, [m.lower() for m in all_ids], n=limit, cutoff=0.45)
    lower_to_canonical = {m.lower(): m for m in all_ids}
    for c in close:
        canonical = lower_to_canonical[c]
        if canonical not in suggestions:
            suggestions.append(canonical)

    return suggestions[:limit]
