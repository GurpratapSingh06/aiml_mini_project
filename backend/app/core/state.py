"""
VEDANTA — Application State & Startup Lifecycle Tracker
Tracks startup phases, component readiness, and system degradation.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Dict, Any, Optional

class SystemStartupState(str, Enum):
    INITIALIZING = "INITIALIZING"
    RESTORING_KNOWLEDGE = "RESTORING KNOWLEDGE"
    LOADING_SEARCH_INDEX = "LOADING SEARCH INDEX"
    RECOVERING_BACKGROUND_JOBS = "RECOVERING BACKGROUND JOBS"
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"

class ApplicationState:
    def __init__(self):
        self.state: SystemStartupState = SystemStartupState.INITIALIZING
        self.startup_t0: float = time.perf_counter()
        self.ready_t: Optional[float] = None
        self.timings_ms: Dict[str, float] = {}
        self.retrieval_ready: bool = False
        self.db_ready: bool = False
        self.index_details: Dict[str, Any] = {}
        self.errors: list[str] = []

    def set_state(self, state: SystemStartupState, detail: str = "") -> None:
        self.state = state
        elapsed = (time.perf_counter() - self.startup_t0) * 1000
        self.timings_ms[state.value] = round(elapsed, 2)
        if state == SystemStartupState.READY and self.ready_t is None:
            self.ready_t = time.perf_counter()

    def get_summary(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "retrieval_ready": self.retrieval_ready,
            "db_ready": self.db_ready,
            "startup_latency_ms": round((time.perf_counter() - self.startup_t0) * 1000, 2) if not self.ready_t else round((self.ready_t - self.startup_t0) * 1000, 2),
            "timings_ms": self.timings_ms,
            "index_details": self.index_details,
            "errors": self.errors,
        }

# Global singleton application state
app_state = ApplicationState()
