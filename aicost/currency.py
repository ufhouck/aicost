import os
import json
import time
import requests
from pathlib import Path

CACHE_DURATION = 24 * 60 * 60  # 24 hours
CACHE_FILE = Path.home() / ".aicost_currency_cache.json"
BASE_URL = "https://api.frankfurter.app/latest?from=USD"

def _fetch_from_api() -> dict:
    try:
        response = requests.get(BASE_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        rates["USD"] = 1.0  # Base currency
        return rates
    except Exception as e:
        return {"USD": 1.0} # Fallback

def get_rates() -> dict:
    """Gets exchange rates from Frankfurter, using a 24-hour local cache."""
    now = time.time()
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                cached_data = json.load(f)
            if now - cached_data.get("timestamp", 0) < CACHE_DURATION:
                return cached_data.get("rates", {"USD": 1.0})
        except Exception:
            pass # fallback to fetch

    # If we are here, we need to fetch new rates
    rates = _fetch_from_api()
    if rates and "USD" in rates: # check if fetch was at least partially successful
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"timestamp": now, "rates": rates}, f)
        except Exception:
            pass # ignore if we cannot write cache
    return rates

def convert_cost(cost_usd: float, to_currency: str) -> float:
    """Converts a cost in USD to the target currency."""
    to_currency = to_currency.upper()
    if to_currency == "USD":
        return cost_usd
        
    rates = get_rates()
    if to_currency in rates:
        return cost_usd * rates[to_currency]
    else:
        # Fallback if currency not found
        return cost_usd
