import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.newser import (
    fetch_news,
    handle_edit,
    handle_favorites,
    remove_favorite,
    add_favorite,
)


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

    # Setup test data
    from src.newser import last_articles, favorites

    last_articles[str(ctx.author.id)] = [
        {
            "title": "PKB Polski wzrósł o 3,5% w pierwszym kwartale 2023",
            "link": "https://www.money.pl/gospodarka/pkb-polski-wzrost-2023,263,0,2526789.html",
        },
        {
            "title": "Kolejne rozmowy pokojowe zakończone fiaskiem",
            "link": "https://www.tvn24.pl/wiadomosci-ze-swiata,2/kolejne-rozmowy-pokojowe,1280564.html",
        },
    ]

    await add_favorite(ctx, 1)

    # Verify the favorite was added
    assert str(ctx.author.id) in favorites
    assert len(favorites[str(ctx.author.id)]) == 1
    assert (
        favorites[str(ctx.author.id)][0]["title"]
        == "PKB Polski wzrósł o 3,5% w pierwszym kwartale 2023"
    )
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
        {
            "title": "Nowy projekt ustawy o ochronie środowiska - co się zmieni?",
            "link": "https://www.rp.pl/polityka/art39087981-nowy-projekt-ustawy",
        },
        {
            "title": "Reforma edukacji 2023 - najważniejsze zmiany dla uczniów i nauczycieli",
            "link": "https://www.newsweek.pl/polska/spoleczenstwo/reforma-edukacji-2023/4n8xjlp",
        },
    ]

    await handle_favorites(ctx)

    # Verify that send was called twice (2 favorites)
    assert ctx.send.call_count == 2
    assert (
        "Nowy projekt ustawy o ochronie środowiska" in ctx.send.call_args_list[0][0][0]
    )
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

    # Setup test data
    from src.newser import favorites

    favorites[str(ctx.author.id)] = [
        {
            "title": "Rozwój sztucznej inteligencji w Polsce - raport ministerstwa cyfryzacji",
            "link": "https://www.pb.pl/technologie/rozwoj-sztucznej-inteligencji-w-polsce,1548321",
        },
        {
            "title": "Nowe odkrycie polskich archeologów - sensacyjne znalezisko sprzed 3000 lat",
            "link": "https://www.naukawpolsce.pl/aktualnosci/news,96325,nowe-odkrycie-polskich-archeologow.html",
        },
    ]

    await remove_favorite(ctx, 1)

    # Verify the favorite was removed
    assert len(favorites[str(ctx.author.id)]) == 1
    assert (
        favorites[str(ctx.author.id)][0]["title"]
        == "Nowe odkrycie polskich archeologów - sensacyjne znalezisko sprzed 3000 lat"
    )
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
        {
            "title": "Raport ekonomiczny 2023 - zdrowie polskiej gospodarki",
            "link": "https://www.pap.pl/aktualnosci/raport-ekonomiczny-2023-zdrowie-gospodarki",
        }
    ]

    await remove_favorite(ctx, 2)  # Invalid index

    # Verify error message was sent
    ctx.send.assert_called_once_with(
        "Nieprawidłowy numer wiadomości lub brak ulubionych."
    )
