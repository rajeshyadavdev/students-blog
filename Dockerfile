FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p blog/static/profile_pic

EXPOSE 8000

CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:8000 --workers 3 --worker-class gthread --threads 4 wsgi:app"]
