from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, Tuple, List

import requests


BASE_URL = "http://127.0.0.1:8002"


def _post(path: str, payload: Dict[str, Any]) -> Tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    r = requests.post(url, json=payload, timeout=200)
    try:
        data = r.json() if r.content else {}
    except Exception:
        data = {"raw": r.text}
    return r.status_code, data


def _get(path: str) -> Tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    r = requests.get(url, timeout=20)
    try:
        data = r.json() if r.content else {}
    except Exception:
        data = {"raw": r.text}
    return r.status_code, data


def get_user_id(username: str, password: str) -> str:
    """Ensure the user exists and return their UUID using API-only flow.

    Tries signup first (which returns user_id now). If already exists, uses login to fetch user_id.
    """
    # Try signup
    code, data = _post("/users/signup", {"username": username, "password": password})
    if code in (200, 201) and isinstance(data, dict) and data.get("user_id"):
        user_id = data["user_id"]
        print(f"[users] created {username} (id={user_id})")
        return user_id
    # If already exists, login
    if code == 400 and isinstance(data, dict) and data.get("detail") == "username already exists":
        code2, data2 = _post("/users/login", {"username": username, "password": password})
        if code2 == 200 and isinstance(data2, dict) and data2.get("user_id"):
            print(f"[users] {username} exists; fetched id via login")
            return data2["user_id"]
        raise RuntimeError(f"login failed for existing user {username}: {code2} {data2}")
    raise RuntimeError(f"signup failed for {username}: {code} {data}")


def create_trip(trip_name: str, creator_user_id: str) -> str:
    """Create a trip and return trip_id using creator's UUID."""
    code, data = _post(
        "/trips",
        {
            "trip_name": trip_name,
            "user_id": creator_user_id,
            "date_ranges": ["2025-12-15 to 2025-12-22"],
            "preferences": ["food", "history"],
        },
    )
    if code != 200 or not isinstance(data, dict) or "trip_id" not in data:
        raise RuntimeError(f"create trip failed: {code} {data}")
    trip_id = data["trip_id"]
    print(f"[trips] created '{trip_name}' -> trip_id={trip_id}")
    return trip_id


# remove legacy v2 helper


def list_trips(username: str) -> List[Dict[str, Any]]:
    code, data = _get(f"/trips/by-user/{username}")
    if code == 404:
        print(f"[trips] user {username} not found")
        return []
    if code != 200 or not isinstance(data, dict):
        raise RuntimeError(f"list trips failed: {code} {data}")
    
    # Handle new structured response format
    trips = data.get("trips", [])
    print(f"[trips] {username} trips: {len(trips)}")
    return trips


def add_user_to_trip(trip_id: str, user_id: str) -> None:
    code, data = _post(
        "/trips/add-user",
        {
            "trip_id": trip_id,
            "user_id": user_id,
            "preferences": ["nature"],
        },
    )
    if code != 200:
        raise RuntimeError(f"add user failed: {code} {data}")
    print(f"[trips] added user {user_id} to trip {trip_id}")


def chat(trip_id: str, username: str, message: str) -> None:
    code, data = _post(
        "/chats",
        {
            "trip_id": trip_id,
            "username": username,
            "message": message,
        },
    )
    if code not in (200, 201):
        raise RuntimeError(f"chat failed: {code} {data}")
    print(f"[chats] {username}: {message}")


def list_chats(trip_id: str) -> List[Dict[str, Any]]:
    code, data = _get(f"/chats/{trip_id}")
    if code != 200 or not isinstance(data, list):
        raise RuntimeError(f"list chats failed: {code} {data}")
    return data


def reach_consensus(trip_id: str) -> Dict[str, Any]:
    """Call the reach-consensus endpoint to process NEW messages and get consensus state."""
    code, data = _post(f"/chats/reach-consensus?trip_id={trip_id}", {})
    if code != 200 or not isinstance(data, dict):
        raise RuntimeError(f"reach consensus failed: {code} {data}")
    
    consensus_data = data.get("data", {})
    status = consensus_data.get("status", "unknown")
    
    print(f"[consensus] Status: {status}")
    
    # Print summary if available
    summary = consensus_data.get("summary", {})
    if summary:
        print(f"[consensus] Summary: {json.dumps(summary, indent=2)}")
    
    # Print candidates if available
    candidates = consensus_data.get("candidates", [])
    if candidates:
        print(f"[consensus] Candidates ({len(candidates)}):")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.get('place_name')} - {candidate.get('budget')} - {candidate.get('why_it_matches', [])}")
    
    # Print consensus card if finalized
    consensus_card = consensus_data.get("consensus_card")
    if consensus_card:
        print(f"[consensus] FINALIZED - Consensus Card:")
        print(json.dumps(consensus_card, indent=2))
    
    return consensus_data


def consensus_chat_step(user_message: str, consensus_data: Dict[str, Any], messages: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Call the consensus chat step endpoint to get travel planning options."""
    if messages is None:
        messages = []
    
    payload = {
        "user_message": user_message,
        "messages": messages,
        "consensus": consensus_data,
        "origin_city": kwargs.get("origin_city", "New York"),
        "budget_range": kwargs.get("budget_range", "mid-range"),
        "passengers": kwargs.get("passengers", 2),
        "needs_flight": kwargs.get("needs_flight", True),
        "flights_limit": kwargs.get("flights_limit", 3),
        "flights_offset": kwargs.get("flights_offset", 0),
        "hotels_limit": kwargs.get("hotels_limit", 5),
        "hotels_offset": kwargs.get("hotels_offset", 0),
        "cabs_limit": kwargs.get("cabs_limit", 5),
        "cabs_transfer_offset": kwargs.get("cabs_transfer_offset", 0),
        "cabs_day_offset": kwargs.get("cabs_day_offset", 0)
    }
    
    code, data = _post("/consensus-chat/step", payload)
    if code != 200 or not isinstance(data, dict):
        raise RuntimeError(f"consensus chat step failed: {code} {data}")
    
    print(f"[consensus-chat] User: {user_message}")
    print(f"[consensus-chat] Route taken: {data.get('route_taken', 'unknown')}")
    
    # Print relevant options based on what was returned
    if data.get('flight_options'):
        print(f"[consensus-chat] Found {len(data['flight_options'])} flight options")
        for i, flight in enumerate(data['flight_options'][:2], 1):  # Show first 2
            print(f"  {i}. {flight.get('airline', 'Unknown')} {flight.get('flight_number', '')} - {flight.get('price', 'N/A')}")
    
    if data.get('hotel_options'):
        print(f"[consensus-chat] Found {len(data['hotel_options'])} hotel options")
        for i, hotel in enumerate(data['hotel_options'][:2], 1):  # Show first 2
            print(f"  {i}. {hotel.get('name', 'Unknown')} - {hotel.get('price_per_night', 'N/A')} ({hotel.get('rating', 'N/A')}★)")
    
    if data.get('trip_overview'):
        overview = data['trip_overview']
        print(f"[consensus-chat] Trip Overview: {overview.get('title', 'N/A')}")
        if overview.get('highlights'):
            print(f"  Highlights: {', '.join(overview['highlights'][:3])}")
    
    if data.get('suggestions'):
        print(f"[consensus-chat] Suggestions: {', '.join(data['suggestions'][:2])}")
    
    return data


def test_consensus_flow(trip_id: str) -> None:
    """Test the complete consensus flow with multiple message rounds."""
    print("\n=== Testing Consensus Flow ===")
    
    # Round 1: Initial preferences
    print("\n--- Round 1: Initial Preferences ---")
    chat(trip_id, "alice", "I want to visit Italy from 2025-05-15 to 2025-05-22. Budget around $1500 per person.")
    chat(trip_id, "bob", "I love history and food! Rome sounds amazing.")
    
    # Run consensus
    consensus1 = reach_consensus(trip_id)
    
    # Round 2: More specific preferences
    print("\n--- Round 2: More Specific Preferences ---")
    chat(trip_id, "alice", "I also want to see Florence and maybe some museums.")
    chat(trip_id, "bob", "Barcelona could be nice too, but I prefer Italy for the culture.")
    
    # Run consensus again
    consensus2 = reach_consensus(trip_id)
    
    # Round 3: Narrowing down
    print("\n--- Round 3: Narrowing Down ---")
    chat(trip_id, "alice", "Let's focus on Rome. It has everything we want - history, food, museums.")
    
    # Run consensus final time
    consensus3 = reach_consensus(trip_id)
    
    # Test calling consensus again with no new messages
    print("\n--- Round 4: No New Messages (should return cached state) ---")
    consensus4 = reach_consensus(trip_id)
    
    print(f"\n=== Consensus Flow Complete ===")
    print(f"Final Status: {consensus4.get('status')}")
    
    return consensus4


def test_consensus_chat_flow(consensus_data: Dict[str, Any]) -> None:
    """Test the consensus chat flow for travel planning after consensus is reached."""
    print("\n=== Testing Consensus Chat Flow ===")
    
    # Check if we have a finalized consensus
    if not consensus_data.get('consensus_card'):
        print("⚠️  No finalized consensus found. Need consensus_card for chat flow.")
        return
    
    consensus_card = consensus_data['consensus_card']
    
    # Create consensus payload structure expected by the API
    consensus_payload = {
        "destination": consensus_card.get('destination', 'Rome, Italy'),
        "dates": {
            "start": "2025-05-15",
            "end": "2025-05-22", 
            "display": "May 15-22, 2025"
        },
        "budget": consensus_card.get('budget', 'mid-range'),
        "preferences": consensus_card.get('preferences', []),
        "must_haves": consensus_card.get('must_haves', [])
    }
    
    # Test different chat interactions
    print("\n--- Step 1: Ask for flights ---")
    flight_response = consensus_chat_step(
        "Show me flight options from New York to Rome",
        consensus_payload,
        origin_city="New York",
        passengers=2
    )
    
    print("\n--- Step 2: Ask for hotels ---")
    hotel_response = consensus_chat_step(
        "What hotels are available in Rome?",
        consensus_payload,
        messages=[{"role": "user", "content": "Show me flight options from New York to Rome"}]
    )
    
    print("\n--- Step 3: Ask for itinerary ---")
    itinerary_response = consensus_chat_step(
        "Can you create a detailed itinerary for our Rome trip?",
        consensus_payload,
        messages=[
            {"role": "user", "content": "Show me flight options from New York to Rome"},
            {"role": "user", "content": "What hotels are available in Rome?"}
        ]
    )
    
    print("\n--- Step 4: Ask for transportation ---")
    transport_response = consensus_chat_step(
        "How do we get from the airport to our hotel?",
        consensus_payload
    )
    
    print("\n=== Consensus Chat Flow Complete ===")
    print(f"✅ Tested flight search, hotel search, itinerary, and transportation options")


def main() -> None:
    print("== Trip Planner End-to-End Demo ==")
    print(f"Base URL: {BASE_URL}\n")

    # 1) Ensure users and fetch their UUIDs
    alice_id = get_user_id("alice", "pass123")
    bob_id = get_user_id("bob", "pass123")

    # 2) Create a trip as Alice
    trip_id = create_trip("Italy Adventure", alice_id)

    # 3) List trips for Alice (should include the new one)
    trips_alice = list_trips("alice")
    print(json.dumps(trips_alice, indent=2))

    # 4) Add Bob to the trip
    add_user_to_trip(trip_id, bob_id)

    # 5) Test basic chat functionality
    print("\n=== Basic Chat Test ===")
    chat(trip_id, "alice", "Hey! Shall we target May 15-22 for Italy?")
    time.sleep(0.1)
    chat(trip_id, "bob", "Sounds great! I prefer Rome and Florence.")
    time.sleep(0.1)
    chat(trip_id, "alice", "Awesome. I'll check flights from NYC.")

    # 6) List chats for the trip
    chats = list_chats(trip_id)
    print("\nChats:")
    print(json.dumps(chats, indent=2))

    # 7) Test consensus flow
    final_consensus = test_consensus_flow(trip_id)

    # 8) Test consensus chat flow (if consensus was reached)
    if final_consensus.get('consensus_card'):
        test_consensus_chat_flow(final_consensus)
    else:
        print("\n⚠️  Skipping consensus chat flow - no finalized consensus reached")
        print("   Try adding more specific messages to reach consensus first")

    # 9) List all chats after consensus processing
    print("\n=== Final Chat List (should show SUMMARIZED status) ===")
    final_chats = list_chats(trip_id)
    print(f"Total messages: {len(final_chats)}")

    print("\n=== Demo Complete ===")
    print(f"Trip ID: {trip_id}")
    print(f"Final Consensus Status: {final_consensus.get('status')}")
    if final_consensus.get('consensus_card'):
        print("✅ Consensus reached with finalized travel card!")
        print("✅ Consensus chat flow tested successfully!")
    else:
        print(f"📋 Multiple candidates available: {len(final_consensus.get('candidates', []))}")


def main_consensus_only() -> None:
    """Alternative main function that only tests consensus flow on existing trip."""
    print("== Consensus Flow Test Only ==")
    print(f"Base URL: {BASE_URL}\n")
    
    # Use hardcoded trip ID for quick testing (replace with actual trip ID)
    trip_id = "your-trip-id-here"  # Uncomment and set this for quick testing
    
    print("To test consensus only, uncomment and set trip_id in main_consensus_only()")
    print("Then call main_consensus_only() instead of main()")
    
    test_consensus_flow(trip_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

