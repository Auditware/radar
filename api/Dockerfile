# Rust builder
FROM rust:slim as rust-builder

WORKDIR /api/rust_syn_wrapper

COPY rust_syn_wrapper .
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN cargo build --release

# Main image
FROM python:3.11-slim

RUN useradd --user-group --system --create-home --no-log-init radar

WORKDIR /api

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        build-essential \
        libssl-dev \
        pkg-config \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=rust-builder /api/rust_syn_wrapper/target/release/librust_syn.so /api/utils/rust_syn.so
RUN chown -R radar:radar /api && chmod 644 /api/utils/rust_syn.so
COPY --chown=radar:radar . /api/

USER radar

ARG DEBUG 
ARG POSTGRES_DB 
ARG POSTGRES_USER 
ARG POSTGRES_PASSWORD
ARG POSTGRES_HOST
ARG POSTGRES_HOST_LOCAL
ARG POSTGRES_PORT
ARG DJANGO_SUPERUSER_USERNAME
ARG DJANGO_SUPERUSER_PASSWORD
ARG SECRET_KEY
ARG RABBITMQ_USER
ARG RABBITMQ_PASSWORD
ARG CELERY_BROKER_HOST
ARG CELERY_BROKER_HOST_LOCAL
ARG CELERY_BROKER_PORT

ENV DEBUG ${DEBUG}
ENV POSTGRES_DB ${POSTGRES_DB}
ENV POSTGRES_USER ${POSTGRES_USER}
ENV POSTGRES_PASSWORD ${POSTGRES_PASSWORD}
ENV POSTGRES_HOST ${POSTGRES_HOST}
ENV POSTGRES_HOST_LOCAL ${POSTGRES_HOST_LOCAL}
ENV POSTGRES_PORT ${POSTGRES_PORT}
ENV DJANGO_SUPERUSER_USERNAME ${DJANGO_SUPERUSER_USERNAME}
ENV DJANGO_SUPERUSER_PASSWORD ${DJANGO_SUPERUSER_PASSWORD}
ENV SECRET_KEY ${SECRET_KEY}
ENV RABBITMQ_USER ${RABBITMQ_USER}
ENV RABBITMQ_PASSWORD ${RABBITMQ_PASSWORD}
ENV CELERY_BROKER_HOST ${CELERY_BROKER_HOST}
ENV CELERY_BROKER_HOST_LOCAL ${CELERY_BROKER_HOST_LOCAL}
ENV CELERY_BROKER_PORT ${CELERY_BROKER_PORT}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    VENV_PATH="/opt/pysetup/.venv" \
    PATH="/home/radar/.local/bin:$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* /api/
RUN poetry install --no-root

EXPOSE 8000

CMD ["/api/entrypoint.sh"]