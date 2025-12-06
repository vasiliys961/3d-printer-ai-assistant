# Dockerfile для 3D Printer AI Assistant
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data/chroma /app/data/storage /app/data/temp /app/logs

# Устанавливаем переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose порт для API
EXPOSE 8000

# Команда по умолчанию (можно переопределить в docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

