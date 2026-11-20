from __future__ import annotations

import json
import os
from datetime import datetime
import requests

# Path to the library's pricing data
PRICING_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pricing.json")

# OpenRouter is used as a reliable "Price Oracle" to fetch base token prices
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"


def get_current_prices() -> list[dict]:
    """Fetches latest prices from OpenRouter's public model catalog."""
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


def main() -> None:
    print(f"Starting weekly pricing automation: {datetime.now().strftime('%Y-%m-%d')}")

    with open(PRICING_FILE, "r", encoding="utf-8") as f:
        local_data = json.load(f)

    remote_models = get_current_prices()
    if not remote_models:
        print("Could not fetch remote data. Aborting.")
        return

    # Index remote models by exact lowercase ID to prevent substring collisions
    # (e.g. 'openai/gpt-4o' must never match 'openai/gpt-4o-mini')
    remote_by_id = {
        str(rm["id"]).strip().lower(): rm
        for rm in remote_models
        if isinstance(rm, dict) and rm.get("id")
    }

    updates_made = 0
    for model in local_data.get("models", []):
        # Only auto-update token-based text models; unit-based image/video/audio & gateways
        # have distinct billing units that cannot be mapped from prompt/completion token rates.
        if model.get("type") != "text" or model.get("source_type") == "gateway":
            continue

        target_slug = resolve_openrouter_slug(model)
        if not target_slug:
            continue

        match = remote_by_id.get(target_slug)
        if not match:
            continue

        pricing = match.get("pricing") or {}
        try:
            new_input = float(pricing.get("prompt", 0)) * 1_000_000
            new_output = float(pricing.get("completion", 0)) * 1_000_000
        except (TypeError, ValueError):
            continue

        # Guard against zero/negative promo endpoints overwriting canonical paid pricing
        if new_input <= 0 or new_output <= 0:
            continue

        old_input = model.get("cost_per_1m_input_tokens", 0.0)
        old_output = model.get("cost_per_1m_output_tokens", 0.0)

        if abs(old_input - new_input) > 0.000001:
            print(f"Input price update for {model['id']} ({target_slug}): {old_input:.4f} -> {new_input:.4f} USD/1M")
            model["cost_per_1m_input_tokens"] = round(new_input, 4)
            updates_made += 1

        if abs(old_output - new_output) > 0.000001:
            print(f"Output price update for {model['id']} ({target_slug}): {old_output:.4f} -> {new_output:.4f} USD/1M")
            model["cost_per_1m_output_tokens"] = round(new_output, 4)
            updates_made += 1

        # Update cache-read pricing when OpenRouter exposes input_cache_read
        if "input_cache_read" in pricing and pricing["input_cache_read"] is not None:
            try:
                new_cache = float(pricing["input_cache_read"]) * 1_000_000
                old_cache = model.get("cost_per_1m_cached_input_tokens")
                if new_cache > 0 and (old_cache is None or abs(old_cache - new_cache) > 0.000001):
                    model["cost_per_1m_cached_input_tokens"] = round(new_cache, 4)
                    updates_made += 1
            except (TypeError, ValueError):
                pass

    if updates_made > 0:
        local_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(PRICING_FILE, "w", encoding="utf-8") as f:
            json.dump(local_data, f, indent=2)
            f.write("\n")
        print(f"Total updates applied: {updates_made}")
    else:
        print("No pricing changes detected this week.")


if __name__ == "__main__":
    main()
