FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p staticfiles media

ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=conf.settings

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conf.wsgi:application"]
