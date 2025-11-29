import unittest
from unittest.mock import MagicMock, patch
import json
import os
from tagger import TagGenerator
from deduplicator import TagDeduplicator
from search import TagSearch

class TestTagSystem(unittest.TestCase):
    def setUp(self):
        os.environ["GOOGLE_API_KEY"] = "dummy"
        # print(f"DEBUG: setUp set API KEY: {os.environ.get('GOOGLE_API_KEY')}")

    @patch('google.genai.Client')
    def test_tag_generation(self, mock_client_cls):
        # Mock the client instance
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock the models.generate_content method
        mock_response = MagicMock()
        mock_response.text = '["AI", "Machine Learning"]'
        mock_client.models.generate_content.return_value = mock_response

        tagger = TagGenerator()
        tags = tagger.generate_tags("Some text about AI")
        self.assertEqual(tags, ["AI", "Machine Learning"])

    @patch('google.genai.Client')
    def test_deduplication(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = '["AI"]'
        mock_client.models.generate_content.return_value = mock_response

        deduplicator = TagDeduplicator()
        unique_tags = deduplicator.deduplicate(["AI", "Artificial Intelligence"])
        self.assertEqual(unique_tags, ["AI"])

    @patch('google.genai.Client')
    def test_search_extraction(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        # Case 1: Match found in pool
        mock_response.text = '["Deep Learning"]'
        mock_client.models.generate_content.return_value = mock_response

        searcher = TagSearch()
        query_tags = searcher.extract_query_tags("papers on Deep Learning", tag_pool=["Deep Learning", "AI"])
        self.assertEqual(query_tags, ["Deep Learning"])

        # Case 2: No match in pool
        mock_response.text = '["other"]'
        query_tags = searcher.extract_query_tags("papers on Cooking", tag_pool=["Deep Learning", "AI"])
        self.assertEqual(query_tags, ["other"])

    def test_match_logic(self):
        # No mocking needed for pure logic
        # We need to instantiate TagSearch, but we can mock the init to avoid API key check/Gemini init
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy"}):
             with patch('google.genai.Client'):
                searcher = TagSearch()
                score = searcher.match(["AI"], ["AI", "ML"])
                self.assertEqual(score, 0.5) # 1 intersection / 2 union

                score = searcher.match(["AI"], ["Food"])
                self.assertEqual(score, 0.0)

    def test_search_documents(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy"}):
             with patch('google.genai.Client') as mock_client_cls:
                # Mock extract_query_tags
                mock_client = MagicMock()
                mock_client_cls.return_value = mock_client
                
                mock_response = MagicMock()
                mock_response.text = '["AI"]'
                mock_client.models.generate_content.return_value = mock_response
                
                searcher = TagSearch()
                # Mock extract_query_tags directly for cleaner unit test of search_documents logic
                searcher.extract_query_tags = MagicMock(return_value=["AI"])
                
                docs = [
                    {"id": "1", "tags": ["Food", "Cooking"]},
                    {"id": "2", "tags": ["AI", "ML"]}, # High match
                    {"id": "3", "tags": ["AI", "Food"]}, # Partial match
                ]
                
                results = searcher.search_documents("query", docs, ["AI", "Food"])
                
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0]["id"], "2")
                self.assertEqual(results[0]["_score"], 1.0) # AI vs AI,ML -> 0.5? Wait.
                # My previous logic:
                # AI vs AI, ML -> intersection {AI}, union {AI, ML} -> 1/2 = 0.5
                # AI vs AI, Food -> intersection {AI}, union {AI, Food} -> 1/2 = 0.5
                
                # In the previous test code I wrote:
                # results[0]["_score"], 1.0
                # results[1]["_score"], 0.5
                # But that was for the SECOND set of docs in the test.
                
                # Let's align with the docs I defined in THIS replacement block.
                # docs[1] is id=2, tags=["AI", "ML"]. Query tags=["AI"]. Score = 0.5.
                # docs[2] is id=3, tags=["AI", "Food"]. Query tags=["AI"]. Score = 0.5.
import unittest
from unittest.mock import MagicMock, patch
import json
import os
from tagger import TagGenerator
from deduplicator import TagDeduplicator
from search import TagSearch

class TestTagSystem(unittest.TestCase):
    def setUp(self):
        os.environ["GOOGLE_API_KEY"] = "dummy"
        # print(f"DEBUG: setUp set API KEY: {os.environ.get('GOOGLE_API_KEY')}")

    @patch('google.genai.Client')
    def test_tag_generation(self, mock_client_cls):
        # Mock the client instance
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock the models.generate_content method
        mock_response = MagicMock()
        mock_response.text = '["AI", "Machine Learning"]'
        mock_client.models.generate_content.return_value = mock_response

        tagger = TagGenerator()
        tags = tagger.generate_tags("Some text about AI")
        self.assertEqual(tags, ["AI", "Machine Learning"])

    @patch('google.genai.Client')
    def test_deduplication(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = '["AI"]'
        mock_client.models.generate_content.return_value = mock_response

        deduplicator = TagDeduplicator()
        unique_tags = deduplicator.deduplicate(["AI", "Artificial Intelligence"])
        self.assertEqual(unique_tags, ["AI"])

    @patch('google.genai.Client')
    def test_search_extraction(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_response = MagicMock()
        # Case 1: Match found in pool
        mock_response.text = '["Deep Learning"]'
        mock_client.models.generate_content.return_value = mock_response

        searcher = TagSearch()
        query_tags = searcher.extract_query_tags("papers on Deep Learning", tag_pool=["Deep Learning", "AI"])
        self.assertEqual(query_tags, ["Deep Learning"])

        # Case 2: No match in pool
        mock_response.text = '["other"]'
        query_tags = searcher.extract_query_tags("papers on Cooking", tag_pool=["Deep Learning", "AI"])
        self.assertEqual(query_tags, ["other"])

    def test_match_logic(self):
        # No mocking needed for pure logic
        # We need to instantiate TagSearch, but we can mock the init to avoid API key check/Gemini init
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy"}):
             with patch('google.genai.Client'):
                searcher = TagSearch()
                score = searcher.match(["AI"], ["AI", "ML"])
                self.assertEqual(score, 0.5) # 1 intersection / 2 union

                score = searcher.match(["AI"], ["Food"])
                self.assertEqual(score, 0.0)

    def test_search_documents(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy"}):
             with patch('google.genai.Client') as mock_client_cls:
                # Mock extract_query_tags
                mock_client = MagicMock()
                mock_client_cls.return_value = mock_client
                
                mock_response = MagicMock()
                mock_response.text = '["AI"]'
                mock_client.models.generate_content.return_value = mock_response
                
                searcher = TagSearch()
                # Mock extract_query_tags directly for cleaner unit test of search_documents logic
                searcher.extract_query_tags = MagicMock(return_value=["AI"])
                
                docs = [
                    {"id": "1", "tags": ["Food", "Cooking"]},
                    {"id": "2", "tags": ["AI", "ML"]}, # High match
                    {"id": "3", "tags": ["AI", "Food"]}, # Partial match
                ]
                
                results = searcher.search_documents("query", docs, ["AI", "Food"])
                
                # First block: extract_query_tags returns ["AI"]
                # Doc 2: ["AI", "ML"] -> Score 0.5
                # Doc 3: ["AI", "Food"] -> Score 0.5
                self.assertEqual(len(results), 2)
                # Order is stable/undefined for equal scores, but both are 0.5
                self.assertEqual(results[0]["_score"], 0.5)
                self.assertEqual(results[1]["_score"], 0.5)
                
                # Second block
                docs = [
                    {"id": "1", "tags": ["Food"]},
                    {"id": "2", "tags": ["AI"]}, # Exact match 1.0
                    {"id": "3", "tags": ["AI", "ML"]}, # 0.5
                ]
                results = searcher.search_documents("query", docs, ["AI"])
                
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0]["id"], "2")
                self.assertEqual(results[0]["_score"], 1.0)
                self.assertEqual(results[1]["id"], "3")
                self.assertEqual(results[1]["_score"], 0.5)

    def test_search_filtering(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy"}):
             with patch('google.genai.Client') as mock_client_cls:
                mock_client = MagicMock()
                mock_client_cls.return_value = mock_client
                mock_response = MagicMock()
                mock_response.text = '["AI"]'
                mock_client.models.generate_content.return_value = mock_response
                
                searcher = TagSearch()
                searcher.extract_query_tags = MagicMock(return_value=["AI"])
                
                docs = [
                    {"id": "1", "tags": ["AI"], "group_id": "g1", "owner_id": "u1"},
                    {"id": "2", "tags": ["AI"], "group_id": "g2", "owner_id": "u2"},
                    {"id": "3", "tags": ["AI"], "group_id": "g1", "owner_id": "u2"},
                ]
                
                # Test Group Filter
                results = searcher.search_documents("query", docs, ["AI"], group_id="g1")
                self.assertEqual(len(results), 2)
                ids = sorted([r["id"] for r in results])
                self.assertEqual(ids, ["1", "3"])
                
                # Test Owner Filter
                results = searcher.search_documents("query", docs, ["AI"], owner_id="u2")
                self.assertEqual(len(results), 2)
                ids = sorted([r["id"] for r in results])
                self.assertEqual(ids, ["2", "3"])
                
                # Test Both Filters
                results = searcher.search_documents("query", docs, ["AI"], group_id="g1", owner_id="u2")
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["id"], "3")
                
                # Test No Filter
                results = searcher.search_documents("query", docs, ["AI"])
                self.assertEqual(len(results), 3)

if __name__ == '__main__':
    # Ensure dummy key for tests if not present, though we mock mostly
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = "dummy"
    unittest.main()
