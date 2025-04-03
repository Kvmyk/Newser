import os
import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Załaduj zmienne środowiskowe
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEWSDATA_API_KEY = os.getenv('NEWSDATA_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Konfiguracja Gemini (Google Generative AI)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.0")

# Intencje i prefiks
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Pamięć ulubionych wiadomości (tymczasowo w RAM)
favorites = {}
# Pamięć ostatnich wiadomości na użytkownika
last_articles = {}

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')

@bot.command(name='news')
async def fetch_news(ctx, *, query: str = None):
    if not query:
        await ctx.send("Użycie: `!news <temat>` | `!news <temat> [liczba]` | `!news help` | `!news redaguj` | `!news ulubione` | `!news dodaj <numer>` | `!news readFav` | `!news redaguj <numer>`")
        return

    if query.lower() == "help":
        await ctx.send("""
**Pomoc - Komendy !news:**
`!news <temat>` - Wyszukaj najnowsze wiadomości na dany temat (domyślnie 3 artykuły).
`!news <temat> [liczba]` - Wyszukaj określoną liczbę wiadomości (1-10) na dany temat.
`!news redaguj <temat>` - Pobierz wiadomości i zredaguj ich treść za pomocą AI.
`!news redaguj <numer>` - Zredaguj wiadomość z ostatnio wyświetlonych wyników (1-3).
`!news ulubione` - Zobacz swoje zapisane ulubione wiadomości.
`!news dodaj <numer>` - Dodaj wskazaną wiadomość z listy do ulubionych.
`!news usun <numer>` - Usuń wskazaną wiadomość z listy ulubionych.
""")
        return

    if query.lower().startswith("usun"):
        try:
            index = int(query[len("usun"):].strip())
            await remove_favorite(ctx, index)
        except ValueError:
            await ctx.send("Użycie: `!news usun <numer>`")
        return

    if query.lower().startswith("redaguj"):
        clean_query = query[len("redaguj"):].strip()
        if not clean_query:
            await ctx.send("Użycie: `!news redaguj <temat>` lub `!news redaguj <numer>`")
            return

        if clean_query.isdigit():
            index = int(clean_query)
            user_id = str(ctx.author.id)
            articles = last_articles.get(user_id, [])
            if 1 <= index <= len(articles):
                article = articles[index - 1]
                title = article.get('title', '')
                desc = article.get('description', '')
                prompt = f"Zredaguj tę wiadomość w bardziej przystępny i naturalny sposób:\nTytuł: {title}\nOpis: {desc} \n Wypisz tylko wersję krótką i chwytliwą."
                try:
                    response = model.generate_content(prompt, max_output_tokens=1000, temperature=0.5)
                    await ctx.send(f"🎨 **Zredagowana wersja:**\n{response.text}\n🔗 {article.get('link', '')} \n")

                except Exception as e:
                    await ctx.send(f"Błąd podczas redagowania: {e}")
            else:
                await ctx.send("Nieprawidłowy numer wiadomości do redakcji.")
        else:
            await edit_news(ctx, clean_query)
        return

    if query.lower() == "ulubione":
        user_id = str(ctx.author.id)
        if user_id in favorites and favorites[user_id]:
            for i, fav in enumerate(favorites[user_id], 1):
                await ctx.send(f"{i}. 🔖 **{fav['title']}**\n🔗 {fav['link']}")
        else:
            await ctx.send("Nie masz jeszcze żadnych ulubionych wiadomości.")
        return

    if query.lower().startswith("dodaj"):
        try:
            index = int(query[len("dodaj"):].strip())
            await add_favorite(ctx, index)
        except ValueError:
            await ctx.send("Użycie: `!news dodaj <numer>`")
        return

    await fetch_and_send_news(ctx, query)

async def fetch_and_send_news(ctx, query):
    # Sprawdź czy w zapytaniu jest liczba artykułów
    parts = query.split()
    if len(parts) > 1 and parts[-1].isdigit():
        article_count = min(max(1, int(parts[-1])), 10)  # Ogranicz do zakresu 1-10
        search_query = ' '.join(parts[:-1])
    else:
        article_count = 3  # Domyślna liczba artykułów
        search_query = query

    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={search_query}&language=pl"
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get('results', [])[:article_count]
        if not articles:
            await ctx.send("Brak wyników dla podanego zapytania.")
            return

        for i, article in enumerate(articles):
            title = article.get('title', 'Brak tytułu')
            link = article.get('link', '')
            await ctx.send(f"🔖 **{title}**\n🔗 {link}\nDodaj do ulubionych: `!news dodaj {i+1}`")

        last_articles[str(ctx.author.id)] = articles

    except Exception as e:
        await ctx.send(f"Błąd podczas pobierania danych: {e}")

async def edit_news(ctx, query):
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={query}&language=pl"
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get('results', [])[:1]
        if not articles:
            await ctx.send("Brak wyników do redakcji.")
            return

        title = articles[0].get('title', '')
        desc = articles[0].get('description', '')
        link = articles[0].get('link', '')

        prompt = f"Zredaguj tę wiadomość w bardziej przystępny i naturalny sposób:\nTytuł: {title}\nOpis: {desc} \n Wypisz tylko wersję krótką i chwytliwą."
        response = model.generate_content(prompt, max_tokens=1500, temperature=0.5)
        await ctx.send(f"🎨 **Zredagowana wersja:**\n{response.text}\n🔗 {link}")


    except Exception as e:
        await ctx.send(f"Błąd podczas redakcji: {e}")

@bot.command(name='fav')
async def add_favorite(ctx, index: int):
    user_id = str(ctx.author.id)
    articles = last_articles.get(user_id, [])
    if 0 < index <= len(articles):
        fav = articles[index - 1]
        if user_id not in favorites:
            favorites[user_id] = []
        favorites[user_id].append({
            'title': fav.get('title', 'Brak tytułu'),
            'link': fav.get('link', '')
        })
        await ctx.send(f"Dodano do ulubionych: **{fav.get('title', '')}**")
    else:
        await ctx.send("Nieprawidłowy numer wiadomości.")

async def remove_favorite(ctx, index: int):
    user_id = str(ctx.author.id)
    if user_id in favorites and 0 < index <= len(favorites[user_id]):
        removed_article = favorites[user_id].pop(index - 1)
        await ctx.send(f"Usunięto z ulubionych: **{removed_article.get('title', '')}**")
    else:
        await ctx.send("Nieprawidłowy numer wiadomości lub brak ulubionych.")

# Uruchom bota
bot.run(DISCORD_TOKEN)