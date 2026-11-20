from __future__ import annotations

import json
import os
import re
from datetime import datetime
import requests

# Path to the library's canonical pricing database
PRICING_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pricing.json")

# OpenRouter serves as our live market oracle for both price updates & new model discovery
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"

# Trusted flagship provider namespaces eligible for automatic weekly model discovery
WATCHED_PROVIDERS: dict[str, str] = {
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
}

# Only auto-discover newly released models from late-2026 onward (avoids backfilling hundreds of old models)
MIN_DISCOVERY_CREATED_TS = 1793000000

# Skip dated snapshots, variants, moderation, or experimental endpoints during auto-discovery
SKIP_SLUG_PATTERNS = (
    ":",
    "-exp",
    "-preview",
    "guard",
    "embed",
    "moderation",
    "audio-preview",
    "realtime",
)
DATED_SUFFIX_RE = re.compile(r"-\d{4,8}$")


def get_current_prices() -> list[dict]:
    """Fetches latest model catalog and pricing from OpenRouter."""
    try:
        response = requests.get(OPENROUTER_API_URL, timeout=15)
        response.raise_for_status()
        data = response.json().get("data", [])
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching from OpenRouter: {e}")
        return []


def resolve_openrouter_slug(model: dict) -> str | None:
    """Returns the exact OpenRouter model slug to match against, avoiding substring collisions."""
    explicit_id = model.get("openrouter_id")
    if explicit_id:
        return explicit_id.strip().lower()

    model_id = model.get("id", "").strip().lower()
    provider = model.get("provider", "").strip().lower()
    if "/" in model_id and not model_id.startswith("openrouter/"):
        return model_id
    if provider and provider != "openrouter":
        clean_id = model_id.split("/")[-1]
        return f"{provider}/{clean_id}"
    return None


def infer_tags(rm: dict, in_cost: float) -> list[str]:
    tags: list[str] = []
    slug = str(rm.get("id", "")).lower()
    arch = rm.get("architecture") or {}
    in_mods = [str(x).lower() for x in (arch.get("input_modalities") or [])]
    ctx = int(rm.get("context_length") or 0)

    if "image" in in_mods:
        tags.extend(["vision", "multimodal"])
    if "audio" in in_mods or "video" in in_mods:
        tags.append("multimodal")
    if ctx >= 500_000:
        tags.append("long-context")

    if in_cost <= 0.35:
        tags.extend(["cheap", "fast"])
    elif in_cost >= 5.0:
        tags.append("premium")

    if any(k in slug for k in ("flash", "lite", "mini", "haiku", "luna", "scout")):
        tags.append("fast")
    if any(k in slug for k in ("pro", "opus", "astra", "fable", "max", "r1", "o3", "o4", "grok", "sonnet", "neon", "carbon")):
        tags.extend(["reasoning", "coding"])
    else:
        tags.append("general")

    # Deduplicate preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def should_auto_discover(rm: dict, known_slugs: set[str], known_ids: set[str]) -> bool:
    or_id = str(rm.get("id", "")).strip().lower()
    if not or_id or "/" not in or_id or or_id in known_slugs:
        return False

    if any(pat in or_id for pat in SKIP_SLUG_PATTERNS):
        return False

    prefix, short_id = or_id.split("/", 1)
    if prefix not in WATCHED_PROVIDERS:
        return False

    if DATED_SUFFIX_RE.search(short_id):
        return False

    # Skip '-pro' duplicate variants when OpenRouter mirrors identical pricing to non-pro
    created = int(rm.get("created") or 0)
    if created < MIN_DISCOVERY_CREATED_TS:
        return False

    if short_id in known_ids:
        return False

    pricing = rm.get("pricing") or {}
    try:
        in_p = float(pricing.get("prompt", 0)) * 1_000_000
        out_p = float(pricing.get("completion", 0)) * 1_000_000
    except (TypeError, ValueError):
        return False

    return in_p > 0 and out_p > 0


def main() -> None:
    print(f"Starting weekly pricing & model discovery automation: {datetime.now().strftime('%Y-%m-%d')}")

    with open(PRICING_FILE, "r", encoding="utf-8") as f:
        local_data = json.load(f)

    remote_models = get_current_prices()
    if not remote_models:
        print("Could not fetch remote data. Aborting.")
        return

    remote_by_id = {
        str(rm["id"]).strip().lower(): rm
        for rm in remote_models
        if isinstance(rm, dict) and rm.get("id")
    }

    updates_made = 0
    known_slugs: set[str] = set()
    known_ids: set[str] = set()

    # Phase 1: Sync existing curated models
    for model in local_data.get("models", []):
        known_ids.add(str(model.get("id", "")).lower())
        slug = resolve_openrouter_slug(model)
        if slug:
            known_slugs.add(slug)

        if model.get("type") != "text" or model.get("source_type") == "gateway":
            continue
        if not slug:
            continue

        match = remote_by_id.get(slug)
        if not match:
            continue

        pricing = match.get("pricing") or {}
        try:
            new_input = float(pricing.get("prompt", 0)) * 1_000_000
            new_output = float(pricing.get("completion", 0)) * 1_000_000
        except (TypeError, ValueError):
            continue

        if new_input <= 0 or new_output <= 0:
            continue

        old_input = model.get("cost_per_1m_input_tokens", 0.0)
        old_output = model.get("cost_per_1m_output_tokens", 0.0)

        if abs(old_input - new_input) > 0.000001:
            print(f"Input price update for {model['id']} ({slug}): {old_input:.4f} -> {new_input:.4f} USD/1M")
            model["cost_per_1m_input_tokens"] = round(new_input, 4)
            updates_made += 1

        if abs(old_output - new_output) > 0.000001:
            print(f"Output price update for {model['id']} ({slug}): {old_output:.4f} -> {new_output:.4f} USD/1M")
            model["cost_per_1m_output_tokens"] = round(new_output, 4)
            updates_made += 1

        if "input_cache_read" in pricing and pricing["input_cache_read"] is not None:
            try:
                new_cache = float(pricing["input_cache_read"]) * 1_000_000
                old_cache = model.get("cost_per_1m_cached_input_tokens")
                if new_cache > 0 and (old_cache is None or abs(old_cache - new_cache) > 0.000001):
                    model["cost_per_1m_cached_input_tokens"] = round(new_cache, 4)
                    updates_made += 1
            except (TypeError, ValueError):
                pass

    # Phase 2: Auto-discover brand-new mainline models from watched flagship providers
    discovered_entries: list[dict] = []
    for rm in sorted(remote_models, key=lambda x: int(x.get("created") or 0), reverse=True):
        if not should_auto_discover(rm, known_slugs, known_ids):
            continue

        or_id = str(rm["id"]).strip().lower()
        prefix, short_id = or_id.split("/", 1)
        pricing = rm.get("pricing") or {}
        in_cost = round(float(pricing["prompt"]) * 1_000_000, 4)
        out_cost = round(float(pricing["completion"]) * 1_000_000, 4)

        entry: dict = {
            "id": short_id,
            "openrouter_id": or_id,
            "provider": WATCHED_PROVIDERS[prefix],
            "source_type": "direct",
            "type": "text",
            "billing_unit": "1m_tokens",
            "context_window": int(rm.get("context_length") or 128000),
            "cost_per_1m_input_tokens": in_cost,
            "cost_per_1m_output_tokens": out_cost,
            "tags": infer_tags(rm, in_cost),
            "description": str(rm.get("name") or short_id).split(": ", 1)[-1] + " (auto-discovered via weekly sync).",
        }

        if pricing.get("input_cache_read") is not None:
            try:
                cache_val = round(float(pricing["input_cache_read"]) * 1_000_000, 4)
                if cache_val > 0:
                    entry["cost_per_1m_cached_input_tokens"] = cache_val
            except (TypeError, ValueError):
                pass

        batch_rm = remote_by_id.get(f"{or_id}:batch")
        if batch_rm:
            try:
                batch_in = float((batch_rm.get("pricing") or {}).get("prompt", 0)) * 1_000_000
                if 0 < batch_in < in_cost:
                    entry["batch_discount"] = round(1.0 - (batch_in / in_cost), 2)
            except (TypeError, ValueError):
                pass

        discovered_entries.append(entry)
        known_slugs.add(or_id)
        known_ids.add(short_id)
        updates_made += 1
        print(f"Discovered new flagship model: {short_id} ({or_id}) at ${in_cost}/${out_cost} per 1M")

    if discovered_entries:
        # Insert newly discovered flagship models at the top of the catalog
        local_data["models"] = discovered_entries + local_data.get("models", [])

    if updates_made > 0:
        local_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(PRICING_FILE, "w", encoding="utf-8") as f:
            json.dump(local_data, f, indent=2)
            f.write("\n")
        print(f"Total updates/discoveries applied: {updates_made}")
    else:
        print("No pricing changes or new models detected this week.")


if __name__ == "__main__":
    main()
