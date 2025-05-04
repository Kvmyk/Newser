import pytest
import sqlite3
import pathlib
import os
from datetime import datetime
from src.db.database import (
    init_db,
    add_favorite_db,
    get_favorites_db,
    remove_favorite_db,
    DB_DIR,
    DB_PATH  # Dodano brakującą zmienną
)
import src.db.database as database
from unittest.mock import AsyncMock, MagicMock, patch
from src.newser import (
    fetch_news,
    handle_edit,
    handle_favorites,
    remove_favorite,
    add_favorite,
)


@pytest.fixture
def test_db():
    """Fixture tworzący tymczasową bazę danych do testów"""
    # Tworzenie tymczasowego pliku bazy danych ze zmienioną nazwą dla każdego testu
    import tempfile
    import pathlib
    
    # Zapisz oryginalne ustawienie ścieżki bazy danych
    original_db_path = database.DB_PATH
    
    # Utwórz tymczasowy plik bazy danych
    temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = pathlib.Path(temp_db_file.name)
    temp_db_file.close()
    
    # Przekieruj ścieżkę bazy danych na tymczasowy plik
    database.DB_PATH = test_db_path
    
    # Inicjalizuj bazę danych
    init_db()
    
    # Zwróć ścieżkę do testów
    yield test_db_path
    
    # Po zakończeniu testu przywróć oryginalną ścieżkę
    database.DB_PATH = original_db_path
    
    # Usuń tymczasowy plik bazy danych
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except (OSError):
            pass  # Ignoruj błędy usuwania pliku


@pytest.mark.asyncio
async def test_database_article_operations(test_db):
    """Test operacji na artykułach w bazie danych"""
    user_id = "123456789"
    
    # Testowy artykuł z aktualną tematyką
    test_article = {
        "title": "Nowy procesor M3 Ultra - Apple prezentuje przełomową technologię",
        "link": "https://www.apple.com/newsroom/2024/m3-ultra-announcement"
    }
    
    # Dodanie artykułu
    add_favorite_db(user_id, test_article["title"], test_article["link"])
    
    # Sprawdzenie czy artykuł został dodany
    favorites = get_favorites_db(user_id)
    assert len(favorites) == 1
    assert favorites[0]["title"] == test_article["title"]
    assert favorites[0]["link"] == test_article["link"]
    
    # Usunięcie artykułu
    article_id = favorites[0]["id"]
    assert remove_favorite_db(user_id, article_id) == True
    
    # Weryfikacja usunięcia
    assert len(get_favorites_db(user_id)) == 0


@pytest.mark.asyncio
async def test_multiple_users_isolation(test_db):
    """Test izolacji danych między użytkownikami"""
    user1_id = "111222333"
    user2_id = "444555666"
    
    # Dodanie artykułów dla różnych użytkowników
    test_articles = {
        user1_id: [
            {
                "title": "Przełom w technologii kwantowej - polski naukowiec na czele projektu",
                "link": "https://www.nauka.gov.pl/aktualnosci/przelom-kwantowy-2024"
            },
            {
                "title": "Nowa strategia cyberbezpieczeństwa UE na lata 2024-2030",
                "link": "https://cybersecurity-europe.eu/strategy-2024"
            }
        ],
        user2_id: [
            {
                "title": "SpaceX ogłasza pierwszą turystyczną misję na Marsa",
                "link": "https://www.spacex.com/mars-mission-2024"
            }
        ]
    }
    
    # Dodanie artykułów do bazy
    for user_id, articles in test_articles.items():
        for article in articles:
            add_favorite_db(user_id, article["title"], article["link"])
    
    # Sprawdzenie izolacji danych
    user1_favorites = get_favorites_db(user1_id)
    user2_favorites = get_favorites_db(user2_id)
    
    assert len(user1_favorites) == 2
    assert len(user2_favorites) == 1
    assert "kwantowej" in user1_favorites[0]["title"]
    assert "SpaceX" in user2_favorites[0]["title"]


@pytest.mark.asyncio
async def test_database_error_handling(test_db):
    """Test obsługi błędów bazy danych"""
    user_id = "999888777"
    
    # Test usuwania nieistniejącego artykułu
    assert remove_favorite_db(user_id, 99999) == False
    
    # Test dodawania artykułu z nieprawidłowymi danymi
    with pytest.raises(sqlite3.Error):
        add_favorite_db(None, None, None)
    
    # Test pobierania dla nieistniejącego użytkownika
    empty_favorites = get_favorites_db("nonexistent_user")
    assert len(empty_favorites) == 0


@pytest.mark.asyncio
async def test_database_article_limits(test_db):
    """Test limitów i wydajności bazy danych"""
    user_id = "777666555"
    
    # Dodanie większej liczby artykułów
    for i in range(100):
        title = f"Artykuł testowy {i}: Najnowsze trendy w AI {i+1}/2024"
        link = f"https://ai-news.com/trends-{i}-2024"
        add_favorite_db(user_id, title, link)
    
    # Sprawdzenie poprawności zapisanych danych
    favorites = get_favorites_db(user_id)
    assert len(favorites) == 100
    assert all("Artykuł testowy" in f["title"] for f in favorites)
    
    # Test wydajności usuwania
    for favorite in favorites[:50]:
        assert remove_favorite_db(user_id, favorite["id"]) == True
    
    # Weryfikacja pozostałych artykułów
    remaining = get_favorites_db(user_id)
    assert len(remaining) == 50


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
        "results": [
            {
                "title": "Nowa polityka zagraniczna Polski wobec krajów UE",
                "link": "https://www.gazeta.pl/wiadomosci/7,114884,30675821,polityka-zagraniczna.html",
            },
            {
                "title": "Wzrost inflacji w Polsce - eksperci alarmują",
                "link": "https://www.onet.pl/informacje/onetwiadomosci/gospodarka-wzrost-inflacji/qm6j3kl",
            },
            {
                "title": "Minister Sportu o planach rozwoju infrastruktury na Euro 2028",
                "link": "https://www.rmf24.pl/tylko-w-rmf24/wywiady/news-minister-sportu-o-planach-na-przyszlosc,nId,7312654",
            },
        ]
    }

    with patch("requests.get", return_value=mock_response):
        await fetch_news(ctx, query="test")

        # Verify that send was called three times (3 articles)
        assert ctx.send.call_count == 3
        assert "Nowa polityka zagraniczna Polski" in ctx.send.call_args_list[0][0][0]
        assert "Wzrost inflacji w Polsce" in ctx.send.call_args_list[1][0][0]
        assert "Minister Sportu o planach" in ctx.send.call_args_list[2][0][0]


@pytest.mark.asyncio
async def test_fetch_news_no_results():
    ctx = AsyncMock()
    ctx.send = AsyncMock()

    # Mock the requests.get response with no results
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}

    with patch("requests.get", return_value=mock_response):
        await fetch_news(ctx, query="nonexistenttopic")

        # Verify that send was called with "no results" message
        ctx.send.assert_called_once_with("Brak wyników dla podanego zapytania.")


@pytest.mark.asyncio
async def test_fetch_news_error_handling():
    ctx = AsyncMock()
    ctx.send = AsyncMock()

    # Mock requests.get to raise an exception
    with patch("requests.get", side_effect=Exception("API Error")):
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
        "results": [
            {
                "title": "Debata polityczna w Sejmie - najważniejsze ustalenia",
                "content": "W dniu wczorajszym w Sejmie odbyła się burzliwa debata dotycząca projektu nowej ustawy o szkolnictwie wyższym. Posłowie wszystkich ugrupowań przedstawili swoje stanowiska. Opozycja krytykuje zwłaszcza artykuły dotyczące finansowania uczelni prywatnych.",
                "link": "https://www.wprost.pl/kraj/11334507/debata-polityczna-w-sejmie.html",
            }
        ]
    }

    # Mock the Gemini model response
    with patch("requests.get", return_value=mock_response), patch(
        "google.generativeai.GenerativeModel.generate_content"
    ) as mock_generate:
        mock_generate.return_value.text = "Wczoraj w Sejmie RP miała miejsce debata nad projektem ustawy o szkolnictwie wyższym. Przedstawiciele wszystkich partii zabierali głos w dyskusji. Szczególnie kontrowersyjne okazały się zapisy o finansowaniu niepublicznych uczelni, co wywołało sprzeciw opozycji."
        await fetch_news(ctx, query="redaguj test")

        # Verify the edit was processed
        ctx.send.assert_called_once()
        assert "Zredagowana wersja:" in ctx.send.call_args[0][0]
        assert (
            "https://www.wprost.pl/kraj/11334507/debata-polityczna-w-sejmie.html"
            in ctx.send.call_args[0][0]
        )


@pytest.mark.asyncio
async def test_add_favorite():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    user_id = str(ctx.author.id)
    
    # Przygotowanie danych testowych
    from src.newser import last_articles
    
    last_articles[user_id] = [
        {
            "title": "PKB Polski wzrósł o 3,5% w pierwszym kwartale 2023",
            "link": "https://www.money.pl/gospodarka/pkb-polski-wzrost-2023,263,0,2526789.html",
        },
        {
            "title": "Kolejne rozmowy pokojowe zakończone fiaskiem",
            "link": "https://www.tvn24.pl/wiadomosci-ze-swiata,2/kolejne-rozmowy-pokojowe,1280564.html",
        },
    ]
    
    # Usuń wszystkie dotychczasowe ulubione z bazy danych
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        conn.commit()
    
    # Wykonaj test
    await add_favorite(ctx, 1)
    
    # Sprawdź czy zostało dodane do bazy danych
    favorites = get_favorites_db(user_id)
    assert len(favorites) == 1
    assert favorites[0]["title"] == "PKB Polski wzrósł o 3,5% w pierwszym kwartale 2023"
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
        {
            "title": "Nowe inwestycje w przemyśle - 2 mld zł na rozwój sektora motoryzacyjnego",
            "link": "https://www.interia.pl/biznes/news-nowe-inwestycje-w-przemysle,nId,7098442",
        }
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
    user_id = str(ctx.author.id)
    
    # Usuń wszystkie ulubione z bazy dla tego użytkownika
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        conn.commit()
    
    await handle_favorites(ctx)
    
    # Sprawdź czy wyświetlono komunikat o braku ulubionych
    ctx.send.assert_called_once_with("Nie masz jeszcze żadnych ulubionych wiadomości.")


@pytest.mark.asyncio
async def test_handle_favorites_with_items():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    user_id = str(ctx.author.id)
    
    # Usuń istniejące ulubione i dodaj testowe artykuły
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        conn.commit()
    
    add_favorite_db(user_id, "Nowy projekt ustawy o ochronie środowiska - co się zmieni?", 
                   "https://www.rp.pl/polityka/art39087981-nowy-projekt-ustawy")
    add_favorite_db(user_id, "Reforma edukacji 2023 - najważniejsze zmiany dla uczniów i nauczycieli", 
                   "https://www.newsweek.pl/polska/spoleczenstwo/reforma-edukacji-2023/4n8xjlp")
    
    await handle_favorites(ctx)
    
    # Sprawdź czy wyświetlono oba artykuły
    assert ctx.send.call_count == 2
    assert "Nowy projekt ustawy o ochronie środowiska" in ctx.send.call_args_list[0][0][0]
    assert "Reforma edukacji 2023" in ctx.send.call_args_list[1][0][0]


@pytest.mark.asyncio
async def test_handle_edit_with_number():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123

    # Setup test data
    from src.newser import last_articles

    last_articles[str(ctx.author.id)] = [
        {
            "title": "Nowe regulacje prawne w Unii Europejskiej - wpływ na gospodarkę Polski",
            "content": "Komisja Europejska przyjęła wczoraj pakiet nowych regulacji dotyczących handlu emisjami CO2. Państwa członkowskie będą musiały dostosować krajowe przepisy do końca 2024 roku. Polska delegacja zgłosiła zastrzeżenia do niektórych rozwiązań, uznając je za zbyt restrykcyjne dla rozwijających się gospodarek.",
            "link": "https://www.polsatnews.pl/wiadomosc/2023-05-12/nowe-regulacje-prawne-w-unii-europejskiej",
        }
    ]

    # Mock the Gemini model response
    with patch("google.generativeai.GenerativeModel.generate_content") as mock_generate:
        mock_generate.return_value.text = "Komisja Europejska zatwierdziła nowy pakiet przepisów regulujących handel emisjami dwutlenku węgla. Kraje UE mają czas do końca przyszłego roku na implementację tych zasad. Przedstawiciele Polski wyrazili obawy co do niektórych zapisów, które mogą negatywnie wpłynąć na gospodarki będące w fazie rozwoju."
        await handle_edit(ctx, "1")

        # Verify the edit was processed
        ctx.send.assert_called_once()
        assert "Zredagowana wersja:" in ctx.send.call_args[0][0]
        assert (
            "https://www.polsatnews.pl/wiadomosc/2023-05-12/nowe-regulacje-prawne-w-unii-europejskiej"
            in ctx.send.call_args[0][0]
        )


@pytest.mark.asyncio
async def test_handle_edit_invalid_number():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123

    # Setup test data
    from src.newser import last_articles

    last_articles[str(ctx.author.id)] = [
        {
            "title": "Nowe dane gospodarcze - analiza ekspertów",
            "content": "Główny Urząd Statystyczny opublikował dzisiaj dane dotyczące inflacji oraz bezrobocia za ostatni kwartał. Ekonomiści wskazują na pozytywne trendy w zatrudnieniu przy jednoczesnym spowolnieniu wzrostu cen.",
            "link": "https://www.wnp.pl/finanse/nowe-dane-gospodarcze-analiza,673259.html",
        }
    ]

    await handle_edit(ctx, "2")  # Invalid index

    # Verify error message was sent
    ctx.send.assert_called_once_with("Nieprawidłowy numer wiadomości do redakcji.")


@pytest.mark.asyncio
async def test_remove_favorite():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    user_id = str(ctx.author.id)
    
    # Usuń istniejące ulubione i dodaj testowe artykuły
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        conn.commit()
    
    # Dodaj dwa artykuły do bazy
    add_favorite_db(user_id, "Rozwój sztucznej inteligencji w Polsce - raport ministerstwa cyfryzacji", 
                   "https://www.pb.pl/technologie/rozwoj-sztucznej-inteligencji-w-polsce,1548321")
    add_favorite_db(user_id, "Nowe odkrycie polskich archeologów - sensacyjne znalezisko sprzed 3000 lat", 
                   "https://www.naukawpolsce.pl/aktualnosci/news,96325,nowe-odkrycie-polskich-archeologow.html")
    
    # Najpierw wywołaj handle_favorites aby zaktualizować mapowanie id
    await handle_favorites(ctx)
    ctx.send.reset_mock()  # Reset mock, aby licznik był czysty
    
    # Teraz spróbuj usunąć pierwszy element
    await remove_favorite(ctx, 1)
    
    # Sprawdź czy zostało usunięte z bazy
    favorites = get_favorites_db(user_id)
    assert len(favorites) == 1
    assert "Nowe odkrycie polskich archeologów" in favorites[0]["title"]
    
    # Sprawdź czy wysłano potwierdzenie usunięcia
    ctx.send.assert_called()
    assert "Usunięto artykuł numer 1" in ctx.send.call_args_list[0][0][0]


@pytest.mark.asyncio
async def test_remove_favorite_invalid_index():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = 123
    user_id = str(ctx.author.id)
    
    # Usuń istniejące ulubione i dodaj testowy artykuł
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
        conn.commit()
    
    # Dodaj jeden artykuł do bazy
    add_favorite_db(user_id, "Raport ekonomiczny 2023 - zdrowie polskiej gospodarki", 
                   "https://www.pap.pl/aktualnosci/raport-ekonomiczny-2023-zdrowie-gospodarki")
    
    # Najpierw wywołaj handle_favorites aby zaktualizować mapowanie id
    await handle_favorites(ctx)
    ctx.send.reset_mock()  # Reset mock, aby licznik był czysty
    
    # Teraz spróbuj usunąć nieistniejący element
    await remove_favorite(ctx, 2)  # Nieprawidłowy indeks
    
    # Sprawdź czy wysłano komunikat o błędzie - poprawiona asercja
    assert "odświeżanie" in ctx.send.call_args_list[0][0][0].lower() or "nie znaleziono" in ctx.send.call_args_list[0][0][0].lower() or "spróbuj ponownie" in ctx.send.call_args_list[0][0][0].lower()
