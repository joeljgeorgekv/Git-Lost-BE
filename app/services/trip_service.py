from __future__ import annotations

from typing import Optional
import random
from sqlalchemy.orm import Session
from app.models.trip import Trip
from app.models.trip_user import TripUser
from app.models.trip_chat import TripChatMessage
from app.models.user import User
from app.core.logger import log_info, log_error
from app.domain.trip_domain import CreateGroupTripRequest, AddUserToTripRequest, CreateTripResponse, ListTripsResponse, TripSummary


class TripService:
    """Encapsulates trip-related business logic."""

    def __init__(self) -> None:
        # If you later need external services, inject them here
        pass
    
    def create_group_trip(self, db: Session, payload: CreateGroupTripRequest) -> CreateTripResponse:
        # Validate user exists
        user: Optional[User] = db.query(User).filter(User.id == payload.user_id).first()
        if user is None:
            log_error("create trip failed - user not found", user_id=str(payload.user_id))
            raise ValueError("user_not_found")

        # Create trip with unique numeric code (6-8 digits)
        trip_code: str = self._generate_unique_trip_code(db)
        trip = Trip(trip_name=payload.trip_name, trip_code=trip_code)
        db.add(trip)
        # Ensure trip.id is generated before using it in TripUser
        db.flush()

        # Link creator with preferences
        tu = TripUser(
            user_id=payload.user_id,
            trip_id=trip.id,
            date_ranges=payload.date_ranges,
            preferred_places=payload.preferred_places,
            budget=payload.budget,
            preferences=payload.preferences,
            must_haves=payload.must_haves,
        )
        db.add(tu)
        db.commit()
        log_info("trip created", trip_id=str(trip.id), user_id=str(payload.user_id), trip_code=trip.trip_code)
        return CreateTripResponse(trip_id=trip.id, trip_code=trip.trip_code)

    def _generate_unique_trip_code(self, db: Session) -> str:
        """Generate a unique 6-8 digit numeric code for a trip.

        Tries random codes and checks uniqueness in the database. Uses increasing
        length if collisions occur.
        """
        for length in (6, 7, 8):
            for _ in range(100):
                candidate = str(random.randint(10 ** (length - 1), (10 ** length) - 1))
                exists = db.query(Trip).filter(Trip.trip_code == candidate).first() is not None
                if not exists:
                    return candidate
        # As a fallback, append a random suffix to a 8-digit base
        return str(random.randint(10 ** 7, (10 ** 8) - 1))

    def add_user_to_trip(self, db: Session, payload: AddUserToTripRequest) -> None:
        # Validate trip exists
        trip: Optional[Trip] = db.query(Trip).filter(Trip.id == payload.trip_id).first()
        if trip is None:
            log_error("add user to trip failed - trip not found", trip_id=str(payload.trip_id))
            raise ValueError("trip_not_found")

        # Validate user exists
        user: Optional[User] = db.query(User).filter(User.id == payload.user_id).first()
        if user is None:
            log_error("add user to trip failed - user not found", user_id=str(payload.user_id))
            raise ValueError("user_not_found")

        # Upsert TripUser
        tu: Optional[TripUser] = (
            db.query(TripUser)
            .filter(TripUser.trip_id == payload.trip_id, TripUser.user_id == payload.user_id)
            .first()
        )
        if tu is None:
            tu = TripUser(
                user_id=payload.user_id,
                trip_id=payload.trip_id,
                date_ranges=payload.date_ranges,
                preferred_places=payload.preferred_places,
                budget=payload.budget,
                preferences=payload.preferences,
                must_haves=payload.must_haves,
            )
            db.add(tu)
        else:
            tu.date_ranges = payload.date_ranges
            tu.preferred_places = payload.preferred_places
            tu.preferences = payload.preferences
            tu.must_haves = payload.must_haves

        db.commit()
        log_info("user added to trip", trip_id=str(payload.trip_id), user_id=str(payload.user_id))

    def list_trips_for_username(self, db: Session, username: str) -> ListTripsResponse:
        """Return trips for a given username as ListTripsResponse.

        Raises ValueError('user_not_found') if the username does not exist.
        """
        user: Optional[User] = db.query(User).filter(User.username == username).first()
        if user is None:
            log_error("list trips failed - user not found", username=username)
            raise ValueError("user_not_found")

        trips = (
            db.query(Trip)
            .join(TripUser, TripUser.trip_id == Trip.id)
            .filter(TripUser.user_id == user.id)
            .order_by(Trip.trip_name.asc())
            .all()
        )

        trip_summaries = []
        for t in trips:
            last_msg: Optional[TripChatMessage] = (
                db.query(TripChatMessage)
                .filter(TripChatMessage.trip_id == t.id)
                .order_by(TripChatMessage.created_at.desc())
                .first()
            )
            trip_summaries.append(
                TripSummary(
                    id=str(t.id),
                    trip_name=t.trip_name,
                    latest_message=(last_msg.message if last_msg else None),
                    latest_message_at=(last_msg.created_at.isoformat() if last_msg else None),
                )
            )
        return ListTripsResponse(trips=trip_summaries)
