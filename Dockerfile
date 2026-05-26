FROM python:3.11-slim
WORKDIR /app

# Reflex needs Node.js for the bundler; unzip is needed by `reflex init`.
RUN apt-get update && apt-get install -y \
    docker.io \
    fonts-nanum \
    curl \
    unzip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Reflex frontend (3000) + backend (8000)
EXPOSE 3000 8000

WORKDIR /app/aria_app

# Disable Reflex hot-reload — file-change reloads in a mounted-volume setup
# cause worker churn and "worker refused to stop" loops.
ENV REFLEX_HOT_RELOAD=0
ENV REFLEX_USE_GRANIAN=0

CMD ["reflex", "run", "--env", "dev", "--frontend-port", "3000", "--backend-port", "8000", "--loglevel", "info"]
