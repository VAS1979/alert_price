# Dockerfile: контейнеризация FastAPI-приложения alert_price

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main

COPY . .

EXPOSE 8088

CMD ["uvicorn", "alert_price.api.app:app", "--host", "0.0.0.0", "--port", "8088"]
