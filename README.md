![NEWSER-LOGOpng](https://github.com/user-attachments/assets/dc38e2ed-4970-45d8-b8a7-93e7aa7a459a)
# 🤖Newser - Discord News Bot

Bot Discordowy, który pobiera najnowsze wiadomości z [NewsData.io](https://newsdata.io) i umożliwia ich redakcję za pomocą AI (Google Gemini). Użytkownicy mogą także zapisywać ulubione artykuły i przeglądać je później.

---

## 🧩 Funkcje

- `!news <temat>` – Wyszukaj najnowsze wiadomości na dany temat (domyślnie 3 artykuły)
- `!news <temat> [liczba]` – Wyszukaj określoną liczbę wiadomości (1–10) na dany temat
- `!news redaguj <temat>` – Pobierz wiadomości i zredaguj ich treść za pomocą AI
- `!news redaguj <numer>` – Zredaguj wiadomość z ostatnio wyświetlonych wyników
- `!news dodaj <numer>` – Dodaj wskazaną wiadomość z listy do ulubionych
- `!news usun <numer>` – Usuń wskazaną wiadomość z listy ulubionych
- `!news ulubione` – Zobacz swoje zapisane ulubione wiadomości


---

## 🚀 Jak uruchomić

1. **Sklonuj repozytorium**
   ```bash
   git clone https://github.com/Kvmyk/Newser.git
   cd Newser
   ```

2. **Utwórz plik `.env`** w katalogu `newser-bot` z taką zawartością:
   ```env
   DISCORD_TOKEN=twoj_token_z_discorda
   NEWSDATA_API_KEY=twoj_klucz_z_newsdata.io
   GOOGLE_API_KEY=twoj_klucz_z_google_generative_ai
   ```

3. **Zainstaluj zależności**
   ```bash
   pip install -r requirements.txt
   ```

4. **Uruchom bota**
   ```bash
   python newser.py
   ```

---

## 📦 Wymagane zależności

Plik `requirements.txt` powinien zawierać:

```txt
discord.py>=2.3.2
requests>=2.31.0
python-dotenv>=1.0.1
google-generativeai>=0.3.2
anyio
pytest-asyncio
pytest-trio
pytest-twisted

```

---

## 🐳 Uruchomienie w Dockerze

Jeśli chcesz uruchomić projekt w kontenerze Docker, wykonaj poniższe kroki:

1. **Zbuduj obraz Dockera**:
   ```bash
   docker build -t newser-bot .
   ```
2. **Uruchom kontener**:
   ```bash
   docker run --env-file .env -d --name newser-container newser-bot
   ```

---

## 🧠 Wykorzystywane API

- [NewsData.io](https://newsdata.io) – agregator wiadomości z całego świata
- [Google Gemini (Generative AI)](https://makersuite.google.com/app/apikey) – do redagowania wiadomości przez AI

---

## 💾 Informacje o danych

- Dane ulubionych wiadomości i ostatnich wyników są przechowywane tymczasowo w pamięci.
- Po restarcie bota ulubione artykuły znikają.

---

## 🪪 Licencja

MIT © 2025 — Jakub Kamionka
