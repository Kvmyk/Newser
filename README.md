![NEWSER-LOGOpng](https://github.com/user-attachments/assets/dc38e2ed-4970-45d8-b8a7-93e7aa7a459a)
# 🤖Newser - Discord News Bot

Bot Discordowy, który pobiera najnowsze wiadomości z [NewsData.io](https://newsdata.io) i umożliwia ich redakcję za pomocą AI (Google Gemini). Użytkownicy mogą także zapisywać ulubione artykuły i przeglądać je później.

---

## 🧩 Funkcje

- `!news <temat>` – Wyszukuje najnowsze wiadomości
- `!news redaguj <temat>` – Redaguje wiadomość za pomocą AI i dodaje link do źródła
- `!news redaguj <numer>` – Redaguje wiadomość z ostatnio wyświetlonych wyników (1–3)
- `!news dodaj <numer>` – Dodaje wskazaną wiadomość do ulubionych
- `!news ulubione` – Wyświetla ulubione wiadomości
- `!news help` – Wyświetla pomoc i instrukcję użycia

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
