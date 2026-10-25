"""Testable, UI-independent waste tracking and classification logic."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Iterable

from smart_bin.config import CLASS_TO_CATEGORY, WASTE_CATEGORIES

# Only accept short, simple identifiers; do not store arbitrary QR content.
_ID_PATTERN = re.compile(r"[A-Za-z0-9_.@-]{1,128}\Z")


def normalise_user_id(value: str) -> str | None:
    candidate = value.strip()
    return candidate if _ID_PATTERN.fullmatch(candidate) else None


def classify_waste(labels: Iterable[str]) -> dict[str, list[str]]:
    found = set(labels)
    return {
        category: sorted(found.intersection(items))
        for category, items in WASTE_CATEGORIES.items()
    }


@dataclass(frozen=True)
class WasteEvent:
    user_id: str
    item: str
    category: str
    amount: int
    timestamp: str

    @classmethod
    def create(cls, user_id: str, item: str) -> "WasteEvent":
        return cls(
            user_id=user_id,
            item=item,
            category=CLASS_TO_CATEGORY[item],
            amount=1,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class DetectionTracker:
    """Count one event per continuously visible item *class* and active user.

    Each class must appear in N consecutive frames to qualify. The class must
    then disappear for M consecutive frames before it can count again. This is
    a prototype counter, not a unique-object tracker for multiple identical items.
    """

    def __init__(
        self, stable_frames: int = 5, reset_frames: int = 3,
        idle_logout_seconds: float = 10.0,
    ) -> None:
        if stable_frames < 1 or reset_frames < 1 or idle_logout_seconds <= 0:
            raise ValueError("Tracker thresholds must be positive")
        self.stable_frames = stable_frames
        self.reset_frames = reset_frames
        self.idle_logout_seconds = idle_logout_seconds
        self.user_id: str | None = None
        self.last_activity: float | None = None
        self._consecutive: dict[str, int] = {}
        self._missing: dict[str, int] = {}
        self._logged: set[str] = set()

    def _clear_counts(self) -> None:
        self._consecutive.clear()
        self._missing.clear()
        self._logged.clear()

    def login(self, value: str, now: float) -> bool:
        """Return True if a valid *new* user has logged in."""
        user = normalise_user_id(value)
        if user is None:
            return False
        changed = user != self.user_id
        if changed:
            self._clear_counts()
        self.user_id = user
        self.last_activity = now
        return changed

    def logout(self) -> None:
        self.user_id = None
        self.last_activity = None
        self._clear_counts()

    def update(self, labels: Iterable[str], now: float) -> list[str]:
        """Return the classes newly confirmed in this frame."""
        if self.user_id is None:
            return []
        if (self.last_activity is not None
                and now - self.last_activity > self.idle_logout_seconds):
            self.logout()
            return []

        visible = set(labels).intersection(CLASS_TO_CATEGORY)
        if visible:
            self.last_activity = now

        # Iterate previously observed labels, too, so absent ones can re-arm.
        tracked = visible | set(self._consecutive) | self._logged
        newly_confirmed: list[str] = []
        for item in sorted(tracked):
            if item in visible:
                self._missing[item] = 0
                self._consecutive[item] = self._consecutive.get(item, 0) + 1
                if self._consecutive[item] >= self.stable_frames and item not in self._logged:
                    self._logged.add(item)
                    newly_confirmed.append(item)
            else:
                self._consecutive[item] = 0
                self._missing[item] = self._missing.get(item, 0) + 1
                if self._missing[item] >= self.reset_frames:
                    self._logged.discard(item)
                    self._consecutive.pop(item, None)
                    self._missing.pop(item, None)
        return newly_confirmed
