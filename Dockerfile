FROM python:3.12 AS builder
WORKDIR /Newser
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /Newser

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

ENV PYTHONPATH=/Newser/src

CMD ["python", "src/newser.py"]