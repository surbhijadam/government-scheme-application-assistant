FROM python:3.12-slim

WORKDIR /app

# System packages PyMySQL's C extensions need to build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Create tables (idempotent - safe if they already exist), then serve with
# gunicorn instead of the Flask dev server, which is not meant for production
# or even "always-on" local use (recall the warning it prints on startup).
CMD ["sh", "-c", "python create_db.py && gunicorn --bind 0.0.0.0:5000 --workers 2 run:app"]