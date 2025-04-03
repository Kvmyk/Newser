# Stage 1: Builder
FROM python:3.11-slim as builder

# Ustawienie zmiennych środowiskowych dla Pythona
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Utworzenie i ustawienie katalogu roboczego
WORKDIR /app

# Instalacja narzędzi budowania
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Kopiowanie tylko plików potrzebnych do instalacji zależności
COPY pyproject.toml .
COPY poetry.lock* ./ 

# Instalacja zależności
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install

# Stage 2: Runtime
FROM python:3.11-slim

# Ustawienie zmiennych środowiskowych
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Utworzenie i ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie zainstalowanych zależności z buildera
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Kopiowanie kodu aplikacji
COPY src/ ./src/
COPY .env .

# Utworzenie i ustawienie użytkownika bez uprawnień roota
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Uruchomienie aplikacji
CMD ["python", "src/newser.py"]
