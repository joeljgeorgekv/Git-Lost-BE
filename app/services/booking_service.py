"""Placeholder booking service.

This module will house the business logic for booking flights, cabs, and hotels.
Do not implement real logic at this stage.
"""

from __future__ import annotations

from typing import List
from app.domain.booking_domain import (
    RoomBookingRequest,
    RoomBookingResponse,
    HotelInfo,
    StayInfo,
    PriceInfo,
    PaymentInfo,
    CabBookingResponse,
    CabBookingRequest,
    FlightBookingRequest,
    FlightBookingResponse,
    HotelSearchItem,
    FlightInfo,
    CabSearchItem,
    VehicleInfo,
    DriverInfo,
    CabTripInfo,
    FareInfo,
)

class BookingService:
    """Service layer abstraction for booking workflows.

    Add methods later to orchestrate bookings across providers.
    """

    def __init__(self) -> None:
        pass

    def book_rooms(self, data: RoomBookingRequest) -> RoomBookingResponse:
        """Echo back booking details strictly from the payload without hardcoded defaults."""
        def _get(key: str):
            return getattr(data, key, None)

        return RoomBookingResponse(
                number_of_rooms=_get("number_of_rooms"),
                booking_id="RM-2025-0001",
                status="confirmed",
            trip_id=_get("trip_id"),
            hotel_id=_get("hotel_id"),
            notes=None,
        )

    def book_cab(self, data: CabBookingRequest) -> CabBookingResponse:
        """Return cab booking response matching current CabBookingResponse model."""
        def _get(key: str):
            if isinstance(data, dict):
                return data.get(key)
            return getattr(data, key, None)

        return CabBookingResponse(
            trip_id=_get("trip_id"),
            registration=_get("registration"),
            pickup_location=_get("pickup_location"),
            drop_location=_get("drop_location"),
            pickup_time=_get("pickup_time"),
            passengers=_get("passengers"),
            cab_type=_get("cab_type"),
        )

    def book_flight(self, data: FlightBookingRequest) -> FlightBookingResponse:
        """Return flight booking response matching current FlightBookingResponse model."""
        def _get(key: str):
            return getattr(data, key, None)

        return FlightBookingResponse(
            booking_id="FL-2025-0789",
            status="confirmed",
            trip_id=_get("trip_id"),
            flight_number=_get("flight_number"),
            notes=None,
            from_airport=_get("from_airport"),
            to_airport=_get("to_airport"),
            depart_time=_get("depart_time"),
            passengers=_get("passengers"),
            cabin_class=_get("cabin_class"),
        )

    def get_hotels(self) -> List[HotelSearchItem]:
        """Return a hardcoded list of hotels for demo/testing."""
        return [
            HotelSearchItem(
                id="H1001",
                name="Seaside Inn",
                location="Goa",
                stars=4.2,
                currency="INR",
                price_per_night=3900.0,
            ),
            HotelSearchItem(
                id="H1002",
                name="Hilltop Retreat",
                location="Manali",
                stars=4.6,
                currency="INR",
                price_per_night=5200.0,
            ),
            HotelSearchItem(
                id="H1003",
                name="City Comfort Hotel",
                location="Bengaluru",
                stars=4.0,
                currency="INR",
                price_per_night=3100.0,
            ),
        ]

    def get_cabs(self) -> List[CabSearchItem]:
        """Return a hardcoded list of cabs for demo/testing."""
        return [
            CabSearchItem(
                type="Sedan",
                model="Toyota Etios",
                capacity=4,
                registration="GA-07-AB-1234",
                driver_name="Akhil",
                rating=4.8,
                currency="INR",
                base_fare=1200.0,
                per_km=18.0,
            ),
            CabSearchItem(
                type="SUV",
                model="Mahindra XUV500",
                capacity=6,
                registration="GA-08-CD-5678",
                driver_name="Rohan",
                rating=4.6,
                currency="INR",
                base_fare=1600.0,
                per_km=22.0,
            ),
            CabSearchItem(
                type="Hatchback",
                model="Maruti Swift",
                capacity=4,
                registration="GA-05-EF-2468",
                driver_name="Neeraj",
                rating=4.4,
                currency="INR",
                base_fare=1000.0,
                per_km=15.0,
            ),
        ]

    def get_flights(self) -> List[FlightInfo]:
        """Return a hardcoded list of flights for demo/testing."""
        return [
            FlightInfo(
                flight_number="AI-202",
                airline="Air India",
                from_airport="DEL",
                to_airport="GOI",
                depart_time="2025-10-10T09:15:00+05:30",
                arrive_time="2025-10-10T11:45:00+05:30",
                duration_min=150,
                currency="INR",
                price_total=7800.0,
                stops=0,
            ),
            FlightInfo(
                flight_number="6E-4512",
                airline="IndiGo",
                from_airport="BLR",
                to_airport="BOM",
                depart_time="2025-10-11T07:30:00+05:30",
                arrive_time="2025-10-11T09:00:00+05:30",
                duration_min=90,
                currency="INR",
                price_total=4200.0,
                stops=0,
            ),
            FlightInfo(
                flight_number="UK-901",
                airline="Vistara",
                from_airport="MAA",
                to_airport="DEL",
                depart_time="2025-10-12T18:20:00+05:30",
                arrive_time="2025-10-12T20:55:00+05:30",
                duration_min=155,
                currency="INR",
                price_total=9100.0,
                stops=0,
            ),
        ]
