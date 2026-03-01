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
This section describes the sequence of operations when the system runs. Below are two perspectives:

### 📝 General (non‑technical) flow
```text
User approaches system
   ↓
Session starts (camera & sensors wake)
   ↓
System captures face + licence images
   ↓
Liveness check (blink detection)
   ↓
Is user seen before?
├─ Yes (face matches one of the cached profiles) → skip OCR & license API
│         perform only liveness & alcohol checks
├─ No  → full validation (OCR, face match, API)
│         if any step fails → abort remaining checks
│         (ignition will be blocked immediately)
│         if all pass → add face encoding to cache
│             (multiple users supported, capped at 50 entries)
   ↓
Alcohol sensor reading
   ↓
Aggregate results → final decision
   ↓
Ignition enabled or blocked
   ↓
Session data written to JSON log
```

### 🔧 Detailed function‑level flow
```text
main()
├─ start_alcohol_sensor()  (thread)
├─ IgnitionController().__init__()  # block by default
├─ session = create_session()
├─ _load_face_cache()
├─ cam = Camera()
│   ├─ capture_stable_image(face_img)
│   └─ capture_stable_image(license_img)
├─ liveness_ok = check_blink_from_frames(cam.get_frame_stream())
├─ cam.close()
├─ if not liveness_ok:
│     final_decision = False  # short-circuit, skip other checks
│     go to summary
├─ current_encoding = load_and_encode(face_img)
├─ if cache_hit:
│     ocr_ok = face_ok = api_ok = True
│     logger.log_check(... cached/ skipped ...)
│   else:
│     license_data = process_document(license_img, ...)
│     ocr_ok = license_data is not None
│     if not ocr_ok: goto summary
│     face_result = match_faces(license_img, face_img)
│     face_ok = face_result.get("match")
│     if not face_ok: goto summary
│     api_ok = verify_license(license_data)
│     if not api_ok: goto summary
│     if ocr_ok and face_ok and api_ok:
│         _save_face_cache(current_encoding)
├─ alcohol_thread.join(); alcohol_ok = not alcohol_sensor.is_alcohol_detected()
├─ final_decision = ocr_ok and liveness_ok and face_ok and api_ok and alcohol_ok
├─ logger.set_final_decision(final_decision); logger.write()
└─ ignition.allow_ignition() or ignition.block_ignition()
```

**Note:** the diagrams above reflect the current cached‑face optimization: repeat visitors bypass OCR and API once their face encoding has been stored.

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

Error handling is pervasive: every stage (camera, OCR, face match, API,
alcohol sensor, GPIO) is wrapped in try/except. Failures do not crash
the app; instead the error is logged via `session_logger.log_error` and
that check is marked as failed (with details). This ensures reliable
operation even if a sensor or library raises an exception.


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