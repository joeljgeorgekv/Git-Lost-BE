# Trip Planner Service - Backend

A comprehensive travel planning service built with FastAPI, LangGraph, and AI agents for intelligent trip planning.

## Features

### Core Trip Management
- **User Management**: Simple signup/login system for MVP
- **Trip Creation**: Create group trips with user preferences
- **User Collaboration**: Add multiple users to trips with individual preferences

### AI-Powered Travel Planning
- **LangGraph Workflow**: Multi-stage travel planning using LangGraph agents
- **Place Suggestions**: AI-powered destination recommendations based on chat context
- **Trip Overview**: Automatic trip planning with areas and activities
- **Flight Search**: Flight options with pricing and booking links
- **Hotel Search**: Hotel recommendations with amenities and pricing
- **Detailed Itinerary**: Day-by-day itinerary with verified distances and timings

### External API Integration
- **Google Places API**: For destination photos and distance calculations
- **Flight APIs**: Mock implementation ready for real flight search APIs
- **Hotel APIs**: Mock implementation ready for real hotel booking APIs

## Architecture

### Service Layer Pattern
- **Domain Models**: Pydantic models for request/response validation
- **Service Layer**: Business logic separated from routes
- **Agent-Based AI**: Specialized agents for different planning stages
- **LangGraph Orchestration**: Workflow management for complex planning flows

### Technology Stack
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with PostgreSQL
- **LangGraph**: AI workflow orchestration
- **OpenAI**: GPT models for intelligent planning
- **Pydantic**: Data validation and serialization

## API Endpoints

### User Management
- `POST /users/signup` - Create new user account
- `POST /users/login` - User authentication

### Trip Management
- `POST /trips` - Create a new group trip
- `POST /trips/add-user` - Add user to existing trip

### Chat-Based Planning
- `POST /chat/group-plan` - Simple group planning from chat messages
- `GET /chat/health` - Chat service health check

### Advanced Travel Planning
- `POST /travel/plan` - LangGraph-based travel planning workflow
  - Stage: `place_suggestions` - Get destination recommendations
  - Stage: `trip_overview` - Create trip plan with areas
  - Stage: `flights` - Find flight options
  - Stage: `hotels` - Find hotel options
  - Stage: `detailed_itinerary` - Generate detailed day-by-day plan
- `GET /travel/health` - Travel planning service health check

### Health & Monitoring
- `GET /health` - Overall service health check

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- OpenAI API Key
- Google Places API Key (optional)

### Environment Setup
1. Copy `.env.example` to `.env`
2. Configure your API keys and database URL
3. Install dependencies: `pip install -r requirements.txt`

### Database Setup
```bash
# Start PostgreSQL with Docker
docker-compose up -d

# The app will automatically create tables on startup
```

### Running the Service
```bash
# Development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Usage Examples

### 1. Basic Trip Creation
```bash
# Create user
curl -X POST "http://localhost:8000/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password"}'

# Create trip
curl -X POST "http://localhost:8000/trips" \
  -H "Content-Type: application/json" \
  -d '{
    "trip_name": "Bali Adventure",
    "user_id": "user-uuid-here",
    "date_ranges": ["April 15-20, 2025"],
    "preferred_places": ["Ubud", "Seminyak"],
    "budget": 800,
    "preferences": ["Beach", "Culture", "Food"],
    "must_haves": ["WiFi", "Pool"]
  }'
```

### 2. AI-Powered Travel Planning
```bash
# Get place suggestions
curl -X POST "http://localhost:8000/travel/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "We want tropical beaches and good food", "user": "Alice"},
      {"role": "user", "content": "Budget is $800 per person for 5 days", "user": "Bob"}
    ],
    "stage": "place_suggestions",
    "origin_city": "Delhi",
    "budget_range": "mid-range"
  }'

# Create trip overview (after selecting Bali)
curl -X POST "http://localhost:8000/travel/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "We chose Bali!", "user": "Alice"}],
    "stage": "trip_overview",
    "selected_place": "Bali",
    "selected_dates": "April 15-20, 2025",
    "origin_city": "Delhi",
    "budget_range": "mid-range"
  }'
```

## Development

### Project Structure
```
app/
├── clients/          # External API clients
├── core/            # Core utilities (database, config, logging)
├── domain/          # Domain models and types
├── langgraph/       # LangGraph agents and workflows
│   ├── agents/      # Specialized planning agents
│   └── graphs/      # Workflow definitions
├── models/          # SQLAlchemy database models
├── routes/          # FastAPI route handlers
├── schemas/         # Pydantic schemas (legacy)
└── services/        # Business Logic services
```

### Adding New Features
1. Define domain models in `app/domain/`
2. Create service classes in `app/services/`
3. Add route handlers in `app/routes/`
4. Update Postman collection for testing

### Testing
Use the provided Postman collection (`postman/TripPlanner.postman_collection.json`) with the local environment (`postman/Local.postman_environment.json`) for comprehensive API testing.

## Deployment

### Docker Support
```bash
# Build and run with docker-compose
docker-compose up --build
```

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `GOOGLE_PLACES_API_KEY`: Google Places API key (optional)
- `DEBUG`: Enable debug mode (development only)

## Contributing

1. Follow the established service layer pattern
2. Add comprehensive logging using `app.core.logger`
3. Update domain models for new features
4. Maintain backward compatibility in API responses
5. Add Postman requests for new endpoints

## License

This project is part of the Git Lost hackathon submission. It intentionally contains no business logic yet—only a clean, modular structure and a single mock `/health` endpoint.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- LangGraph
- OpenAI
- Pydantic
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