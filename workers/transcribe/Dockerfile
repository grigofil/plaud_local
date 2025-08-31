FROM python:3.11-slim

# нужен ffmpeg для чтения/ресемплинга аудио
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
# сами задачи монтируются томом ./tasks:/tasks (см. compose)
