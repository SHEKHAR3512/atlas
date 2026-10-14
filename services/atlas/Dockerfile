FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/atlas:/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY services/atlas/requirements.txt /app/services/atlas/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/services/atlas/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "services.atlas.main:app", "--host", "0.0.0.0", "--port", "8000"]
