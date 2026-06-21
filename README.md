# Tokyo (preview)

Tokyo is an API-first paper trading and financial data analysis platform for a solo quant
operator. This repository currently implements the first runnable MVP slice:

- versioned Pydantic contracts
- decimal-safe domain primitives
- SQLAlchemy storage schema and Alembic baseline
- FastAPI REST and WebSocket entrypoints
- paper execution, kill switch, risk checks, and daily report services
- Docker Compose, config examples, and focused tests

Run unit and contract tests:

```bash
uv run pytest tests/unit tests/contract
```

Run the local API with Docker Compose:

```bash
cp .env.example .env
# Edit .env and replace the placeholder password and API key first.
docker compose up --build
```

The compose stack binds the API to `127.0.0.1:8000` and keeps PostgreSQL and Redis off
the host network by default. Protected REST routes require either `X-API-Key` or
`Authorization: Bearer <token>` matching `TOKYO_API_KEY`; the health endpoint remains open for
local liveness checks.
