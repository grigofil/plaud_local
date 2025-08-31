FROM python:3.11-slim

# нужен ffmpeg для чтения/ресемплинга аудио
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем сервер
COPY server.py .

ENV PYTHONUNBUFFERED=1
# сами задачи монтируются томом ./tasks:/app/tasks (см. compose)

# Запускаем HTTP сервер вместо RQ worker
CMD ["python", "server.py"]
