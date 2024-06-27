FROM python:3.11-slim

RUN useradd --user-group --system --create-home --no-log-init radar

WORKDIR /api

USER root
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
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    VENV_PATH="/opt/pysetup/.venv" \
    PATH="/root/.cargo/bin:$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
RUN pip install --no-cache-dir poetry
RUN chown -R radar:radar /api

USER radar
COPY pyproject.toml poetry.lock* /api/
RUN poetry install --no-root
RUN poetry run python -m pip list

COPY --chown=radar:radar . /api/

USER root
RUN cd /api/rust_syn_wrapper && \
    cargo build --release && \
    cp /api/rust_syn_wrapper/target/release/librust_syn.so /api/utils/rust_syn.so && \
    chown radar:radar /api/utils/rust_syn.so && \
    chmod 644 /api/utils/rust_syn.so
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

EXPOSE 8000

ENTRYPOINT ["/api/entrypoint.sh"]