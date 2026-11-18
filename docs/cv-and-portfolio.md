# CV / portfolio description

Use only the aspects you personally implemented. The repository demonstrates
code organization, but the original design project's division of work and
real-world performance could not be verified from the supplied files.

## Project title

**Smart Recycling Bin — Computer Vision & IoT Design Project**

## Short description

Built a prototype waste recognition system using a custom YOLO model and
OpenCV to classify 22 waste object classes into recyclable, non-recyclable,
and hazardous groups. Integrated a Streamlit dashboard, QR/RFID-based user
identification, and optional Firebase Firestore event logging.

## CV bullets (select 2–3)

- Developed a **YOLO/OpenCV-based waste recognition prototype** that maps 22
  object classes into three waste-disposal categories.
- Integrated a **Streamlit detection dashboard** with QR-code identification,
  optional serial RFID input, and user-linked logging to Firebase Firestore.
- Refactored the Python application into modular detection, classification,
  identity and storage components; added configurable settings, event
  de-duplication logic and **10 unit tests**.

## Technology stack

**Python · YOLO (Ultralytics) · OpenCV · Streamlit · Raspberry Pi · UART/RFID · Firebase Firestore · GitHub Actions · pytest**

**Important:** Only list Raspberry Pi, UART/RFID and Firebase as implemented
technologies if they reflect the hardware and services you personally used.
Do not claim a mechanical automatic-sorting system, accuracy percentage,
inference FPS, or production deployment without further evidence.

## Original embedded-hardware context (team project)

The original ModuCycle team design included Arduino-based sensing and actuation, a Raspberry Pi vision system, and CAN bus architecture. The recovered water-bin firmware has MCP2515 CAN-transmission logic configured for 500 kbit/s (CAN IDs 0x036 and 0x0F6), while the main-bin firmware contains ultrasonic/relay and RFID serial logic. See the [hardware documentation](hardware/README.md) and [CAN protocol notes](hardware/can-protocol.md).

**Conservative interview/CV wording:**

- "Contributed to a four-member modular recycling-bin engineering project involving Raspberry Pi vision, Arduino sensor integration and CAN bus design."
- "Examined and documented MCP2515-based CAN status-message transmission in archived Arduino firmware, including two CAN IDs and one-byte water-level status payloads." (Use this only if you actually did the documentation/review yourself.)

Do **not** claim you personally implemented the complete CAN system, a working Pi-side CAN receiver, a validated vehicle CAN network, a deployed NB-IoT service or an autonomous mechanical sorter without more evidence. A project proposal is not an implementation record. Your personal role should match what you can defend in an interview.
