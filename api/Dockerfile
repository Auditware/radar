# Rust builder
FROM python:3.12-slim AS rust-builder

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
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --upgrade pip
ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
RUN cargo build --release

# Main image
FROM python:3.12-slim

RUN useradd --user-group --system --create-home --no-log-init radar

WORKDIR /api

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        git \
        build-essential \
        libssl-dev \
        pkg-config \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /api/utils
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
    POETRY_VIRTUALENVS_CREATE=true

# Install poetry and dependencies as root
# Upgrade pip to latest version to address security vulnerability GHSA-4xh5-x5gv-qwph
RUN pip install --no-cache-dir --upgrade pip poetry==1.8.3

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock* /api/
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && rm -rf /api/.venv \
    && poetry install --no-root

RUN pip install solc-select && \
    solc-select install 0.8.20 && \
    solc-select use 0.8.20

RUN curl -L https://foundry.paradigm.xyz | bash && \
    bash -c "source /root/.bashrc && foundryup" && \
    cp /root/.foundry/bin/* /usr/local/bin/ && \
    chmod +x /usr/local/bin/forge /usr/local/bin/cast /usr/local/bin/anvil /usr/local/bin/chisel

# Copy application files in layers for better caching
COPY utils/ /api/utils/
COPY api/ /api/api/
COPY builtin_templates/ /api/builtin_templates/
COPY scripts/ /api/scripts/
COPY manage.py entrypoint.sh /api/

# Set ownership after copying
RUN chown -R radar:radar /api

# Switch to radar user
USER radar

EXPOSE 8000

CMD ["/api/entrypoint.sh"]