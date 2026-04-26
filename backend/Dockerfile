FROM python:3.11-slim

WORKDIR /app

# Устанавливаем ВСЕ системные зависимости для psycopg2 и Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libtiff-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install gunicorn==20.1.0
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN mkdir -p /backend_static /media && \
    chmod -R 777 /backend_static /media && \
    chown -R 1000:1000 /backend_static /media

USER 1000:1000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "kittygram_backend.wsgi:application"]