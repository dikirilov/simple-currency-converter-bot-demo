FROM python:3.11-slim-bullseye AS builder

RUN pip install poetry==1.7.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=1 \
    POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    REQUESTS_TIMEOUT=90

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --with app --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.11-slim-bullseye AS runtime

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN addgroup runner && adduser --ingroup runner runner

COPY --from=builder --chown=runner /app /app

COPY --chown=runner . /app

USER runner

CMD ["/app/.venv/bin/python", "app.py"]