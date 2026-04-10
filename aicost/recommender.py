from aicost.calculator import get_pricing_data, calculate_text_cost, calculate_image_cost

def recommend_models(task_description: str, limit: int = 3):
    """
    Recommends models based on keyword matching from the task description.
    Sorts them roughly by an inferred cost-to-performance or pure cost ratio if keywords match.
    """
    models = get_pricing_data()
    task_desc_lower = task_description.lower()
    words = set(task_desc_lower.replace(",", " ").replace(".", " ").split())
    
    scored_models = []
    
    for model in models:
        score = 0
        tags = [t.lower() for t in model.get("tags", [])]
        desc = model.get("description", "").lower()
        
        # Word hits
        for word in words:
            if word in tags:
                score += 3
            elif word in desc:
                score += 1
                
        # Bonus for specific keywords that commonly imply general model strength
        if score > 0:
            if "cheap" in task_desc_lower and "cheap" in tags:
                score += 5
            if "fast" in task_desc_lower and "fast" in tags:
                score += 2
            if "vision" in task_desc_lower or "image" in task_desc_lower or "ocr" in task_desc_lower:
                if "vision" in tags or "image" in tags or "ocr" in tags:
                    score += 5
                    
            scored_models.append((score, model))
            
    # Sort by score (descending), then by something like input cost (ascending) to break ties favorably
    scored_models.sort(key=lambda x: (x[0], -x[1].get('cost_per_1m_input_tokens', x[1].get('cost_per_unit', 0))), reverse=True)
    
    # Return top N models
    return [m[1] for m in scored_models[:limit]]
