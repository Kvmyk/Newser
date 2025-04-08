import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.newser import fetch_news, handle_edit, handle_favorites, remove_favorite, add_favorite

@pytest.mark.asyncio
async def test_fetch_news_help():
    # Create mock context
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    
    # Test help command
    await fetch_news(ctx, query="help")
    
    # Verify that send was called with help message
    ctx.send.assert_called_once()
    assert "Pomoc - Komendy !news:" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_fetch_news_with_topic():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Mock the requests.get response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'results': [
            {'title': 'Test News 1', 'link': 'http://test1.com'},
            {'title': 'Test News 2', 'link': 'http://test2.com'},
            {'title': 'Test News 3', 'link': 'http://test3.com'}
        ]
    }
    
    with patch('requests.get', return_value=mock_response):
        await fetch_news(ctx, query="test")
        
        # Verify that send was called three times (3 articles)
        assert ctx.send.call_count == 3
        assert "Test News 1" in ctx.send.call_args_list[0][0][0]
        assert "Test News 2" in ctx.send.call_args_list[1][0][0]
        assert "Test News 3" in ctx.send.call_args_list[2][0][0]

@pytest.mark.asyncio
async def test_fetch_news_no_results():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    
    # Mock the requests.get response with no results
    mock_response = MagicMock()
    mock_response.json.return_value = {'results': []}
    
    with patch('requests.get', return_value=mock_response):
        await fetch_news(ctx, query="nonexistenttopic")
        
        # Verify that send was called with "no results" message
        ctx.send.assert_called_once_with("Brak wyników dla podanego zapytania.")

@pytest.mark.asyncio
async def test_fetch_news_error_handling():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    
    # Mock requests.get to raise an exception
    with patch('requests.get', side_effect=Exception("API Error")):
        await fetch_news(ctx, query="test")
        
        # Verify error message was sent
        ctx.send.assert_called_once()
        assert "Błąd podczas pobierania danych" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_fetch_news_with_redaguj():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Mock the requests.get response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'results': [
            {'title': 'Test News 1', 'content': 'Test content', 'link': 'http://test1.com'}
        ]
    }
    
    # Mock the Gemini model response
    with patch('requests.get', return_value=mock_response), \
         patch('google.generativeai.GenerativeModel.generate_content') as mock_generate:
        mock_generate.return_value.text = "Zredagowana treść"
        await fetch_news(ctx, query="redaguj test")
        
        # Verify the edit was processed
        ctx.send.assert_called_once()
        assert "Zredagowana wersja:" in ctx.send.call_args[0][0]
        assert "http://test1.com" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_add_favorite():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import last_articles, favorites
    last_articles[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'link': 'http://test1.com'},
        {'title': 'Test News 2', 'link': 'http://test2.com'}
    ]
    
    await add_favorite(ctx, 1)
    
    # Verify the favorite was added
    assert str(ctx.author.id) in favorites
    assert len(favorites[str(ctx.author.id)]) == 1
    assert favorites[str(ctx.author.id)][0]['title'] == 'Test News 1'
    ctx.send.assert_called_once()
    assert "Dodano do ulubionych" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_add_favorite_invalid_index():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import last_articles
    last_articles[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'link': 'http://test1.com'}
    ]
    
    await add_favorite(ctx, 2)  # Invalid index
    
    # Verify error message was sent
    ctx.send.assert_called_once_with("Nieprawidłowy numer wiadomości.")

@pytest.mark.asyncio
async def test_add_favorite_no_articles():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup empty last_articles
    from src.newser import last_articles
    last_articles[str(ctx.author.id)] = []
    
    await add_favorite(ctx, 1)
    
    # Verify error message was sent
    ctx.send.assert_called_once_with("Nieprawidłowy numer wiadomości.")

@pytest.mark.asyncio
async def test_handle_favorites_empty():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Clear favorites for this user
    from src.newser import favorites
    favorites[str(ctx.author.id)] = []
    
    await handle_favorites(ctx)
    
    # Verify the empty message was sent
    ctx.send.assert_called_once_with("Nie masz jeszcze żadnych ulubionych wiadomości.")

@pytest.mark.asyncio
async def test_handle_favorites_with_items():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import favorites
    favorites[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'link': 'http://test1.com'},
        {'title': 'Test News 2', 'link': 'http://test2.com'}
    ]
    
    await handle_favorites(ctx)
    
    # Verify that send was called twice (2 favorites)
    assert ctx.send.call_count == 2
    assert "Test News 1" in ctx.send.call_args_list[0][0][0]
    assert "Test News 2" in ctx.send.call_args_list[1][0][0]

@pytest.mark.asyncio
async def test_handle_edit_with_number():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import last_articles
    last_articles[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'content': 'Test content 1', 'link': 'http://test1.com'}
    ]
    
    # Mock the Gemini model response
    with patch('google.generativeai.GenerativeModel.generate_content') as mock_generate:
        mock_generate.return_value.text = "Zredagowana treść"
        await handle_edit(ctx, "1")
        
        # Verify the edit was processed
        ctx.send.assert_called_once()
        assert "Zredagowana wersja:" in ctx.send.call_args[0][0]
        assert "http://test1.com" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_edit_invalid_number():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import last_articles
    last_articles[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'content': 'Test content 1', 'link': 'http://test1.com'}
    ]
    
    await handle_edit(ctx, "2")  # Invalid index
    
    # Verify error message was sent
    ctx.send.assert_called_once_with("Nieprawidłowy numer wiadomości do redakcji.")

@pytest.mark.asyncio
async def test_remove_favorite():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import favorites
    favorites[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'link': 'http://test1.com'},
        {'title': 'Test News 2', 'link': 'http://test2.com'}
    ]
    
    await remove_favorite(ctx, 1)
    
    # Verify the favorite was removed
    assert len(favorites[str(ctx.author.id)]) == 1
    assert favorites[str(ctx.author.id)][0]['title'] == 'Test News 2'
    ctx.send.assert_called_once()
    assert "Usunięto z ulubionych" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_remove_favorite_invalid_index():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    
    # Setup test data
    from src.newser import favorites
    favorites[str(ctx.author.id)] = [
        {'title': 'Test News 1', 'link': 'http://test1.com'}
    ]
    
    await remove_favorite(ctx, 2)  # Invalid index
    
    # Verify error message was sent
    ctx.send.assert_called_once_with("Nieprawidłowy numer wiadomości lub brak ulubionych.") 