import uuid

from app.models.user import User
from app.models.trip import Trip
from app.models.trip_user import TripUser


def test_user_model_fields():
    u = User(id=uuid.uuid4(), username="alice")
    assert isinstance(u.username, str)


def test_trip_model_fields():
    t = Trip(id=uuid.uuid4(), trip_name="Goa Trip")
    assert isinstance(t.trip_name, str)


def test_trip_user_model_fields():
    tu = TripUser(
        user_id=uuid.uuid4(),
        trip_id=uuid.uuid4(),
        preferred_dates=None,
        preferred_places=None,
        budget=None,
        preferences=None,
        must_haves=None,
    )
    assert isinstance(tu.user_id, uuid.UUID)
    assert isinstance(tu.trip_id, uuid.UUID)
