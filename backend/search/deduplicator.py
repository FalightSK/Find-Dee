import os
from google import genai
from google.genai import types
from typing import List
import json

class TagDeduplicator:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        client = genai.Client(api_key=api_key)
        self.model = client

    def deduplicate(self, tags: List[str]) -> List[str]:
        if not tags:
            return []
            
        prompt = f"""
        Analyze the following list of tags and deduplicate them by merging semantically similar tags ignore the language of the tags.
        Keep the most canonical/common form.
        Return ONLY a JSON array of strings of the unique tags.
        
        Tags:
        {json.dumps(tags)}
        """
        response = self.model.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            )
        )
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

    def deduplicate_and_map(self, tags: List[str]) -> dict:
        if not tags:
            return {}
            
        prompt = f"""
        Analyze the following list of tags and deduplicate them by merging semantically similar tags ignore the language of the tags.
        Keep the most canonical/common form.
        Return ONLY a JSON object where the key is the original tag and the value is the canonical tag.
        Every original tag MUST be present as a key in the returned JSON.
        
        Tags:
        {json.dumps(tags)}
        """
        response = self.model.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            )
        )
        try:
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Error deduplicating tags: {e}")
            # Fallback: map each tag to itself
            return {tag: tag for tag in tags}
