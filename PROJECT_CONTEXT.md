# Trip Planner Service - Project Context & AI Assistant Guide

## 🎯 Project Overview
**Git Lost 2025 Hackathon Project**: AI-powered group travel planning service with LangGraph workflow orchestration.

### Core Vision
Transform group travel planning from chaotic chat discussions into structured, AI-guided experiences with:
- Multi-stage planning workflow (Places → Overview → Flights → Hotels → Detailed Itinerary)
- Real-time chat analysis and preference extraction
- External API integration for flights, hotels, and places
- Verified distance calculations and realistic itineraries

## 🏗️ Architecture & Tech Stack

### **Backend Framework**
- **FastAPI** - Modern Python web framework with automatic OpenAPI docs
- **Poetry** - Dependency management (NOT pip/requirements.txt)
- **SQLAlchemy 2.0** - Database ORM with PostgreSQL
- **Pydantic v2** - Data validation and serialization

### **AI & Workflow**
- **LangGraph** - Multi-agent workflow orchestration
- **LangChain ChatOpenAI** - Unified OpenAI integration with structured output
- **OpenAI GPT-4/3.5** - Chat completion and planning intelligence
- **Specialized Agents**: PlaceSuggestion, TripPlanning, Flight, Hotel, Itinerary

### **External APIs**
- **Google Places API** - Photos, place details, distance matrix
- **Flight APIs** - Mock implementation (ready for Amadeus/Skyscanner)
- **Hotel APIs** - Mock implementation (ready for Booking.com/Expedia)

### **Database**
- **PostgreSQL 16** - Primary database
- **Docker Compose** - Local development database

## 📁 Project Structure

```
app/
├── clients/              # External API clients
│   ├── google_places_client.py  # Google Places/Maps integration
│   ├── flight_client.py     # Flight search (mock)
│   └── hotel_client.py      # Hotel search (mock)
├── core/                 # Core utilities
│   ├── config.py            # App configuration
│   ├── database.py          # SQLAlchemy setup
│   └── logger.py            # Simple print-based logging (MVP)
├── domain/               # Domain models (Pydantic)
│   ├── user_domain.py       # User signup/login models
│   ├── trip_domain.py       # Trip creation models
│   ├── chat_domain.py       # Chat planning models
│   └── travel_planning_domain.py  # LangGraph workflow models
├── langgraph/            # LangGraph agents & workflows
│   ├── agents/
│   │   ├── place_suggestion_agent.py
│   │   ├── trip_planning_agent.py
│   │   ├── flight_agent.py
│   │   ├── hotel_agent.py
│   │   └── itinerary_agent.py
│   └── graphs/
│       └── travel_planning_graph.py  # Main workflow
├── models/               # SQLAlchemy database models
│   ├── user.py              # User table
│   ├── trip.py              # Trip table
│   └── trip_user.py         # Many-to-many with preferences
├── routes/               # FastAPI route handlers
│   ├── health.py            # Health checks
│   ├── user_routes.py       # User management
│   ├── trip_routes.py       # Trip CRUD
│   ├── clean_chat_routes.py # Chat-based planning
│   └── travel_planning_routes.py  # LangGraph workflow
├── schemas/              # Legacy Pydantic schemas (being phased out)
└── services/             # Business logic layer
    ├── user_service.py      # User operations
    ├── trip_service.py      # Trip operations
    ├── chat_plan_service.py # Chat analysis + LangGraph
    └── travel_planning_service.py  # LangGraph orchestration
```

## 🔄 LangGraph Workflow States

### **Planning Stages (Enum)**
1. `PLACE_SUGGESTIONS` - AI suggests 3-5 destinations with photos, budgets, best months
2. `TRIP_OVERVIEW` - Creates trip name, areas to explore, day breakdown
3. `FLIGHTS` - Flight options with pricing and booking links
4. `HOTELS` - Hotel recommendations with amenities
5. `DETAILED_ITINERARY` - Day-by-day activities with verified distances

### **State Management**
```python
class TravelPlanningState(TypedDict):
    messages: List[Dict[str, Any]]  # Chat history
    stage: PlanningStage           # Current workflow stage
    selected_place: Optional[str]  # User's destination choice
    selected_dates: Optional[str]  # Trip dates
    origin_city: Optional[str]     # Starting location
    budget_range: str             # "budget"|"mid-range"|"luxury"
    # ... stage outputs (place_suggestions, trip_overview, etc.)
```

## 🛠️ Development Patterns

### **Service Layer Architecture**
- **Routes** → **Services** → **Models/Clients**
- Domain models for request/response validation
- Error handling with ValueError tags mapped to HTTP exceptions
- Simple print-based logging for MVP

### **Database Models**
- `User` - Basic auth (plaintext passwords for hackathon)
- `Trip` - Trip metadata
- `TripUser` - Many-to-many with individual preferences including `date_ranges: list[str]`

### **API Response Patterns**
- Most endpoints return 200 with empty body (MVP simplicity)
- LangGraph endpoints return structured JSON with stage-specific data
- Error responses use standard HTTP status codes

## 🔧 Environment & Setup

### **Required Environment Variables**
```bash
DATABASE_URL=postgresql+psycopg://trip:trip@localhost:5432/tripdb
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here  # Optional
FLIGHT_API_KEY=your_flight_api_key_here                # Future
HOTEL_API_KEY=your_hotel_api_key_here                  # Future
```

### **Development Commands**
```bash
# Install dependencies
poetry install

# Start database
docker-compose up -d

# Run development server
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Database auto-creates tables on startup (init_db())
```

## 🧪 Testing & API Documentation

### **Postman Collection**
- `postman/TripPlanner.postman_collection.json` - Complete API test suite
- `postman/Local.postman_environment.json` - Local development environment
- Covers all workflow stages with realistic payloads

### **Key API Endpoints**
- `POST /travel/plan` - Main LangGraph workflow (stage-based)
- `POST /chat/group-plan` - Simple chat analysis (legacy + LangGraph)
- `POST /trips` - Basic trip creation
- `POST /users/signup` - User registration

## 🚀 Current Status & Next Steps

### **✅ Completed**
- Complete LangGraph workflow with 5 specialized agents
- Service layer refactoring (routes → services → domain)
- LangChain ChatOpenAI integration with structured output
- External API client abstractions
- Comprehensive Postman collection
- Database models with proper relationships
- Simple logging system

### **🔄 In Progress / Future**
- Real external API integrations (currently mocked)
- User authentication beyond basic signup/login
- Database migrations (currently using create_all)
- Unit tests for services and agents
- Production logging and monitoring
- Deployment configuration

### **🎯 Hackathon Priorities**
1. **Frontend Integration** - Ensure API responses match UI expectations
2. **Real API Keys** - Replace mocks with actual flight/hotel APIs
3. **Error Handling** - Robust fallbacks for AI/API failures
4. **Performance** - Optimize LangGraph execution for real-time feel

## 🤖 AI Assistant Guidelines

### **When Working on This Project**
1. **Follow Service Layer Pattern** - Always route → service → domain
2. **Use Domain Models** - Pydantic models in `app/domain/` for new features
3. **Maintain LangGraph State** - Preserve workflow state between stages
4. **Mock External APIs** - Provide realistic fallbacks for development
5. **Simple Logging** - Use `app.core.logger` for print-based logging
6. **Poetry Dependencies** - Never suggest requirements.txt, always use pyproject.toml

### **Code Style Preferences**
- Type hints everywhere (`from __future__ import annotations`)
- Pydantic v2 syntax
- SQLAlchemy 2.0 style
- FastAPI dependency injection
- Descriptive variable names
- Comprehensive error handling

### **Testing Approach**
- Use Postman collection for API testing
- Mock external services in development
- Focus on service layer unit tests
- Integration tests via Postman automation

## 📋 Common Tasks & Solutions

### **Adding New Planning Stage**
1. Add enum to `PlanningStage`
2. Create specialized agent in `app/langgraph/agents/`
3. Add node to `TravelPlanningGraph`
4. Update domain models for new data structures
5. Add Postman requests for testing

### **Integrating Real APIs**
1. Update client classes in `app/clients/`
2. Add API keys to `.env.example`
3. Maintain mock fallbacks for development
4. Update agent classes to use real data

### **Database Changes**
1. Modify models in `app/models/`
2. Consider migration strategy (currently auto-create)
3. Update domain models if API changes needed
4. Test with fresh database

This project represents a sophisticated AI-powered travel planning system built for rapid hackathon development while maintaining production-ready architecture patterns.
