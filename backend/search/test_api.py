from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from api import app
import json

client = TestClient(app)

def test_generate_tags():
    with patch('api.tagger') as mock_tagger:
        mock_tagger.generate_tags.return_value = ["AI", "ML"]
        response = client.post("/tags/generate", json={"text": "Some text"})
        assert response.status_code == 200
        assert response.json() == {"tags": ["AI", "ML"]}

def test_deduplicate_tags():
    with patch('api.deduplicator') as mock_dedup:
        mock_dedup.deduplicate.return_value = ["AI"]
        response = client.post("/tags/deduplicate", json={"tags": ["AI", "Artificial Intelligence"]})
        assert response.status_code == 200
        assert response.json() == {"unique_tags": ["AI"]}

def test_search():
    with patch('api.searcher') as mock_searcher:
        mock_searcher.extract_query_tags.return_value = ["AI"]
        mock_searcher.match.return_value = 1.0
        
        payload = {
            "query": "papers about AI",
            "tag_pool": ["AI", "ML"]
        }
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["match_score"] == 1.0
        assert data["query_tags"] == ["AI"]

if __name__ == "__main__":
    # Simple runner if pytest is not available, but pytest is recommended
    try:
        test_generate_tags()
        print("test_generate_tags PASSED")
        test_deduplicate_tags()
        print("test_deduplicate_tags PASSED")
        test_search()
        print("test_search PASSED")
    except AssertionError as e:
        print(f"Test FAILED: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
