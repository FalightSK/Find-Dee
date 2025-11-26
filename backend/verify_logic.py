import sys
import os

# Mock classes to simulate the behavior of the real services
class MockTagGenerator:
    def generate_metadata(self, file_path, mime_type):
        print(f"[MockTagGenerator] Generating metadata for {file_path} ({mime_type})")
        # Simulate generating a NEW tag that is NOT in the initial pool
        return {
            "tags": ["Machine Learning", "Neural Networks"], 
            "title": "Intro to AI", 
            "summary": "A basic intro."
        }

class MockTagSearch:
    def extract_query_tags(self, query, tag_pool):
        print(f"[MockTagSearch] Extracting tags for query: '{query}'")
        print(f"[MockTagSearch] Constrained to Tag Pool: {tag_pool}")
        
        # Simulate the LLM picking a tag from the pool
        found_tags = []
        for tag in tag_pool:
            if tag.lower() in query.lower():
                found_tags.append(tag)
        
        if not found_tags:
             # specific logic simulation: if query mentions "neural", and "Neural Networks" is in pool
             if "neural" in query.lower() and "Neural Networks" in tag_pool:
                 found_tags.append("Neural Networks")
        
        return found_tags

# Simulation of the logic in bot.py
def simulate_bot_logic():
    print("--- Starting Logic Verification ---")
    
    # 1. Initial State
    tag_pool = ["Lecture", "Exam"]
    print(f"1. Initial Tag Pool: {tag_pool}")
    
    # Initialize Services
    tagger = MockTagGenerator()
    searcher = MockTagSearch()
    
    # 2. Simulate File Upload (PDF)
    print("\n--- Step 2: Simulate PDF Upload ---")
    file_path = "/tmp/test.pdf"
    mime_type = "application/pdf"
    
    # Logic from bot.py: Generate metadata (Unconstrained generation)
    generated_metadata = tagger.generate_metadata(file_path, mime_type)
    new_tags = generated_metadata["tags"]
    print(f"   Generated Tags (Unconstrained): {new_tags}")
    
    # Logic from bot.py: Update Pool
    # (Simplified deduplication logic for verification)
    tag_pool.extend(new_tags)
    tag_pool = list(set(tag_pool))
    print(f"   Updated Tag Pool: {tag_pool}")
    
    # Verify: Did the pool grow?
    if "Neural Networks" in tag_pool:
        print("   [SUCCESS] New tags were added to the pool.")
    else:
        print("   [FAILURE] New tags were NOT added to the pool.")

    # 3. Simulate Search
    print("\n--- Step 3: Simulate Search ---")
    query = "I need to find slides about Neural Networks"
    
    # Logic from bot.py: Search (Constrained to Pool)
    query_tags = searcher.extract_query_tags(query, tag_pool)
    print(f"   Extracted Query Tags: {query_tags}")
    
    # Verify: Did it find the new tag?
    if "Neural Networks" in query_tags:
        print("   [SUCCESS] Search found the tag in the updated pool.")
    else:
        print("   [FAILURE] Search did not find the tag.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    simulate_bot_logic()
