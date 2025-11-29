import os
from google import genai
from google.genai import types
from typing import List
import json

class TagGenerator:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        client = genai.Client(api_key=api_key)
        self.model = client

    def generate_metadata(self, file_path: str, mime_type: str) -> dict:
        """
        Generates metadata (tags, title, summary) for a given file.
        """
        prompt = """
        Analyze the following file and provide:
        1. A list of relevant tags (max 5).
        2. A concise title.
        3. A brief summary (1-2 sentences).
        4. A short, concise, content-based filename (in English, no spaces, use underscores, max 30 chars). Do not include file extension.
        
        Return ONLY a JSON object with keys: "tags" (list of strings), "title" (string), "summary" (string), "suggested_filename" (string).
        """
        
        try:
            # Upload the file to Gemini
            sample_file = self.model.files.upload(
            file=file_path,
            )
            
            response = self.model.models.generate_content(
                model="gemini-2.0-flash",
                contents=[sample_file, prompt],
                config=types.GenerateContentConfig(
                temperature=0,
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
            print(f"Error generating metadata: {e}")
            return {"tags": [], "title": "Untitled", "summary": "No summary available.", "suggested_filename": "untitled_file"}

    def generate_tags(self, document_text: str) -> List[str]:
        prompt = f"""
        Generate a list of relevant tags for the following text.
        Return ONLY a JSON array of strings. Do not include markdown formatting.
        
        Text:
        {document_text}
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
            # Handle potential markdown code blocks if the model ignores instruction
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Error parsing tags: {e}")
    def summarize_group(self, summaries: List[str]) -> str:
        """
        Summarizes a list of summaries into a single cohesive summary.
        """
        if not summaries:
            return ""
            
        joined_summaries = "\n- ".join(summaries)
        prompt = f"""
        Here are summaries of several documents found for a search query. 
        Please provide a concise, integrated summary (in Thai) that explains what these documents collectively contain.
        
        Summaries:
        - {joined_summaries}
        """
        
        try:
            response = self.model.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error summarizing group: {e}")
            return "ไม่สามารถสรุปผลการค้นหาได้ในขณะนี้"
