FROM python:3.12 AS builder
WORKDIR /Newser
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /Newser

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Skopiuj cały projekt do kontenera
COPY . .

# Ustaw PYTHONPATH, aby Python widział katalog `src` jako moduł
ENV PYTHONPATH=/Newser/src

# Uruchom aplikację
CMD ["python", "src/newser.py"]