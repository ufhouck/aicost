import json
import os

# Assuming running from site-packages or local checkout where data/pricing.json is in project root
def get_pricing_data() -> list:
    """Loads the pricing data from the local JSON file."""
    # Try different potential locations
    potential_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pricing.json"),
        os.path.join(os.getcwd(), "data", "pricing.json")
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("models", [])
                
    return []

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
