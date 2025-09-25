from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# ---------- Room Booking Models ----------

class RoomBookingRequest(BaseModel):
    number_of_rooms: int
    trip_id: Optional[str] = None
    hotel_id: Optional[str] = None
    check_in: Optional[str] = None  # ISO date string
    check_out: Optional[str] = None  # ISO date string
    guests: Optional[int] = None

class HotelInfo(BaseModel):
    id: str
    name: str
    address: str
    room_type: str


class StayInfo(BaseModel):
    check_in: str  # ISO date string
    check_out: str  # ISO date string
    nights: int
    guests: int


class PriceInfo(BaseModel):
    currency: str
    base: float
    taxes: float
    total: float


class PaymentInfo(BaseModel):
    mode: str
    paid: bool


class RoomBookingResponse(BaseModel):
    number_of_rooms: int
    booking_id: str
    status: str
    trip_id: Optional[str] = None
    hotel_id: str
    notes: Optional[str] = None


# ---------- Cab Booking Models ----------

class CabBookingRequest(BaseModel):
    trip_id: str
    registration: str
    pickup_location: Optional[str] = None
    drop_location: Optional[str] = None
    pickup_time: Optional[str] = None  # ISO datetime string
    passengers: Optional[int] = None
    cab_type: Optional[str] = None


class VehicleInfo(BaseModel):
    type: str
    model: str
    registration: str


class DriverInfo(BaseModel):
    name: str
    phone: str
    rating: float


class CabTripInfo(BaseModel):
    pickup_location: str
    drop_location: str
    pickup_time: str  # ISO datetime string
    passengers: int
    estimated_duration_min: int
    estimated_distance_km: float


class FareInfo(BaseModel):
    currency: str
    base: float
    taxes: float
    total: float


class CabBookingResponse(BaseModel):
    trip_id: str
    registration: str
    pickup_location: Optional[str] = None
    drop_location: Optional[str] = None
    pickup_time: Optional[str] = None  # ISO datetime string
    passengers: Optional[int] = None
    cab_type: Optional[str] = None


# ---------- Search/List Models ----------

class HotelSearchItem(BaseModel):
    id: str
    name: str
    location: str
    stars: float
    currency: str
    price_per_night: float


class FlightInfo(BaseModel):
    flight_number: str
    airline: str
    from_airport: str
    to_airport: str
    depart_time: str  # ISO datetime string
    arrive_time: str  # ISO datetime string
    duration_min: int
    currency: str
    price_total: float
    stops: int


class CabSearchItem(BaseModel):
    type: str           # e.g., Sedan, SUV, Hatchback
    model: str          # e.g., Toyota Etios
    capacity: int       # number of passengers
    registration: str
    driver_name: str
    rating: float
    currency: str
    base_fare: float
    per_km: float


# ---------- Flight Booking Models ----------

class FlightBookingRequest(BaseModel):
    trip_id: Optional[str] = None
    flight_number: str
    from_airport: Optional[str] = None
    to_airport: Optional[str] = None
    depart_time: Optional[str] = None  # ISO datetime string
    passengers: Optional[int] = None
    cabin_class: Optional[str] = None  # e.g., Economy, Business


class FlightBookingResponse(BaseModel):
    booking_id: str
    status: str
    trip_id: Optional[str] = None
    flight_number: str
    notes: Optional[str] = None
    from_airport: Optional[str] = None
    to_airport: Optional[str] = None
    depart_time: Optional[str] = None  # ISO datetime string
    passengers: Optional[int] = None
    cabin_class: Optional[str] = None 
