from __future__ import annotations

import datetime
import json
import sys
import time
from pathlib import Path
import requests

CACHE_DURATION = 24 * 60 * 60  # 24 hours
CACHE_DIR = Path.home() / ".aicost"
CACHE_FILE = CACHE_DIR / "exchange_cache.json"
LEGACY_CACHE_FILE = CACHE_DIR / "currency_cache.json"

# Primary: Fawaz Ahmed Currency API on jsDelivr CDN (200+ currencies, zero rate limits)
PRIMARY_CURRENCY_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json"
# Fallback 1: Official Cloudflare Pages mirror
FALLBACK_CDN_URL = "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json"
# Fallback 2: European Central Bank via Frankfurter
FALLBACK_ECB_URL = "https://api.frankfurter.app/latest?from=USD"


def _warn_stderr(message: str) -> None:
    """Writes clean plain-text warnings to stderr without polluting stdout (safe for MCP stdio)."""
    sys.stderr.write(f"Warning: {message}\n")


def _normalize_rates(raw_rates: dict) -> dict[str, float]:
    normalized: dict[str, float] = {"USD": 1.0}
    for code, val in raw_rates.items():
        try:
            fval = float(val)
            if fval > 0:
                normalized[str(code).upper()] = fval
        except (TypeError, ValueError):
            continue
    return normalized


def _fetch_from_api() -> tuple[dict[str, float], str]:
    """Fetches USD exchange rates using a 3-tier resilient fallback chain."""
    for url in (PRIMARY_CURRENCY_URL, FALLBACK_CDN_URL):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            payload = response.json()
            usd_map = payload.get("usd") or {}
            rates = _normalize_rates(usd_map)
            if len(rates) > 1:
                return rates, str(payload.get("date") or "")
        except Exception:
            continue

    try:
        response = requests.get(FALLBACK_ECB_URL, timeout=5)
        response.raise_for_status()
        payload = response.json()
        rates = _normalize_rates(payload.get("rates") or {})
        if len(rates) > 1:
            return rates, str(payload.get("date") or "")
    except Exception:
        pass

    return {"USD": 1.0}, ""


def _load_cached_payload() -> dict | None:
    for candidate in (CACHE_FILE, LEGACY_CACHE_FILE):
        if candidate.exists():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("rates"), dict):
                    return data
            except Exception:
                continue
    return None


def _save_cache(rates: dict[str, float], api_date: str = "") -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": time.time(),
            "api_date": api_date,
            "rates": rates,
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        pass


def refresh_rates() -> dict[str, float]:
    """Forces a fresh fetch of currency exchange rates and updates the local cache."""
    rates, api_date = _fetch_from_api()
    if len(rates) > 1:
        _save_cache(rates, api_date)
    return rates


def get_rates() -> dict[str, float]:
    """Gets exchange rates using a 24-hour local cache with stale-cache offline fallback."""
    now = time.time()
    cached = _load_cached_payload()
    stale_rates: dict[str, float] | None = None

    if cached:
        stale_rates = _normalize_rates(cached.get("rates", {}))
        if len(stale_rates) > 1 and (now - float(cached.get("timestamp", 0))) < CACHE_DURATION:
            return stale_rates

    rates, api_date = _fetch_from_api()
    if len(rates) > 1:
        _save_cache(rates, api_date)
        return rates

    if stale_rates and len(stale_rates) > 1:
        _warn_stderr("Could not refresh exchange rates. Using cached rates.")
        return stale_rates

    return {"USD": 1.0}


def get_exchange_rate(to_currency: str) -> tuple[float, str]:
    """Returns (multiplier, effective_currency_code). Falls back to (1.0, 'USD') if unavailable."""
    target = (to_currency or "USD").strip().upper()
    if target == "USD":
        return 1.0, "USD"

    rates = get_rates()
    if target in rates:
        return rates[target], target

    _warn_stderr(f"Currency '{target}' not found or network unavailable. Falling back to USD.")
    return 1.0, "USD"


def convert_cost(cost_usd: float, to_currency: str) -> float:
    """Converts a USD amount into the target currency."""
    rate, _ = get_exchange_rate(to_currency)
    return cost_usd * rate


def get_currency_date() -> str:
    """Returns a formatted timestamp or date string indicating when exchange rates were cached."""
    cached = _load_cached_payload()
    if cached:
        ts = cached.get("timestamp", 0)
        if ts:
            try:
                return datetime.datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        if cached.get("api_date"):
            return str(cached["api_date"])
    return "Live / No Cache"
