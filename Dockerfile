FROM python:3.12 AS builder
WORKDIR /src
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /src

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY src/newser.py .

CMD ["python", "newser.py"]