from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# ---------- Room Booking Models ----------

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
    booking_id: str
    status: str
    hotel: HotelInfo
    stay: StayInfo
    price: PriceInfo
    payment: PaymentInfo
    notes: Optional[str] = None


# ---------- Cab Booking Models ----------

class CabBookingRequest(BaseModel):
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
    booking_id: str
    status: str
    vehicle: VehicleInfo
    driver: DriverInfo
    trip: CabTripInfo
    fare: FareInfo
    notes: Optional[str] = None


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
