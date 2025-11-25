import random

class TaggingService:
    def __init__(self):
        self.categories = ["Finance", "HR", "Project", "General", "Marketing"]
        
    def generate_tags(self, filename: str, content_preview: str = "") -> dict:
        """
        Simulate AI tagging based on filename and content.
        In a real scenario, this would call an SLM/LLM.
        """
        # Simple heuristic for demo
        category = "General"
        if "invoice" in filename.lower() or "budget" in filename.lower():
            category = "Finance"
        elif "resume" in filename.lower() or "cv" in filename.lower():
            category = "HR"
        elif "plan" in filename.lower() or "proposal" in filename.lower():
            category = "Project"
            
        return {
            "category": category,
            "tags": [category, filename.split('.')[-1]],
            "confidence": round(random.uniform(0.8, 0.99), 2)
        }

tagging_service = TaggingService()
