"""Local JSONL history and optional Firebase Firestore persistence."""

from dataclasses import asdict
import json
from pathlib import Path

from smart_bin.logic import WasteEvent, normalise_user_id


class LocalEventStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, event: WasteEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


class FirestoreEventStore:
    """Optional Firestore integration, using a separate service account JSON."""

    def __init__(self, credentials_path: Path) -> None:
        if not credentials_path.is_file():
            raise FileNotFoundError(f"Firebase credentials not found: {credentials_path}")
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Reuse the same app in Streamlit reruns.
        try:
            app = firebase_admin.get_app("smart-bin")
        except ValueError:
            app = firebase_admin.initialize_app(
                credentials.Certificate(str(credentials_path)), name="smart-bin"
            )
        self.db = firestore.client(app=app)

    def save(self, event: WasteEvent) -> None:
        # Atomically create/update the parent user document and append the event.
        user_ref = self.db.collection("users").document(event.user_id)
        event_ref = user_ref.collection("events").document()
        batch = self.db.batch()
        batch.set(user_ref, {"name": event.user_id}, merge=True)
        batch.set(event_ref, asdict(event))
        batch.commit()

    def lookup_rfid(self, uid: str) -> str | None:
        # Compatible with the original prototype's userid/{UID}.username schema.
        document = self.db.collection("userid").document(uid).get()
        if not document.exists:
            return None
        user_data = document.to_dict() or {}
        return normalise_user_id(str(user_data.get("username", "")))
