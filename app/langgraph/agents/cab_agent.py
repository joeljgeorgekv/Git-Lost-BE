from __future__ import annotations

from typing import List, Dict, Any

from app.clients.cab_client import CabClient
from app.core.logger import log_info, log_error


class CabAgent:
    """Agent responsible for fetching cab and transfer options (mock)."""

    def __init__(self) -> None:
        self.client = CabClient()

    def find_transfers(self, destination: str, dates: str, passengers: int = 2) -> List[Dict[str, Any]]:
        try:
            data = self.client.search_airport_transfers(destination=destination, dates=dates, passengers=passengers)
            log_info("CabAgent transfers found", destination=destination, count=len(data))
            return data
        except Exception as e:
            log_error("CabAgent transfers error", error=str(e))
            return []

    def find_day_cabs(self, destination: str, dates: str, passengers: int = 2) -> List[Dict[str, Any]]:
        try:
            data = self.client.search_day_cabs(destination=destination, dates=dates, passengers=passengers)
            log_info("CabAgent day cabs found", destination=destination, count=len(data))
            return data
        except Exception as e:
            log_error("CabAgent day cabs error", error=str(e))
            return []
