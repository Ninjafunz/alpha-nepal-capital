"""Company Timeline and Narrative History Tracker."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.data.store import DataStore


class TimelineManager:
    """Records significant corporate milestones for the public narrative timeline."""

    def __init__(self, store: DataStore):
        self.store = store

    def ensure_genesis_event(self):
        """Ensures the company founding milestone is registered."""
        events = self.store.get_all_timeline_events()
        if not events:
            self.store.record_timeline_event(
                event_date="2026-08-20",
                category="FOUNDATION",
                title="Company Founded with NPR 100M Capital",
                description=(
                    "Alpha Nepal Capital officially established as an AI-Managed Virtual Investment Company. "
                    "Initial capital of NPR 100,000,000 and 10,000,000 virtual shares at NAV NPR 10.00. "
                    "Governing philosophy: ASA-V1.ethics with Level 3 autonomous AI management."
                ),
                nav_at_event=10.0,
                meta={"capital": 100000000.0, "autonomy_level": 3},
            )

    def add_milestone(
        self,
        event_date: str,
        category: str,
        title: str,
        description: str,
        nav_at_event: Optional[float] = None,
        meta: Optional[Dict] = None,
    ):
        self.store.record_timeline_event(
            event_date=event_date,
            category=category,
            title=title,
            description=description,
            nav_at_event=nav_at_event,
            meta=meta,
        )
