# Refactor notes

This repository starts from four supplied files: `app.py`, `helper.py`,
`settings.py`, and a YOLO checkpoint stored in `best.zip`.

## What was changed

- Reorganized code into **config**, **detection**, **identity**, **logic** and
  **storage** modules to separate concerns and support unit testing.
- Kept the supplied model and all **22 exact class labels**. The original
  misspellings are preserved where required for model compatibility.
- Removed hardcoded `/home/...` service-account paths. Optional Firebase is
  configured through `.env`, and is disabled by default.
- Corrected the original code's **risk of writing event data to the Firebase
  service-account JSON**. Local events are instead appended to a dedicated
  `data/waste_events.jsonl` file.
- Replaced references to undefined serial objects and unprovided `RFID.py`
  with an optional `pyserial` reader and a documented `UID: ...` protocol.
- Replaced the original uninitialized RFID username variable with the actual
  UID (or an optional Firestore lookup under `userid/<UID>`).
- Uses OpenCV for QR decoding, removing the need for the external `zbar` library.
- Uses Firestore Admin SDK consistently through `firebase_admin.firestore`.
- Replaced the original “5 seconds” comment that actually counted **five
  detection frames** with explicit, configurable consecutive-frame counting.
  Adds re-arm logic so a stationary class is not recorded every five frames.
- Removed background threads that manipulated `st.session_state` from outside
  Streamlit's normal execution context.
- Supports uploaded-image demos even with no camera or Firebase setup.
- Added unit tests and GitHub Actions CI for isolated application logic.

## Known constraints / verification needed

- `weights/best.pt` was repackaged **byte-for-byte** from the supplied
  `best.zip` checkpoint. Its ZIP structure and class labels were inspected
  without executing the embedded PyTorch pickle, but inference was **not**
  tested against the original hardware or ML environment.
- Only the Python application and checkpoint were supplied. We cannot verify
  your exact bin electronics, Arduino firmware, data provenance, training
  metrics, project grading, division of work or actual physical sorting.
- One event means a confirmed visible **class**, not a uniquely tracked object.
- QR codes are treated as identifiers, not cryptographic authentication.
- Camera capture runs on the **Streamlit server host**, not through a remote
  browser's webcam.
- Event persistence is best-effort and does not provide an offline sync queue
  or transactional exactly-once guarantee.
