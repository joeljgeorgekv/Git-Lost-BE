from __future__ import annotations

from typing import Any, Dict

from app.core.logger import log_info
from app.langgraph.graphs.consensus_chat_graph import ConsensusChatGraph, ConsensusChatState


class ConsensusChatService:
    """Service orchestrating the consensus chat graph."""

    def __init__(self) -> None:
        self.graph = ConsensusChatGraph()

    def step(self, state: ConsensusChatState) -> Dict[str, Any]:
        log_info(
            "ConsensusChatService.step",
            destination=state.get("destination"),
            user_message=state.get("user_message"),
        )
        result = self.graph.step(state)
        # sanitize non-serializable keys if any
        result.pop("messages", None)
        return result

