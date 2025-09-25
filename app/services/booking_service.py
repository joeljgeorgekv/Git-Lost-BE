"""Placeholder booking service.

This module will house the business logic for booking flights, cabs, and hotels.
Do not implement real logic at this stage.
"""

from __future__ import annotations

from typing import Dict, Any, List
from app.domain.booking_domain import (
    RoomBookingResponse,
    HotelInfo,
    StayInfo,
    PriceInfo,
    PaymentInfo,
    CabBookingResponse,
    CabBookingRequest,
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

    def book_room(self, data: Any) -> RoomBookingResponse:
        """Return a hardcoded room booking response based on optional input data.

        Args:
            data: payload that can be a dict or an object (e.g., Pydantic model) with attributes
                  like hotel_id, check_in, check_out, guests, room_type.
        """
        def _get(key: str):
            if isinstance(data, dict):
                return data.get(key)
            return getattr(data, key, None)

        return RoomBookingResponse(
            booking_id="RM-2025-0001",
            status="confirmed",
            hotel=HotelInfo(
                id=_get("hotel_id") or "H1001",
                name="Seaside Inn",
                address="123 Ocean Drive, Goa",
                room_type=_get("room_type") or "Deluxe",
            ),
            stay=StayInfo(
                check_in=_get("check_in") or "2025-10-10",
                check_out=_get("check_out") or "2025-10-12",
                nights=2,
                guests=_get("guests") or 2,
            ),
            price=PriceInfo(
                currency="INR",
                base=7800,
                taxes=702,
                total=8502,
            ),
            payment=PaymentInfo(
                mode="pay_at_hotel",
                paid=False,
            ),
            notes="This is a mocked booking response for development purposes.",
        )

    def book_cab(self, data: CabBookingRequest) -> CabBookingResponse:
        """Return a hardcoded cab booking response based on optional input data.

        Args:
            data: payload that can be a dict or an object (e.g., Pydantic model) with attributes
                  like pickup_location, drop_location, pickup_time, passengers, cab_type.
        """
        def _get(key: str):
            if isinstance(data, dict):
                return data.get(key)
            return getattr(data, key, None)

        return CabBookingResponse(
            booking_id="CB-2025-0456",
            status="confirmed",
            vehicle=VehicleInfo(
                type=_get("cab_type") or "Sedan",
                model="Toyota Etios",
                registration="GA-07-AB-1234",
            ),
            driver=DriverInfo(
                name="Akhil",
                phone="+91-98765-43210",
                rating=4.8,
            ),
            trip=CabTripInfo(
                pickup_location=_get("pickup_location") or "Dabolim Airport",
                drop_location=_get("drop_location") or "Candolim Beach",
                pickup_time=_get("pickup_time") or "2025-10-10T14:30:00+05:30",
                passengers=_get("passengers") or 2,
                estimated_duration_min=60,
                estimated_distance_km=38.5,
            ),
            fare=FareInfo(
                currency="INR",
                base=1200,
                taxes=108,
                total=1308,
            ),
            notes="This is a mocked cab booking response for development purposes.",
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
