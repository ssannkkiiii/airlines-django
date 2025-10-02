FROM python:3.11-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY backend/requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код проекту
COPY backend/ .

# Створюємо директорії для статичних файлів та медіа
RUN mkdir -p staticfiles media

# Встановлюємо змінні середовища
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=conf.settings

# Відкриваємо порт
EXPOSE 8000

# Команда за замовчуванням
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conf.wsgi:application"]
