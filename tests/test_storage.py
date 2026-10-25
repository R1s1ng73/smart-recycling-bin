import json

from smart_bin.identity import parse_rfid_line
from smart_bin.logic import WasteEvent
from smart_bin.storage import LocalEventStore


def test_local_event_store_appends_without_overwriting(tmp_path):
    path = tmp_path / "logs" / "waste_events.jsonl"
    store = LocalEventStore(path)
    store.save(WasteEvent.create("alice", "can"))
    store.save(WasteEvent.create("alice", "battery"))
    events = [json.loads(row) for row in path.read_text().splitlines()]
    assert len(events) == 2
    assert events[0]["item"] == "can"
    assert events[1]["category"] == "Hazardous"


def test_rfid_parsing():
    assert parse_rfid_line("UID: 0123A\n") == "0123A"
    assert parse_rfid_line("Hello") is None
    assert parse_rfid_line("UID: ../secret") is None
