# 🚗 DriveGuard – Intelligent Ignition Control System

DriveGuard is a **multi-factor driver authentication and safety system** designed to **prevent unauthorized or unsafe vehicle ignition**.  
It integrates **computer vision, biometrics, sensor data, and fail-safe hardware control** into a single, session-based pipeline.

This project is designed to run on a **Raspberry Pi** and is suitable for **academic, prototype, and embedded-systems demonstrations**.

---

## 📌 Key Objectives

- Verify driver identity using **Driving License + Face Recognition**
- Prevent spoofing using **Liveness Detection**
- Detect intoxication using an **Alcohol Sensor**
- Make a **fail-safe ignition decision**
- Log every session in a **structured, auditable format**

---

## 📦 Dependencies

### 🐍 Python Version
### 📚 Required Python Libraries

```bash
pip install opencv-python
pip install pytesseract
pip install face_recognition
pip install numpy
pip install scipy
pip install RPi.GPIO
```
### System Dependencies
```bash
sudo apt install tesseract-ocr
sudo apt install libatlas-base-dev
```
## Project Structure
```text
DriveGuard/
│
├── Main_File.py              # System orchestrator (entry point)
├── cam.py                    # Camera capture with SD-card optimization
├── ocr_test.py               # Driving License OCR (frozen)
├── face_match.py             # Face recognition (license vs user)
├── liveness.py               # Blink-based liveness detection
├── alcohol_sensor.py         # Alcohol detection logic
├── ignition_control.py       # GPIO-based ignition relay control
├── session_logger.py         # JSON session logging
├── license_api.py            # External license verification (stub)
│
├── data/
│   └── sessions/
│       └── session_xxx/
│           ├── images/
│           │   ├── license.jpg
│           │   └── user_face.jpg
│           ├── license.txt
│           └── session_result.json
│
└── README.md

```

## Project Flow
``` text
Start Session
   ↓
Initialize Alcohol Sensor (parallel warm-up)
   ↓
Initialize Ignition (BLOCKED by default)
   ↓
Capture User Face Image
Capture License Image
   ↓
Liveness Detection (Blink Check)
   ↓
OCR on License Image
   ↓
Face Match (License vs User)
   ↓
Alcohol Detection Result
   ↓
Final Decision (AND Gate)
   ↓
Ignition Allowed / Blocked
   ↓
Session Logged (JSON)
```

## Optimisation
``` text
⚙️ Optimizations Implemented (Section-wise)
📷 Camera (cam.py)
Uses in-memory warm-up capture (BytesIO)
Avoids unnecessary SD card writes
Improves performance and SD card lifespan

🪪 OCR (ocr_test.py)
Adaptive thresholding for uneven lighting
Fuzzy keyword detection (handles OCR noise)
Sliding-window name extraction
Frozen intentionally (good-enough reliability)

🧑 Face Recognition (face_match.py)
Enforces single-face detection
Uses encoding distance threshold
Prevents accidental false positives

👁️ Liveness Detection (liveness.py)
Blink detection using Eye Aspect Ratio (EAR)
Prevents photo and phone spoofing
Lightweight and headless (Pi-safe)

🍺 Alcohol Sensor
Sensor warm-up runs in a parallel thread
Saves ~10 seconds of user wait time
Result integrated cleanly into final decision

🔥 Ignition Control (ignition_control.py)
GPIO-driven relay control
Fail-safe default: ignition blocked
Ignition enabled only on explicit approval
Safe cleanup on crash or exit
```

## 🔗 How Everything Is Tied Together
Main_File.py acts as the orchestrator:
  - Coordinates all modules
  - Maintains execution order
  - Collects results
  - Makes final decision
  - Controls ignition
  - Triggers logging


## 📊 Logging & Audit Trail
```json
{
  "timestamp": "2026-01-11T18:54:59.412312",
  "checks": {
    "liveness": { "status": true },
    "ocr": {
      "status": true,
      "details": {
        "Name": "RAMESH KUMAR",
        "License_Num": "KA0123456789012",
        "DOB": "12/05/1998"
      }
    },
    "face_match": {
      "status": true,
      "details": { "distance": 0.42 }
    },
    "alcohol": {
      "status": true,
      "details": { "sensor_value": 123 }
    },
    "license_api": { "status": true }
  },
  "final_decision": true
}
```