"""Streamlit dashboard for the Smart Recycling Bin prototype."""

import time
from pathlib import Path

import cv2
import numpy as np
import streamlit as st

from smart_bin.config import load_config
from smart_bin.detection import WasteDetector
from smart_bin.identity import RFIDReader, scan_qr_code
from smart_bin.logic import DetectionTracker, WasteEvent, classify_waste
from smart_bin.storage import FirestoreEventStore, LocalEventStore

st.set_page_config(page_title="Smart Recycling Bin", page_icon="♻️", layout="wide")

config = load_config()


@st.cache_resource(show_spinner="Loading YOLO model…")
def load_detector(model_path: str, confidence: float) -> WasteDetector:
    return WasteDetector(Path(model_path), confidence)


@st.cache_resource(show_spinner=False)
def load_firebase(path: str) -> FirestoreEventStore:
    return FirestoreEventStore(Path(path))


def release_camera() -> None:
    camera = st.session_state.pop("camera", None)
    if camera is not None:
        camera.release()


def release_rfid() -> None:
    reader = st.session_state.pop("rfid_reader", None)
    if reader is not None:
        reader.close()
    st.session_state.pop("rfid_error", None)


def render_categories(labels: set[str]) -> None:
    grouped = classify_waste(labels)
    cols = st.columns(3)
    for col, (category, items) in zip(cols, grouped.items()):
        with col:
            st.markdown(f"**{category}**")
            st.write(", ".join(s.replace("_", " ") for s in items) if items else "—")
    known = {item for group in grouped.values() for item in group}
    unknown = labels - known
    if unknown:
        st.warning("Unmapped model labels: " + ", ".join(sorted(unknown)))


def get_rfid_uid() -> str | None:
    if not config.rfid_port:
        return None
    if "rfid_error" in st.session_state:
        return None
    if "rfid_reader" not in st.session_state:
        try:
            st.session_state.rfid_reader = RFIDReader(config.rfid_port, config.rfid_baudrate)
        except Exception as exc:
            st.session_state.rfid_error = str(exc)
            return None
    try:
        return st.session_state.rfid_reader.read_uid()
    except Exception as exc:
        st.session_state.rfid_error = str(exc)
        st.session_state.rfid_reader.close()
        st.session_state.pop("rfid_reader", None)
        return None


def process_live_frame(frame_bgr: np.ndarray, detector: WasteDetector) -> None:
    qr_user = scan_qr_code(frame_bgr)
    rfid_uid = None if qr_user else get_rfid_uid()
    if qr_user:
        st.session_state.tracker.login(qr_user, time.monotonic())
    elif rfid_uid:
        if cloud_store:
            try:
                rfid_user = cloud_store.lookup_rfid(rfid_uid)
            except Exception as exc:
                st.warning(f"RFID cloud lookup failed: {exc}")
                rfid_user = None
        else:
            # Without cloud mapping, use the UID as the prototype user ID.
            rfid_user = rfid_uid
        if rfid_user:
            st.session_state.tracker.login(rfid_user, time.monotonic())

    prediction = detector.predict(frame_bgr)
    st.image(prediction.annotated_rgb, channels="RGB", use_container_width=True)
    render_categories(prediction.labels)

    newly_confirmed = st.session_state.tracker.update(
        prediction.labels, time.monotonic()
    )
    for item in newly_confirmed:
        user_id = st.session_state.tracker.user_id
        if user_id is None:
            continue
        event = WasteEvent.create(user_id, item)
        try:
            local_store.save(event)
            st.session_state.event_count += 1
            st.session_state.last_event = f"{event.item} recorded for {user_id}"
        except OSError as exc:
            st.error(f"Local event log failed: {exc}")
        if cloud_store:
            try:
                cloud_store.save(event)
            except Exception as exc:
                st.warning(f"Firestore upload failed; check the local event log: {exc}")

    st.caption(
        f"Active user: {st.session_state.tracker.user_id or 'none'}  ·  "
        f"Events logged this session: {st.session_state.event_count}"
    )
    if st.session_state.last_event:
        st.success(st.session_state.last_event)
    if "rfid_error" in st.session_state:
        st.warning("RFID unavailable: " + st.session_state.rfid_error)


# Periodic one-frame reruns let Streamlit's camera toggle interrupt the feed.
@st.fragment(run_every="0.25s")
def live_camera(detector: WasteDetector) -> None:
    cap = st.session_state.get("camera")
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(config.camera_source)
        if not cap.isOpened():
            cap.release()
            st.error("Could not open the camera. Check CAMERA_SOURCE and permissions.")
            return
        st.session_state.camera = cap
    ok, frame = cap.read()
    if not ok:
        release_camera()
        st.error("Could not read a frame from the camera.")
        return
    process_live_frame(frame, detector)


if "tracker" not in st.session_state:
    st.session_state.tracker = DetectionTracker(
        config.stable_frames, config.reset_frames, config.idle_logout_seconds
    )
if "event_count" not in st.session_state:
    st.session_state.event_count = 0
if "last_event" not in st.session_state:
    st.session_state.last_event = None

local_store = LocalEventStore(config.log_path)
cloud_store = None
if config.firebase_credentials:
    try:
        cloud_store = load_firebase(str(config.firebase_credentials))
    except Exception as exc:
        st.warning(f"Firestore disabled: {exc}")

st.title("♻️ Smart Recycling Bin")
st.caption("Vision-based waste detection and tracking · YOLO · OpenCV · Streamlit")
st.info(
    "Portfolio prototype: detects and categorises waste; it does not control "
    "a mechanical sorting mechanism. Classification rules are project-specific."
)

with st.sidebar:
    st.header("Detection console")
    mode = st.radio("Source", ["Upload an image", "Live local webcam"])
    user_id = st.text_input("Manual user ID (optional)", placeholder="e.g. demo_user")
    if st.button("Set active user"):
        if st.session_state.tracker.login(user_id, time.monotonic()):
            st.success("User activated")
        elif st.session_state.tracker.user_id == user_id and user_id:
            st.info("User is already active")
        else:
            st.error("Use 1–128 letters, digits, _, -, . or @")
    if st.button("Log out"):
        st.session_state.tracker.logout()
        st.success("Logged out")
    st.caption("QR identification happens automatically during live detection.")
    st.caption("Cloud: " + ("enabled" if cloud_store else "off (local log only)"))

try:
    detector = load_detector(str(config.model_path), config.confidence)
except Exception as exc:
    st.error(f"Could not load YOLO model: {exc}")
    st.stop()

if mode == "Upload an image":
    release_camera()
    release_rfid()
    st.session_state.run_camera = False
    st.subheader("Try an image")
    st.write("Works without a webcam, RFID reader or Firebase account.")
    uploaded_file = st.file_uploader("Upload JPEG / PNG", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None and st.button("Analyse image", type="primary"):
        image_bytes = np.frombuffer(uploaded_file.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if image is None:
            st.error("Could not decode this image.")
        else:
            try:
                prediction = detector.predict(image)
                st.image(prediction.annotated_rgb, channels="RGB", use_container_width=True)
                render_categories(prediction.labels)
                st.caption("Image mode is a classification demo; it does not log waste events.")
            except Exception as exc:
                st.error(f"Inference failed: {exc}")
else:
    st.subheader("Live webcam detection")
    st.caption("The webcam must be connected to the machine running Streamlit, not the browser.")
    if st.toggle("Start live camera", key="run_camera"):
        try:
            live_camera(detector)
        except Exception as exc:
            release_camera()
            st.error(f"Camera inference failed: {exc}")
    else:
        release_camera()
        release_rfid()
        st.write("Camera is stopped.")
