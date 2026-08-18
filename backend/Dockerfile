FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

RUN groupadd --system --gid 10001 docetra \
 && useradd --system --uid 10001 --gid docetra --home-dir /app docetra

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip \
 && pip install ".[test]"

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY tests ./tests
COPY scripts ./scripts

USER docetra
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
