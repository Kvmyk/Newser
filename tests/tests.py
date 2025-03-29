import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import sys
import requests

# Add src directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the functions from your actual implementation
from newser import fetch_and_send_news, edit_news, add_favorite, favorites, last_articles

# filepath: c:\Users\Kuba\Documents\GitHub\Newser\tests\tests.py

# Absolute imports for the modules to test

class TestNewsAPI(unittest.TestCase):
    
    def setUp(self):
        # Sample news data for testing
        self.sample_news_data = {
            "status": "success",
            "totalResults": 2,
            "results": [
                {
                    "title": "Test News Title 1",
                    "description": "Test news description 1",
                    "content": "Test news content 1",
                    "url": "https://example.com/news1",
                    "source_id": "source1",
                    "pubDate": "2023-06-01 12:00:00"
                },
                {
                    "title": "Test News Title 2",
                    "description": "Test news description 2",
                    "content": "Test news content 2",
                    "url": "https://example.com/news2",
                    "source_id": "source2",
                    "pubDate": "2023-06-02 12:00:00"
                }
            ]
        }
    
    @patch('Newser.news_api.requests.get')
    def test_fetch_news_success(self, mock_get):
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_news_data
        mock_get.return_value = mock_response
        
        result = fetch_news(category="technology", language="en")
        
        self.assertEqual(result, self.sample_news_data)
        mock_get.assert_called_once()
    
    @patch('Newser.news_api.requests.get')
    def test_fetch_news_failure(self, mock_get):
        # Configure the mock to return a failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = fetch_news(category="technology", language="en")
        
        self.assertIsNone(result)
        mock_get.assert_called_once()
    
    def test_parse_news_response(self):
        parsed_news = parse_news_response(self.sample_news_data)
        
        self.assertEqual(len(parsed_news), 2)
        self.assertEqual(parsed_news[0]['title'], "Test News Title 1")
        self.assertEqual(parsed_news[1]['title'], "Test News Title 2")

class TestBotCommands(unittest.TestCase):

    @patch('Newser.bot_commands.fetch_news')
    async def test_process_news_command(self, mock_fetch_news):
        # Setup mock data
        mock_fetch_news.return_value = {
            "status": "success",
            "results": [{"title": "Test News", "url": "https://example.com"}]
        }
        
        # Mock Discord context
        ctx = MagicMock()
        
        # Test the command
        result = await process_news_command(ctx, category="technology")
        
        # Assertions
        self.assertTrue(result)
        ctx.send.assert_called_once()
        mock_fetch_news.assert_called_with(category="technology")

class TestAIIntegration(unittest.TestCase):

    @patch('Newser.ai_integration.genai.GenerativeModel')
    async def test_summarize_news(self, mock_genai_model):
        # Setup mock AI response
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a summarized version of the news article."
        mock_model_instance.generate_content.return_value = mock_response
        mock_genai_model.return_value = mock_model_instance
        
        news_content = "This is a very long news article that needs to be summarized."
        summary = await summarize_news(news_content)
        
        self.assertEqual(summary, "This is a summarized version of the news article.")
        mock_model_instance.generate_content.assert_called_once()

class TestNewsBot(unittest.TestCase):
    
    def setUp(self):
        # Sample news data for testing
        self.sample_news_data = {
            "status": "success",
            "totalResults": 2,
            "results": [
                {
                    "title": "Test News Title 1",
                    "description": "Test news description 1",
                    "content": "Test news content 1",
                    "link": "https://example.com/news1",
                    "source_id": "source1",
                    "pubDate": "2023-06-01 12:00:00"
                },
                {
                    "title": "Test News Title 2",
                    "description": "Test news description 2",
                    "content": "Test news content 2",
                    "link": "https://example.com/news2",
                    "source_id": "source2",
                    "pubDate": "2023-06-02 12:00:00"
                }
            ]
        }
        
        # Reset the global state variables before each test
        global favorites, last_articles
        favorites.clear()
        last_articles.clear()
    
    @patch('requests.get')
    async def test_fetch_and_send_news(self, mock_get):
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_news_data
        mock_get.return_value = mock_response
        
        # Create a mock context
        ctx = AsyncMock()
        
        # Call the function
        await fetch_and_send_news(ctx, "technology")
        
        # Verify the context was called to send messages
        self.assertEqual(ctx.send.call_count, 3)  # One call for each article + an empty result would be different
        
        # Verify the request was made with the right parameters
        mock_get.assert_called_once()
        # Check if query parameter is included in the URL
        self.assertIn("technology", mock_get.call_args[0][0])
    
    @patch('requests.get')
    async def test_fetch_and_send_news_no_results(self, mock_get):
        # Configure the mock to return a response with no results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "results": []}
        mock_get.return_value = mock_response
        
        # Create a mock context
        ctx = AsyncMock()
        
        # Call the function
        await fetch_and_send_news(ctx, "nonexistent_query")
        
        # Verify the context was called to send a "no results" message
        ctx.send.assert_called_once_with("Brak wyników dla podanego zapytania.")
    
    @patch('requests.get')
    @patch('google.generativeai.GenerativeModel')
    async def test_edit_news(self, mock_genai_model, mock_get):
        # Configure the request mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_news_data
        mock_get.return_value = mock_response
        
        # Configure the AI model mock
        mock_model_instance = MagicMock()
        mock_ai_response = MagicMock()
        mock_ai_response.text = "This is a summarized version of the news article."
        mock_model_instance.generate_content.return_value = mock_ai_response
        mock_genai_model.return_value = mock_model_instance
        
        # Create a mock context
        ctx = AsyncMock()
        
        # Call the function
        await edit_news(ctx, "technology")
        
        # Verify the AI was called with the right content
        mock_model_instance.generate_content.assert_called_once()
        # Verify the context was called to send the edited news
        ctx.send.assert_called_once()
        self.assertIn("Zredagowana wersja", ctx.send.call_args[0][0])
    
    async def test_add_favorite(self):
        # Create a mock context with a user
        ctx = AsyncMock()
        ctx.author.id = 12345
        
        # Setup test data - simulate that this was previously stored by fetch_and_send_news
        user_id = str(ctx.author.id)
        last_articles[user_id] = [
            {"title": "Test News 1", "link": "https://example.com/1"},
            {"title": "Test News 2", "link": "https://example.com/2"}
        ]
        
        # Call the function to add the first article to favorites
        await add_favorite(ctx, 1)
        
        # Verify the article was added to favorites
        self.assertIn(user_id, favorites)
        self.assertEqual(len(favorites[user_id]), 1)
        self.assertEqual(favorites[user_id][0]["title"], "Test News 1")
        
        # Verify the context was called to send a confirmation
        ctx.send.assert_called_once()
        self.assertIn("Dodano do ulubionych", ctx.send.call_args[0][0])

if __name__ == '__main__':
    unittest.main()