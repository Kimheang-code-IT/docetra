FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

RUN groupadd --system --gid 10001 docetra \
 && useradd --system --uid 10001 --gid docetra --home-dir /app docetra

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip \
 && pip install .

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

USER docetra
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
