# Trip Planner Backend (Scaffold)

This repository provides a production-ready scaffold for a Python backend powering a group trip-planning application. It intentionally contains no business logic yet—only a clean, modular structure and a single mock `/health` endpoint.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (PostgreSQL-ready; no real queries yet)
- LangGraph (agents/graphs scaffolding only)
- Poetry for dependency management
- pytest, ruff

## Getting Started

### 1) Install Poetry

Follow the official guide: https://python-poetry.org/docs/#installation

### 2) Install Dependencies

```bash
poetry install
```

### 3) Run the FastAPI Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser at http://localhost:8000/health to verify you see:

```json
{ "status": "ok" }
```

Interactive docs: http://localhost:8000/docs

### 4) Run Tests

```bash
poetry run pytest -q
```

## Project Structure

```
.
├── pyproject.toml
├── README.md
├── .gitignore
├── app/
│   ├── main.py                  # FastAPI entry; includes /health router
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Env/config management (pydantic-settings)
│   │   └── database.py          # SQLAlchemy engine/session placeholder
│   ├── models/
│   │   ├── __init__.py          # SQLAlchemy Base
│   │   ├── user.py              # User model (id UUID, username)
│   │   ├── trip.py              # Trip model (id UUID, trip_name)
│   │   └── trip_user.py         # Assoc model and preference JSON placeholders
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py            # /health mock endpoint
│   │   ├── user_routes.py       # Placeholder router (no endpoints yet)
│   │   └── trip_routes.py       # Placeholder router (no endpoints yet)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py      # Placeholder service
│   │   ├── trip_service.py      # Placeholder service
│   │   └── ai_service.py        # Placeholder for LangGraph-based suggestions
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schema.py       # Pydantic stubs
│   │   ├── trip_schema.py       # Pydantic stubs
│   │   └── trip_user_schema.py  # Pydantic stubs
│   ├── clients/
│   │   ├── __init__.py
│   │   └── openai_client.py     # Placeholder for OpenAI integration
│   └── langgraph/
│       ├── __init__.py
│       ├── agents/
│       │   ├── __init__.py
│       │   └── itinerary_agent.py
│       ├── graphs/
│       │   ├── __init__.py
│       │   └── trip_graph.py
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
└── tests/
    ├── __init__.py
    ├── test_health.py           # Tests /health
    └── test_models.py           # Basic model field tests
```

## Configuration

- Managed via `app/core/config.py` using `pydantic-settings`.
- For local development, create a `.env` file (not committed) in repo root:

```env
ENVIRONMENT=development
OPENAI_API_KEY=
# Example for future DB usage:
# DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/tripdb
```

> Note: Auth (JWT/OAuth2) and DB queries are not implemented in this scaffold.

## Folder Overview

- `app/core/` — Shared concerns like configuration and database session stubs.
- `app/models/` — SQLAlchemy models for `User`, `Trip`, and `TripUser` (with JSON placeholders for preferences).
- `app/routes/` — FastAPI routers. Only `/health` is implemented for now.
- `app/services/` — Service layer placeholders for domain logic.
- `app/schemas/` — Pydantic models for request/response shapes.
- `app/clients/` — Placeholder for external API clients (e.g., OpenAI).
- `app/langgraph/` — Agents/graphs utilities for future AI itinerary and booking flows.

## Trip-Planning Flow (High-Level, Future Work)

1. Users create and join trips.
2. Collect group preferences (dates, places, budget, must-haves).
3. Run AI-based suggestions and polls (LangGraph agents).
4. Generate an itinerary and propose bookings (hotels, cabs, flights, trains).

## Notes

- This is a scaffold only. Do not implement booking logic or AI workflows yet.
- Keep modules small and cohesive. Favor dependency injection for testability.

## Roadmap (Next Steps)

- Add request/response models for booking flows
- Implement LangGraph agent and graph nodes
- Integrate OpenAI via `langchain-openai` in the client wrapper
- Add CI (linting, tests) and deployment scripts

## License

MIT (or your preferred license)