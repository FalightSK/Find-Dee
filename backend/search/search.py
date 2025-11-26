import os
import google.generativeai as genai
from typing import List
import json

class TagSearch:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def extract_query_tags(self, query: str, tag_pool: List[str] = None) -> List[str]:
        pool_str = json.dumps(tag_pool) if tag_pool else "[]"
        prompt = f"""
        Extract key topics/tags from this search query.
        You MUST select tags ONLY from the provided Tag Pool.
        If the query matches a tag in the pool (semantically or exactly), return that tag.
        If the query does NOT match any tag in the pool, return ["other"].
        Return ONLY a JSON array of strings.
        
        Tag Pool:
        {pool_str}
        
        Query:
        {query}
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
            print(f"Error extracting query tags: {e}")
            return ["other"]

    def match(self, query_tags: List[str], document_tags: List[str]) -> float:
        # Simple Jaccard similarity
        if not query_tags or not document_tags:
            return 0.0
        
        q_set = set(t.lower() for t in query_tags)
        d_set = set(t.lower() for t in document_tags)
        
        intersection = q_set.intersection(d_set)
        union = q_set.union(d_set)
        
        return len(intersection) / len(union) if union else 0.0
