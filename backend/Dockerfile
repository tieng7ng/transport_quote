FROM python:3.12-slim

WORKDIR /app

# Dépendances système
# Dépendances système
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Code source
COPY . .

# Répertoires
RUN mkdir -p uploads configs/partners

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
