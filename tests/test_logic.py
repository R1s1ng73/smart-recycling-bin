from smart_bin.config import CLASS_TO_CATEGORY, WASTE_CATEGORIES
from smart_bin.logic import (
    DetectionTracker, WasteEvent, classify_waste, normalise_user_id,
)


def test_every_category_is_unique_and_model_has_22_classes():
    classes = [item for items in WASTE_CATEGORIES.values() for item in items]
    assert len(classes) == len(set(classes)) == 22
    assert CLASS_TO_CATEGORY["battery"] == "Hazardous"
    assert CLASS_TO_CATEGORY["plastic_bottle"] == "Recyclable"


def test_classify_ignores_unknown_labels():
    grouped = classify_waste(["battery", "can", "unseen", "can"])
    assert grouped["Hazardous"] == ["battery"]
    assert grouped["Recyclable"] == ["can"]
    assert grouped["Non-recyclable"] == []


def test_user_id_validation():
    assert normalise_user_id(" demo-1 ") == "demo-1"
    assert normalise_user_id("a/b") is None
    assert normalise_user_id("   ") is None
    assert normalise_user_id("x" * 129) is None


def test_log_only_once_while_item_is_present():
    tracker = DetectionTracker(stable_frames=3, reset_frames=2)
    assert tracker.login("demo", 1.0)
    assert tracker.update(["can"], 1.1) == []
    assert tracker.update(["can"], 1.2) == []
    assert tracker.update(["can"], 1.3) == ["can"]
    assert tracker.update(["can"], 1.4) == []
    assert tracker.update([], 1.5) == []
    assert tracker.update(["can"], 1.6) == []  # brief occlusion
    assert tracker.update([], 1.7) == []
    assert tracker.update([], 1.8) == []
    assert tracker.update(["can"], 1.9) == []
    assert tracker.update(["can"], 2.0) == []
    assert tracker.update(["can"], 2.1) == ["can"]


def test_different_user_resets_counts():
    tracker = DetectionTracker(stable_frames=2)
    tracker.login("first", 0)
    tracker.update(["battery"], 1)
    assert tracker.login("second", 1.1)
    assert tracker.update(["battery"], 1.2) == []
    assert tracker.update(["battery"], 1.3) == ["battery"]


def test_auto_logout_on_inactivity():
    tracker = DetectionTracker(stable_frames=1, idle_logout_seconds=10)
    tracker.login("demo", 1)
    assert tracker.update(["can"], 1.5) == ["can"]
    assert tracker.update([], 12.0) == []
    assert tracker.user_id is None


def test_invalid_user_does_not_log_in():
    tracker = DetectionTracker(stable_frames=1)
    assert not tracker.login("invalid/user", 0)
    assert tracker.update(["can"], 1) == []


def test_event_has_utc_timestamp():
    event = WasteEvent.create("demo", "battery")
    assert event.category == "Hazardous"
    assert event.amount == 1
    assert "+00:00" in event.timestamp
