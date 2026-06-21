FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md /app/
RUN uv sync --frozen --no-dev --no-install-project

COPY tokyo /app/tokyo
COPY config /app/config
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

RUN useradd --create-home --shell /usr/sbin/nologin tokyo \
    && chown -R tokyo:tokyo /app
USER tokyo

CMD ["uvicorn", "tokyo.apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
