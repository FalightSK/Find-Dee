import os
from dotenv import load_dotenv
from tagger import TagGenerator
from deduplicator import TagDeduplicator
from search import TagSearch

# Load environment variables
load_dotenv()

def main():
    print("Initializing Tag System...")
    try:
        tagger = TagGenerator()
        deduplicator = TagDeduplicator()
        searcher = TagSearch()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set GOOGLE_API_KEY in .env file")
        return

    # 1. Input Document
    print("\n--- Document Tagging ---")
    doc_text = input("Enter document text (or press Enter for default): ")
    if not doc_text:
        doc_text = "Artificial Intelligence is transforming the world. Machine learning models like LLMs are becoming very powerful. Deep Learning is a subset of ML."
        print(f"Using default text: {doc_text}")

    # 2. Generate Tags
    print("\nGenerating tags...")
    tags = tagger.generate_tags(doc_text)
    print(f"Raw Tags: {tags}")

    # 3. Deduplicate
    # Let's add some duplicates artificially to test if the model didn't generate them, 
    # or just to show the capability if the input text was repetitive.
    # But for a real demo, we should rely on the model's output or user input.
    # Let's ask if user wants to add more tags to test deduplication.
    more_tags = input("\nEnter additional tags to test deduplication (comma separated, or Enter to skip): ")
    if more_tags:
        tags.extend([t.strip() for t in more_tags.split(",")])
        print(f"Tags after addition: {tags}")
    
    print("Deduplicating...")
    unique_tags = deduplicator.deduplicate(tags)
    print(f"Unique Tags: {unique_tags}")

    # 4. Search
    print("\n--- Search ---")
    query = input("Enter search query (or press Enter for default): ")
    if not query:
        query = "papers about AI and Deep Learning"
        print(f"Using default query: {query}")

    print("Extracting query tags...")
    query_tags = searcher.extract_query_tags(query, tag_pool=unique_tags)
    print(f"Query Tags: {query_tags}")

    print("Matching against document tags...")
    score = searcher.match(query_tags, unique_tags)
    print(f"Match Score (Jaccard Similarity): {score:.2f}")
    
    if score > 0:
        print("Result: Match found!")
    else:
        print("Result: No significant match.")

if __name__ == "__main__":
    main()
