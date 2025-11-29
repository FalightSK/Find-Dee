import os
from google import genai
from google.genai import types
from typing import List
import json

class TagSearch:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        client = genai.Client(api_key=api_key)
        self.model = client

    def extract_query_tags(self, query: str, tag_pool: List[str] = None) -> List[str]:
        pool_str = json.dumps(tag_pool) if tag_pool else "[]"
        prompt = f"""
        Extract key topics/tags from this search query.
        You MUST select tags ONLY from the provided Tag Pool.
        If the query matches a tag in the pool (semantically), return that tag.
        If the query does NOT match any tag in the pool, return ["other"].
        Do not consider the language of the query just focus on it intent.
        Return ONLY a JSON array of strings.
        
        Tag Pool:
        {pool_str}
        
        Query:
        {query}
        """
        response = self.model.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
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
            print(f"Error extracting query tags: {e}")
            return ["other"]

    def match(self, query_tags: List[str], document_tags: List[str]) -> float:
        # Match if any tag exists in the document
        if not query_tags or not document_tags:
            return 0.0
        
        q_set = set(t.lower() for t in query_tags)
        d_set = set(t.lower() for t in document_tags)
        
        intersection = q_set.intersection(d_set)
        
        # Return number of matches to allow sorting by relevance
        return float(len(intersection))

    def search_documents(self, query: str, documents: List[dict], tag_pool: List[str], group_id: str = None, owner_id: str = None) -> List[dict]:
        """
        Searches documents by extracting tags from the query and matching them against document tags.
        Optional: filters by group_id or owner_id if provided.
        """
        # 1. Extract tags from query using the pool
        query_tags = self.extract_query_tags(query, tag_pool)
        
        results = []
        for doc in documents:
            # Filter logic
            if group_id and doc.get("group_id") != group_id:
                continue
            if owner_id and doc.get("owner_id") != owner_id:
                continue

            doc_tags = doc.get("tags", [])
            score = self.match(query_tags, doc_tags)
            
            if score > 0:
                # Return a copy of the doc with the score added
                result_doc = doc.copy()
                result_doc["_score"] = score
                results.append(result_doc)
        
        # Sort by score descending
        results.sort(key=lambda x: x["_score"], reverse=True)
        return results

    def filter_events(self, query: str, events: List[dict]) -> List[str]:
        """
        Uses LLM to filter events based on semantic meaning and relative dates.
        Returns a list of event IDs.
        """
        if not events:
            return []
            
        # Prepare simplified event list for token efficiency
        simplified_events = []
        for e in events:
            simplified_events.append({
                "id": e.get("id"),
                "title": e.get("title"),
                "date": e.get("date") or e.get("date_time"),
                "description": e.get("description", "")
            })
            
        events_json = json.dumps(simplified_events, ensure_ascii=False, indent=2)
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""
        Current Date: {today}
        User Query: {query}
        
        Events List:
        {events_json}
        
        Select the events that are relevant to the user's query. 
        Consider relative dates (e.g. "next week", "tomorrow", "this weekend") and semantic meaning.
        Return ONLY a JSON array of event IDs (strings).
        """
        
        try:
            response = self.model.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
                )
        )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Error filtering events: {e}")
            return []
