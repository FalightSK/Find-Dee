import os
import google.generativeai as genai
from typing import List
import json

class TagGenerator:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_tags(self, document_text: str) -> List[str]:
        prompt = f"""
        Generate a list of relevant tags for the following text.
        Return ONLY a JSON array of strings. Do not include markdown formatting.
        
        Text:
        {document_text}
        """
        response = self.model.generate_content(prompt)
        try:
            text = response.text.strip()
            # Handle potential markdown code blocks if the model ignores instruction
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Error parsing tags: {e}")
            return []
