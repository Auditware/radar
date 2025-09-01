# Rust builder
FROM --platform=$BUILDPLATFORM python:3.11-slim as rust-builder

# Set up build arguments for cross-compilation
ARG TARGETPLATFORM
ARG BUILDPLATFORM

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
        curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . "$HOME/.cargo/env"

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /api/rust_syn_wrapper

COPY rust_syn_wrapper .
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-dev \
        python3-venv \
        python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
RUN cargo build --release

# Main image
FROM python:3.11-slim

# Set up build arguments for cross-compilation
ARG TARGETPLATFORM
ARG BUILDPLATFORM

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
RUN chmod 644 /api/utils/rust_syn.so

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

ENV DEBUG=${DEBUG} \
    POSTGRES_DB=${POSTGRES_DB} \
    POSTGRES_USER=${POSTGRES_USER} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
    POSTGRES_HOST=${POSTGRES_HOST} \
    POSTGRES_HOST_LOCAL=${POSTGRES_HOST_LOCAL} \
    POSTGRES_PORT=${POSTGRES_PORT} \
    DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME} \
    DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD} \
    SECRET_KEY=${SECRET_KEY} \
    RABBITMQ_USER=${RABBITMQ_USER} \
    RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD} \
    CELERY_BROKER_HOST=${CELERY_BROKER_HOST} \
    CELERY_BROKER_HOST_LOCAL=${CELERY_BROKER_HOST_LOCAL} \
    CELERY_BROKER_PORT=${CELERY_BROKER_PORT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install poetry and dependencies as root
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* /api/
RUN poetry config virtualenvs.create false \
    && poetry config virtualenvs.in-project false \
    && poetry config installer.parallel true \
    && poetry install --no-root --no-ansi \
    && poetry cache clear pypi --all \
    && rm -rf $POETRY_CACHE_DIR

# Copy application files and set ownership
COPY . /api/
RUN chown -R radar:radar /api

# Switch to radar user
USER radar

EXPOSE 8000

CMD ["/api/entrypoint.sh"]