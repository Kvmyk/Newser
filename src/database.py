import sqlite3
import os
from datetime import datetime
import pathlib

# Ścieżka do katalogu z bazą danych
DB_DIR = pathlib.Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "newser.db"

# Upewniamy się, że katalog istnieje
DB_DIR.mkdir(exist_ok=True)


def init_db():
    """Inicjalizuje bazę danych i tworzy tabele, jeśli nie istnieją."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tworzenie tabeli ulubionych
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        link TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    conn.commit()
    conn.close()


def add_favorite_db(user_id, title, link):
    """Dodaje ulubiony artykuł do bazy danych."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO favorites (user_id, title, link) VALUES (?, ?, ?)",
        (user_id, title, link),
    )

    conn.commit()
    conn.close()


def get_favorites_db(user_id):
    """Pobiera wszystkie ulubione artykuły użytkownika."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, link FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    results = cursor.fetchall()

    conn.close()

    # Konwertuj wyniki na listę słowników
    favorites = [{"id": row[0], "title": row[1], "link": row[2]} for row in results]
    return favorites


def remove_favorite_db(user_id, favorite_id):
    """Usuwa ulubiony artykuł z bazy danych."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM favorites WHERE id = ? AND user_id = ?", (favorite_id, user_id)
    )
    affected_rows = cursor.rowcount

    conn.commit()
    conn.close()

    return affected_rows > 0  # Zwraca True, jeśli coś zostało usunięte
