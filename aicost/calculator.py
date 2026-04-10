import os
import json
import time
from pathlib import Path
import requests

CACHE_DIR = Path.home() / ".aicost"
CACHE_FILE = CACHE_DIR / "pricing_cache.json"
REMOTE_PRICING_URL = "https://raw.githubusercontent.com/ufhouck/aicost/main/data/pricing.json"

def fetch_remote_pricing() -> dict:
    """Fetches the latest pricing data from GitHub and updates the local cache."""
    try:
        response = requests.get(REMOTE_PRICING_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
    except Exception:
        return {}

def get_pricing_data() -> list:
    """Loads the pricing data, preferring the remote cache over local files."""
    data = get_all_data()
    return data.get("models", [])

def get_pricing_metadata() -> dict:
    """Loads the root metadata from pricing data."""
    return get_all_data()

def get_all_data() -> dict:
    """Retrieves all pricing data from cache (if fresh) or local bundle."""
    # 1. Check Cache
    if CACHE_FILE.exists():
        # If cache is less than 7 days old, use it
        if (time.time() - CACHE_FILE.stat().st_mtime) < (7 * 24 * 3600):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    # 2. Try bundled local file (Fallback)
    potential_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pricing.json"),
        os.path.join(os.getcwd(), "data", "pricing.json")
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
                
    return {}

def calculate_text_cost(model: dict, input_tokens: int, output_tokens: int) -> float:
    """Calculates the cost for text-based models based on token counts."""
    input_cost = (input_tokens / 1_000_000) * model.get("cost_per_1m_input_tokens", 0)
    output_cost = (output_tokens / 1_000_000) * model.get("cost_per_1m_output_tokens", 0)
    return input_cost + output_cost

def calculate_image_cost(model: dict, units: int) -> float:
    """Calculates the cost for image-based models based on unit counts."""
    return units * model.get("cost_per_unit", 0)
    
def get_model_by_id(model_id: str) -> dict:
    models = get_pricing_data()
    for model in models:
        if model.get("id").lower() == model_id.lower():
            return model
    return None
