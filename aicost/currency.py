import os
import json
import time
import requests
from pathlib import Path

CACHE_DURATION = 24 * 60 * 60  # 24 hours
CACHE_DIR = Path.home() / ".aicost"
CACHE_FILE = CACHE_DIR / "currency_cache.json"
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
    """Gets exchange rates, using a 24-hour cache with a stale-fallback mechanism."""
    now = time.time()
    stale_rates = None
    
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                cached_data = json.load(f)
            stale_rates = cached_data.get("rates", {"USD": 1.0})
            # If cache is fresh, return it immediately
            if now - cached_data.get("timestamp", 0) < CACHE_DURATION:
                return stale_rates
        except Exception:
            pass

    # Try to fetch new rates
    rates = _fetch_from_api()
    if rates and len(rates) > 1: # check if fetch was successful (more than just USD)
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"timestamp": now, "rates": rates}, f)
        except Exception:
            pass
        return rates
    
    # If fetch failed but we have stale rates, use them as fallback
    if stale_rates:
        import sys
        print("\n[bold yellow]Offline Warning:[/bold yellow] Could not refresh currencies. Using cached rates.", file=sys.stderr)
        return stale_rates
        
    return {"USD": 1.0}

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
        from rich.console import Console
        Console(stderr=True).print(f"[bold yellow]Warning:[/bold yellow] Currency '{to_currency}' not found or network error. Using USD.")
        return cost_usd

def get_currency_date() -> str:
    """Returns a formatted string of when the currecy was last fetched."""
    import datetime
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                ts = json.load(f).get("timestamp", 0)
                if ts:
                    return datetime.datetime.fromtimestamp(ts).strftime("%B %d, %Y")
        except Exception:
            pass
    return "Live / No Cache"
