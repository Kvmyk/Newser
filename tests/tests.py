import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import json

# Add the src directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.newser import fetch_and_send_news, edit_news, add_favorite, fetch_news

class TestNewserBot(unittest.TestCase):
    def setUp(self):
        # Create mock context
        self.ctx = AsyncMock()
        self.ctx.author.id = 12345
        
        # Sample news data for testing
        self.sample_news = {
            "status": "success",
            "results": [
                {
                    "title": "Test News Title 1",
                    "description": "This is a test news description 1",
                    "link": "https://example.com/news1"
                },
                {
                    "title": "Test News Title 2",
                    "description": "This is a test news description 2",
                    "link": "https://example.com/news2"
                },
                {
                    "title": "Test News Title 3",
                    "description": "This is a test news description 3",
                    "link": "https://example.com/news3"
                }
            ]
        }

    @patch('src.newser.requests.get')
    async def test_fetch_and_send_news(self, mock_get):
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_news
        mock_get.return_value = mock_response

        # Call the function
        await fetch_and_send_news(self.ctx, "test query")
        
        # Assertions
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(self.ctx.send.call_count, 3)  # Should send 3 messages for 3 news items

    @patch('src.newser.requests.get')
    @patch('src.newser.model.generate_content')
    async def test_edit_news(self, mock_generate_content, mock_get):
        # Configure the mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [self.sample_news["results"][0]]}
        mock_get.return_value = mock_response
        
        mock_ai_response = MagicMock()
        mock_ai_response.text = "This is a redacted version of the news"
        mock_generate_content.return_value = mock_ai_response

        # Call the function
        await edit_news(self.ctx, "test query")
        
        # Assertions
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_generate_content.call_count, 1)
        self.assertEqual(self.ctx.send.call_count, 1)
        
    @patch('src.newser.last_articles')
    @patch('src.newser.favorites')
    async def test_add_favorite(self, mock_favorites, mock_last_articles):
        # Configure the mocks
        mock_last_articles.get.return_value = self.sample_news["results"]
        mock_favorites.get.return_value = []
        
        # Call the function
        await add_favorite(self.ctx, 1)
        
        # Assertions
        self.ctx.send.assert_called_once()
        # The call_args gets the args of the last call
        self.assertIn("Dodano do ulubionych", self.ctx.send.call_args[0][0])

    @patch('src.newser.fetch_and_send_news')
    @patch('src.newser.edit_news')
    @patch('src.newser.add_favorite')
    async def test_fetch_news_command_router(self, mock_add_favorite, mock_edit_news, mock_fetch_and_send_news):
        # Test normal news fetching
        await fetch_news(self.ctx, query="poland")
        mock_fetch_and_send_news.assert_called_once_with(self.ctx, "poland")
        
        # Reset mocks
        mock_fetch_and_send_news.reset_mock()
        mock_edit_news.reset_mock()
        
        # Test news editing
        await fetch_news(self.ctx, query="redaguj poland")
        mock_edit_news.assert_called_once_with(self.ctx, "poland")
        
        # Test help command
        await fetch_news(self.ctx, query="help")
        self.ctx.send.assert_called_once()
        
        # Reset mock
        self.ctx.send.reset_mock()
        
        # Test no query
        await fetch_news(self.ctx, query=None)
        self.ctx.send.assert_called_once()

    @patch('src.newser.last_articles')
    @patch('src.newser.favorites')
    async def test_favorites_display(self, mock_favorites, mock_last_articles):
        # Configure the mocks
        user_id = str(self.ctx.author.id)
        mock_favorites.__contains__.return_value = True
        mock_favorites.__getitem__.return_value = [
            {
                'title': 'Favorite Article 1',
                'link': 'https://example.com/fav1'
            },
            {
                'title': 'Favorite Article 2',
                'link': 'https://example.com/fav2'
            }
        ]
        
        # Call the function
        await fetch_news(self.ctx, query="ulubione")
        
        # Assertions
        self.assertEqual(self.ctx.send.call_count, 2)  # Two favorite articles

if __name__ == '__main__':
    unittest.main()