import os
import google.generativeai as genai
from typing import List
import json

class TagDeduplicator:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def deduplicate(self, tags: List[str]) -> List[str]:
        if not tags:
            return []
            
        prompt = f"""
        Analyze the following list of tags and deduplicate them by merging semantically similar tags.
        Keep the most canonical/common form.
        Return ONLY a JSON array of strings of the unique tags.
        
        Tags:
        {json.dumps(tags)}
        """
        response = self.model.generate_content(prompt)
        try:
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Error deduplicating tags: {e}")
            return tags
