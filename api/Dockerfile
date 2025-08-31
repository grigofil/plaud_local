FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# для удобства отладки оставляем код томом (см. compose)
COPY main.py .

ENV PYTHONUNBUFFERED=1
