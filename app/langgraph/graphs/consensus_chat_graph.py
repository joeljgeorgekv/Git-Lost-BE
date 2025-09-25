from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from typing_extensions import TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.core.logger import log_info, log_error
from app.langgraph.agents.trip_planning_agent import TripPlanningAgent
from app.langgraph.agents.flight_agent import FlightAgent
from app.langgraph.agents.hotel_agent import HotelAgent
from app.langgraph.agents.itinerary_agent import ItineraryAgent
from app.langgraph.agents.cab_agent import CabAgent
from langchain_openai import ChatOpenAI
from app.core.config import settings


class ConsensusChatState(TypedDict):
    # Chat context
    user_message: str
    messages: Annotated[List[Dict[str, Any]], add_messages]

    # Consensus-derived context
    destination: str
    dates: str
    origin_city: Optional[str]
    budget_range: Optional[str]
    passengers: int

    # Hints / overrides
    needs_flight: Optional[bool]

    # Options & selections
    trip_overview: Optional[Dict[str, Any]]
    flight_options: Optional[List[Dict[str, Any]]]
    hotel_options: Optional[List[Dict[str, Any]]]
    cab_transfer_options: Optional[List[Dict[str, Any]]]
    cab_day_options: Optional[List[Dict[str, Any]]]

    selected_flight: Optional[str]
    selected_hotel: Optional[str]

    # Pagination
    flights_limit: int
    flights_offset: int
    hotels_limit: int
    hotels_offset: int
    cabs_limit: int
    cabs_transfer_offset: int
    cabs_day_offset: int

    # Output helpers
    suggestions: List[str]
    route_taken: Optional[str]


class ConsensusChatGraph:
    """Graph to drive chat after consensus with lightweight intent parsing and safety for gibberish."""

    def __init__(self) -> None:
        self.trip_agent = TripPlanningAgent()
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.itinerary_agent = ItineraryAgent()
        self.cab_agent = CabAgent()
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=settings.openai_api_key)
        self.graph = self._build_graph()

    # ---- Intent helpers ----
    def _classify_intent_llm(self, text: str) -> str:
        """Use OpenAI to classify user intent into a small label set.

        Supported intents:
          - flights, hotels, cabs, itinerary
          - more_flights, more_hotels, more_cabs
          - refresh_flights, refresh_hotels, refresh_cabs
          - skip_flights
          - none (no actionable intent)
        """
        try:
            system = "You are an intent classifier. Return only one label from the allowed set."
            allowed = [
                "flights","hotels","cabs","itinerary",
                "more_flights","more_hotels","more_cabs",
                "refresh_flights","refresh_hotels","refresh_cabs",
                "skip_flights","none"
            ]
            user = (
                "Classify the user's message into one of the labels: "
                + ", ".join(allowed)
                + ". Message: "
                + text
            )
            resp = self.llm.invoke([
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ])
            label = (resp.content or "none").strip().lower()
            return label if label in allowed else "none"
        except Exception:
            return "none"

    def _answer_need_flights_llm(self, origin_city: Optional[str], destination: str) -> str:
        """Answer 'Do I need flights?' with a concise yes/no + one-line reason via LLM."""
        try:
            origin = origin_city or "(unknown origin)"
            prompt = (
                f"User asks if they need flights for a trip. Origin: {origin}. Destination: {destination}.\n"
                "Respond with a concise 'Yes' or 'No' followed by a short reason (one sentence)."
            )
            resp = self.llm.invoke([
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": prompt},
            ])
            return resp.content.strip()
        except Exception:
            # Fallback to heuristic
            if not origin_city:
                return "Likely yes — I don't know your origin city yet."
            if origin_city.strip().lower() == destination.strip().lower():
                return "No — origin and destination appear to be the same city."
            return "Yes — origin and destination differ."

    def _try_answer_travel_question_llm(self, state: Dict[str, Any], text: str) -> Optional[str]:
        """Attempt to answer arbitrary travel-related questions directly.

        Returns a concise answer string if the question is clearly travel-related to the
        current trip context; returns None if not clearly travel-related so the graph
        can continue with intent routing.
        """
        try:
            destination = state.get("destination")
            dates = state.get("dates")
            areas = []  # Not strictly needed; we keep the prompt minimal
            system = (
                "You answer user questions about a specific trip only if they are clearly"
                " travel-related. If the question is not travel-related, output exactly 'NOT_TRAVEL'."
                " Be concise (max 1-2 sentences)."
            )
            user = (
                f"Trip context: destination={destination}; dates={dates}.\n"
                f"Question: {text}\n"
                "Answer the question if it is about travel (flights, hotels, cabs, itinerary, costs, dates, destination)."
            )
            resp = self.llm.invoke([
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ])
            content = (resp.content or "").strip()
            if content.upper() == "NOT_TRAVEL" or content == "":
                return None
            return content
        except Exception:
            return None
    def _is_gibberish(self, text: str) -> bool:
        if not text:
            return False
        # Heuristic: if < 2 alnum tokens and no known keyword → treat as gibberish
        lowered = text.lower()
        keywords = ["flight", "flights", "hotel", "hotels", "cab", "cabs", "transfer", "itinerary", "plan", "show", "more"]
        if any(k in lowered for k in keywords):
            return False
        tokens = [t for t in ''.join(c if c.isalnum() or c.isspace() else ' ' for c in lowered).split() if t]
        return len(tokens) < 2

    def _needs_flight(self, origin_city: Optional[str], destination: str, hint: Optional[bool]) -> bool:
        if hint is not None:
            return hint
        if not origin_city:
            # If we don't know origin, default to offering flights
            return True
        return origin_city.strip().lower() != destination.strip().lower()

    def _build_graph(self) -> StateGraph:
        sg = StateGraph(ConsensusChatState)
        sg.add_node("overview", self._overview)
        sg.add_node("flights", self._flights)
        sg.add_node("hotels", self._hotels)
        sg.add_node("cabs", self._cabs)
        sg.add_node("itinerary", self._itinerary)

        # Entry is overview; the node will route by adding route_taken
        sg.add_edge("overview", END)
        sg.add_edge("flights", END)
        sg.add_edge("hotels", END)
        sg.add_edge("cabs", END)
        sg.add_edge("itinerary", END)
        sg.set_entry_point("overview")
        return sg.compile()

    # ---- Nodes ----
    def _overview(self, state: ConsensusChatState) -> Dict[str, Any]:
        msg = state.get("user_message", "")
        if self._is_gibberish(msg):
            return {
                "suggestions": [
                    "I didn't change anything. Say things like 'show flights', 'show hotels', 'add cabs', or 'create itinerary'."
                ],
                "route_taken": "noop",
            }
        # Always ensure we have a trip overview ready for itinerary
        try:
            if not state.get("trip_overview"):
                overview = self.trip_agent.create_trip_overview(
                    destination=state["destination"],
                    messages=state["messages"],
                    summary=f"Consensus for {state['destination']} on {state.get('dates','')}"
                )
            else:
                overview = state["trip_overview"]
        except Exception as e:
            log_error("ConsensusChat: overview failed", error=str(e))
            return {
                "suggestions": ["Couldn't set up the plan just now. Try again."],
                "route_taken": "error",
            }

        text = msg.lower()
        # First, classify actionable intent to respect commands like 'skip flights'
        intent = self._classify_intent_llm(text)
        if intent in {"flights","more_flights","refresh_flights"}:
            return {"trip_overview": overview, "route_taken": "flights"}
        if intent in {"hotels","more_hotels","refresh_hotels"}:
            return {"trip_overview": overview, "route_taken": "hotels"}
        if intent in {"cabs","more_cabs","refresh_cabs"}:
            return {"trip_overview": overview, "route_taken": "cabs"}
        if intent == "itinerary":
            return {"trip_overview": overview, "route_taken": "itinerary"}
        if intent == "skip_flights":
            return {"trip_overview": overview, "route_taken": "hotels"}

        # If no actionable intent, try answering travel Q&A directly
        # Heuristic: only attempt Q&A for question-like inputs
        question_like = ("?" in text) or any(text.strip().startswith(w) for w in [
            "what", "why", "how", "when", "where", "do ", "does ", "is ", "are ", "can ", "should "
        ])
        if intent == "none" and question_like:
            qa_answer = self._try_answer_travel_question_llm(state, text)
            if qa_answer:
                return {
                    "trip_overview": overview,
                    "suggestions": [qa_answer],
                    "route_taken": "noop",
                }

        # If message not explicit, decide intelligently based on flights need
        if self._needs_flight(state.get("origin_city"), state["destination"], state.get("needs_flight")):
            return {
                "trip_overview": overview,
                "suggestions": [
                    "I'll start with flight options. You can say 'skip flights' to go straight to hotels.",
                ],
                "route_taken": "flights",
            }
        else:
            return {
                "trip_overview": overview,
                "suggestions": [
                    "This trip may not need flights. I'll show hotels next. You can ask for cabs anytime.",
                ],
                "route_taken": "hotels",
            }

    def _flights(self, state: ConsensusChatState) -> Dict[str, Any]:
        try:
            flights = self.flight_agent.find_flights(
                origin_city=state.get("origin_city", ""),
                destination=state["destination"],
                dates=state.get("dates", ""),
                budget_range=state.get("budget_range", "mid-range"),
            )
            limit = int(state.get("flights_limit", 3))
            offset = int(state.get("flights_offset", 0))
            sliced = flights[offset: offset + limit]
            return {
                "flight_options": sliced,
                "suggestions": [
                    "Select a flight, say 'more flights', or 'show hotels'.",
                ],
                "route_taken": "flights",
            }
        except Exception as e:
            log_error("ConsensusChat: flights failed", error=str(e))
            return {
                "suggestions": ["Couldn't fetch flights. Want to see hotels instead?"],
                "route_taken": "flights_error",
            }

    def _hotels(self, state: ConsensusChatState) -> Dict[str, Any]:
        try:
            hotels = self.hotel_agent.find_hotels(
                destination=state["destination"],
                dates=state.get("dates", ""),
                budget_range=state.get("budget_range", "mid-range"),
            )
            limit = int(state.get("hotels_limit", 5))
            offset = int(state.get("hotels_offset", 0))
            sliced = hotels[offset: offset + limit]
            return {
                "hotel_options": sliced,
                "suggestions": [
                    "Pick a hotel to generate itinerary, or say 'add cabs' or 'create itinerary'.",
                ],
                "route_taken": "hotels",
            }
        except Exception as e:
            log_error("ConsensusChat: hotels failed", error=str(e))
            return {"suggestions": ["Couldn't fetch hotels right now."], "route_taken": "hotels_error"}

    def _cabs(self, state: ConsensusChatState) -> Dict[str, Any]:
        try:
            transfers = self.cab_agent.find_transfers(
                destination=state["destination"],
                dates=state.get("dates", ""),
                passengers=state.get("passengers", 2),
            )
            day = self.cab_agent.find_day_cabs(
                destination=state["destination"],
                dates=state.get("dates", ""),
                passengers=state.get("passengers", 2),
            )
            limit = int(state.get("cabs_limit", 5))
            t_off = int(state.get("cabs_transfer_offset", 0))
            d_off = int(state.get("cabs_day_offset", 0))
            return {
                "cab_transfer_options": transfers[t_off: t_off + limit],
                "cab_day_options": day[d_off: d_off + limit],
                "suggestions": [
                    "Choose a transfer/day cab or say 'create itinerary' or 'show hotels'.",
                ],
                "route_taken": "cabs",
            }
        except Exception as e:
            log_error("ConsensusChat: cabs failed", error=str(e))
            return {"suggestions": ["Couldn't fetch cab options."], "route_taken": "cabs_error"}

    def _itinerary(self, state: ConsensusChatState) -> Dict[str, Any]:
        try:
            overview = state.get("trip_overview")
            if not overview:
                # Build if missing
                overview = self.trip_agent.create_trip_overview(
                    destination=state["destination"],
                    messages=state["messages"],
                    summary=f"Consensus for {state['destination']} on {state.get('dates','')}"
                )
            hotel_name = state.get("selected_hotel") or "Selected Hotel"
            detailed = self.itinerary_agent.create_detailed_itinerary(
                trip_overview=overview,
                selected_hotel=hotel_name,
                messages=state["messages"],
            )
            return {
                "detailed_itinerary": detailed,
                "suggestions": ["Your itinerary is ready. You can adjust selections or ask to book items."],
                "route_taken": "itinerary",
            }
        except Exception as e:
            log_error("ConsensusChat: itinerary failed", error=str(e))
            return {"suggestions": ["Couldn't build itinerary this time."], "route_taken": "itinerary_error"}

    # API
    def step(self, init: ConsensusChatState) -> Dict[str, Any]:
        """Run a single step: entry at overview, which chooses a route, then we manually invoke that route node once."""
        try:
            o = self.graph.invoke(init)
            route = o.get("route_taken")
            if route in {None, "noop", "error"}:
                return o
            if route == "flights":
                return {**o, **self._flights({**init, **o})}
            if route == "hotels":
                return {**o, **self._hotels({**init, **o})}
            if route == "cabs":
                return {**o, **self._cabs({**init, **o})}
            if route == "itinerary":
                return {**o, **self._itinerary({**init, **o})}
            return o
        except Exception as e:
            log_error("ConsensusChat: step failed", error=str(e))
            return {"suggestions": ["Sorry, something went wrong."], "route_taken": "error"}
