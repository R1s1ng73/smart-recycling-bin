"""Application settings and model-specific waste taxonomy."""

from dataclasses import dataclass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These strings intentionally match the supplied YOLO checkpoint, including
# its original spellings (e.g. 'plastic_cultery' and 'reuseable_paper').
WASTE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Recyclable": (
        "cardboard_box", "can", "plastic_bottle_cap",
        "plastic_bottle", "reuseable_paper",
    ),
    "Non-recyclable": (
        "plastic_bag", "scrap_paper", "stick", "plastic_cup",
        "snack_bag", "plastic_box", "straw", "plastic_cup_lid",
        "scrap_plastic", "cardboard_bowl", "plastic_cultery",
    ),
    "Hazardous": (
        "battery", "chemical_spray_can", "chemical_plastic_bottle",
        "chemical_plastic_gallon", "light_bulb", "paint_bucket",
    ),
}

CLASS_TO_CATEGORY = {
    item: category
    for category, items in WASTE_CATEGORIES.items()
    for item in items
}


def _source_from_env(value: str) -> int | str:
    return int(value) if value.isdigit() else value


@dataclass(frozen=True)
class AppConfig:
    model_path: Path
    camera_source: int | str
    confidence: float
    stable_frames: int
    reset_frames: int
    idle_logout_seconds: float
    log_path: Path
    firebase_credentials: Path | None
    rfid_port: str | None
    rfid_baudrate: int


def load_config() -> AppConfig:
    """Read configuration from the environment / optional .env file."""
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    model = os.getenv("MODEL_PATH", "weights/best.pt")
    log = os.getenv("EVENT_LOG_PATH", "data/waste_events.jsonl")
    firebase = os.getenv("FIREBASE_CREDENTIALS", "").strip()
    return AppConfig(
        model_path=(ROOT / model).resolve(),
        camera_source=_source_from_env(os.getenv("CAMERA_SOURCE", "0")),
        confidence=float(os.getenv("CONFIDENCE", "0.5")),
        stable_frames=int(os.getenv("STABLE_FRAMES", "5")),
        reset_frames=int(os.getenv("RESET_FRAMES", "3")),
        idle_logout_seconds=float(os.getenv("IDLE_LOGOUT_SECONDS", "10")),
        log_path=(ROOT / log).resolve(),
        firebase_credentials=(ROOT / firebase).resolve() if firebase else None,
        rfid_port=os.getenv("RFID_PORT") or None,
        rfid_baudrate=int(os.getenv("RFID_BAUDRATE", "9600")),
    )
