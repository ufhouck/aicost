import json
import os
import requests
from datetime import datetime

# Path to the library's pricing data
PRICING_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pricing.json")

# OpenRouter is used as a reliable "Price Oracle" to fetch direct provider prices
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"

def get_current_prices():
    """Fetches latest prices from reliable market sources."""
    try:
        response = requests.get(OPENROUTER_API_URL, timeout=15)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching from OpenRouter: {e}")
        return []

def main():
    print(f"Starting weekly pricing automation: {datetime.now().strftime('%Y-%m-%d')}")
    
    # 1. Load local data
    with open(PRICING_FILE, "r", encoding="utf-8") as f:
        local_data = json.load(f)
    
    remote_models = get_current_prices()
    if not remote_models:
        print("Could not fetch remote data. Aborting.")
        return

    # Map remote data to our structure
    # OpenRouter contains direct models (openai/gpt-4o, anthropic/claude-3-opus, etc.)
    updates_made = 0
    for model in local_data["models"]:
        # Skip gateway types with fixed costs (Martian, Portkey, etc.) as they aren't per-token
        if model.get("source_type") == "gateway":
            continue

        model_id = model["id"].lower()
        provider = model["provider"].lower()
        
        # Strip aggregator prefix if present for matching
        clean_id = model_id.split("/")[-1] if "/" in model_id else model_id
        
        # Find match in remote data
        match = next((rm for rm in remote_models if clean_id in rm["id"].lower()), None)
        
        if match:
            # Extract base prices
            new_input = float(match["pricing"]["prompt"]) * 1_000_000
            new_output = float(match["pricing"]["completion"]) * 1_000_000
            
            if abs(model.get("cost_per_1m_input_tokens", 0) - new_input) > 0.000001:
                print(f"Update found for {model['id']}: {model.get('cost_per_1m_input_tokens', 0):.4f} -> {new_input:.4f} (incl. fee)")
                model["cost_per_1m_input_tokens"] = round(new_input, 4)
                updates_made += 1
            
            if abs(model.get("cost_per_1m_output_tokens", 0) - new_output) > 0.000001:
                print(f"Update found for {model['id']}: {model.get('cost_per_1m_output_tokens', 0):.4f} -> {new_output:.4f} (incl. fee)")
                model["cost_per_1m_output_tokens"] = round(new_output, 4)
                updates_made += 1

    if updates_made > 0:
        local_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(PRICING_FILE, "w", encoding="utf-8") as f:
            json.dump(local_data, f, indent=2)
        print(f"Total updates applied: {updates_made}")
    else:
        print("No pricing changes detected this week.")

if __name__ == "__main__":
    main()
