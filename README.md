# Git-Lost-BE
```

has been replaced with the full instructions. Here is the new code document:

```
# Booking Chatbot Service (Backend Scaffold)

This repository provides a production-ready scaffold for a Python backend that will power a chatbot capable of booking flights, cabs, and hotel rooms using OpenAI and LangGraph. It intentionally contains no booking logic yet—only the skeleton and a single mock endpoint for health checks.

## Features

- **FastAPI** application entrypoint
- **LangGraph** structure prepared for agent/graph development
- **Poetry** for dependency management
- **Modern, modular project layout** for team scalability
- **Tests** for the mock health endpoint

## Tech Stack

- **Python** 3.10+
- **FastAPI**
- **LangChain / LangGraph**
- **Poetry**
- **pytest**, **ruff**

## Getting Started

### 1) Install Poetry

Follow the official installation guide: https://python-poetry.org/docs/#installation

### 2) Install Dependencies

```bash
poetry install
```

This will create a virtual environment and install all dependencies.

### 3) Activate Shell (optional)

```bash
poetry shell
```

### 4) Run the FastAPI Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser at http://localhost:8000/health to verify you see:

```json
{ "status": "ok" }
```

Interactive docs are available at http://localhost:8000/docs

### 5) Run Tests

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
│   ├── main.py                 # FastAPI entry point with /health
│   ├── routes/
│   │   ├── __init__.py
│   │   └── booking.py          # Placeholder router (no endpoints yet)
│   ├── services/
│   │   ├── __init__.py
│   │   └── booking_service.py  # Placeholder service
│   ├── clients/
│   │   ├── __init__.py
│   │   └── openai_client.py    # Placeholder OpenAI client
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Env/config via pydantic-settings
│   └── langgraph/
│       ├── __init__.py
│       ├── agents/
│       │   ├── __init__.py
│       │   └── booking_agent.py  # Placeholder agent
│       ├── graphs/
│       │   ├── __init__.py
│       │   └── booking_graph.py  # Placeholder LangGraph workflow
│       └── utils/
│           ├── __init__.py
│           └── helpers.py        # Placeholder utilities
└── tests/
    ├── __init__.py
    └── test_mock.py           # Tests /health endpoint
```

## Configuration

- Configuration is managed in `app/core/config.py` using `pydantic-settings`.
- For local development, you can create a `.env` file (not committed) in the repository root to supply environment variables, for example:

```env
OPENAI_API_KEY=
ENVIRONMENT=development
```

> Note: The code only references `openai_api_key` as a placeholder. Do not implement real client logic yet.

## Development Notes

- Follow a layered approach:
  - **routes/** define HTTP endpoints and request/response models
  - **services/** contain business/domain logic
  - **clients/** wrap external services (OpenAI, etc.)
  - **core/** holds configuration and shared concerns
  - **langgraph/** contains agents, graphs, and related utilities

- Keep modules small and cohesive. Prefer dependency injection for testability.

## Roadmap (Next Steps)

- Add request/response models for booking flows
- Implement LangGraph agent and graph nodes
- Integrate OpenAI via `langchain-openai` in the client wrapper
- Add CI (linting, tests) and deployment scripts

## License

MIT (or your preferred license)