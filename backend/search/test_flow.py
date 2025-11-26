import unittest
from unittest.mock import MagicMock, patch
import json
from tagger import TagGenerator
from deduplicator import TagDeduplicator
from search import TagSearch

class TestTagSystem(unittest.TestCase):

    @patch('google.generativeai.GenerativeModel')
    def test_tag_generation(self, mock_model_cls):
        # Mock the response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '["AI", "Machine Learning"]'
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        tagger = TagGenerator()
        tags = tagger.generate_tags("Some text about AI")
        self.assertEqual(tags, ["AI", "Machine Learning"])

    @patch('google.generativeai.GenerativeModel')
    def test_deduplication(self, mock_model_cls):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '["AI"]'
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        deduplicator = TagDeduplicator()
        unique_tags = deduplicator.deduplicate(["AI", "Artificial Intelligence"])
        self.assertEqual(unique_tags, ["AI"])

    @patch('google.generativeai.GenerativeModel')
    def test_search_extraction(self, mock_model_cls):
        mock_model = MagicMock()
        mock_response = MagicMock()
        # Case 1: Match found in pool
        mock_response.text = '["Deep Learning"]'
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

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
             with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    searcher = TagSearch()
                    score = searcher.match(["AI"], ["AI", "ML"])
                    self.assertEqual(score, 0.5) # 1 intersection / 2 union

                    score = searcher.match(["AI"], ["Food"])
                    self.assertEqual(score, 0.0)

import os
if __name__ == '__main__':
    # Ensure dummy key for tests if not present, though we mock mostly
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = "dummy"
    unittest.main()
