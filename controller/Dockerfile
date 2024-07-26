FROM python:3.11-slim

WORKDIR /radar

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG DJANGO_HOST
ARG DJANGO_HOST_LOCAL
ARG DJANGO_PORT

ENV DJANGO_HOST ${DJANGO_HOST}
ENV DJANGO_HOST_LOCAL ${DJANGO_HOST_LOCAL}
ENV DJANGO_PORT ${DJANGO_PORT}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    VENV_PATH="/opt/pysetup/.venv" \
    PATH="/home/radar/.local/bin:$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* /radar/
RUN poetry install --no-root

COPY . .

ENTRYPOINT ["python", "main.py"]