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

## � Getting Started

These instructions walk you from a fresh Ubuntu/Raspbian system to a
running DriveGuard container.

### 1. Clone the repository

```bash
git clone <your-repo-url> DriveGuard
cd DriveGuard
```

### 2. (pi only) enable swap

Raspberry Pi 4 with 4 GB of RAM should have at least 2 GB of swap before
installing TensorFlow-based packages.  On any shell:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# persist across reboot
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 3. Install Docker (optional but recommended)

You can either run the Python code directly using `pip` (see below) or use a
container to isolate dependencies.  To install Docker on Ubuntu/Raspbian:

```bash
sudo apt update
sudo apt install -y docker.io        # or `snap install docker`
sudo usermod -aG docker $USER        # logout/login afterwards
```

If you prefer Podman, `sudo apt install podman-docker` provides a compatible
`docker` CLI.

### 4. Build the container image

```bash
# run on the Pi itself
docker build -t driveguard .
# or from another host, add a platform flag:
# docker buildx build --platform linux/arm/v7 -t driveguard:arm .
```

During the build the Dockerfile installs system libraries, Python packages
(from `requirements.txt`), and even pre-downloads DeepFace model weights.

### 5. Run the application

```bash
docker run --rm -it --privileged \
    --device /dev/vchiq \
    --device /dev/gpiomem \
    --device /dev/spidev0.0 \
    --device /dev/spidev0.1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    driveguard
```

Remove the X11 mount if you don't need GUI windows.  The container will
execute `Main_File.py` automatically.

---

## �📦 Dependencies

### 🐍 Python Version
Python 3.7+

### 📚 Required Python Libraries

We maintain a single `requirements.txt` file for all Python packages; simply run:

```bash
pip install -r requirements.txt
```

That list includes DeepFace and its dependencies (TensorFlow, numpy, pandas, etc.) as
well as OpenCV, pytesseract, RPi.GPIO, spidev, etc.

> On a bare host you must still install the `tesseract-ocr` binary separately
> (`sudo apt install tesseract-ocr`).  The Dockerfile shown below takes care of that
> automatically and even pre-fetches the DeepFace model weights during the build.

### System Dependencies
```bash
sudo apt install tesseract-ocr
sudo apt install libatlas-base-dev
sudo apt install libjasper-dev libharfbuzz0b libwebp6
# Optional: For hardware acceleration
sudo apt install libopenblas-dev libtiff5-dev
```

### 🐳 Containerized Deployment
To avoid dependency conflicts and to make the same environment reproducible on
Ubuntu or Raspberry Pi, we provide a Dockerfile.  Build and run like so:

```bash
# on a Raspberry Pi you should enable swap first (see below), then install
# Docker and run the build:

sudo apt update
sudo apt install -y docker.io        # or podman-docker
sudo usermod -aG docker $USER        # log out and back in afterwards

# build the image; on non‑Pi hosts add --platform if you want an ARM image
docker build -t driveguard .
# cross‑compile example:
# docker buildx build --platform linux/arm/v7 -t driveguard:arm .

# run with hardware access (camera, GPIO, SPI)
docker run --rm -it --privileged \
    --device /dev/vchiq \
    --device /dev/gpiomem \
    --device /dev/spidev0.0 \
    --device /dev/spidev0.1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    driveguard
```

The image installs `tesseract-ocr` and, during the build, executes a short Python
snippet to download DeepFace weights (Facenet, etc.) so that the first container
startup is fast and offline.

---

### 🧠 Raspberry Pi Preparations
Before building on a Pi, take these preparatory steps to ensure a smooth
process:

1. **Enable swap space** (TensorFlow and some Python wheels require more RAM)
   ```bash
   # create a 2 GB swap file if none exists
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   # make persistent across reboots
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

2. **Install Docker** (or Podman) as shown above.  Building the image requires
   an OCI runtime; if you prefer not to use containers you can instead just run
   `pip install -r requirements.txt` in a virtualenv.

3. **Ensure network connectivity** – the build stage downloads ~500 MB of
   DeepFace model files.  A flaky connection will make the build slow or fail.

Once the Pi is prepared you can execute the `docker build` command, and the
final container will start the DriveGuard application with no further
configuration.

### 📌 DeepFace on Raspberry Pi

- **Face Detection**: Uses `yunet` (lightweight, fast on CPU)
- **Face Recognition**: Uses `Facenet` (compact model, suitable for embedded systems)
- **Liveness / Anti-Spoofing**: FasNet detects photo/video spoofing attacks (robust alternative to blink detection)
- **Expected Performance**: 2–10 seconds per face match on Pi 4 (depends on SD card & clock speed)
- **Storage Needed**: ~500MB for model weights (cached after first run)
- **RAM Usage**: 4 GB sufficient; recommend enabling 2 GB swap for stability
## Project Structure
```text
DriveGuard/
│
├── Main_File.py              # System orchestrator (entry point)
├── cam.py                    # Camera capture (PiCamera2)
├── ocr_test.py               # Driving License OCR extraction
├── face_match.py             # Face recognition via DeepFace (yunet + Facenet)
├── liveliness.py             # Anti-spoofing liveness detection via DeepFace FasNet
├── alcohol_sensor.py         # Alcohol sensor reading (ADC via SPI)
├── ignition_control.py       # GPIO-based ignition relay control
├── session_logger.py         # JSON session logging with error capture
├── license_api.py            # License verification API (mock)
│
├── data/
│   └── sessions/
│       └── session_xxx/
│           ├── images/
│           │   ├── license.jpg       # License/ID image
│           │   └── user_face.jpg     # Captured face image
│           ├── license.txt           # OCR raw output
│           └── session_result.json   # Full session log with all checks
│
└── README.md
```

### Module Notes

- **face_match.py**: Uses DeepFace.verify() with yunet face detector and Facenet model; includes built-in anti-spoofing check
- **liveliness.py**: Detects spoofing using DeepFace FasNet (photo/video attack detection), more robust than blink detection
- **Main_File.py**: Simplified orchestration; removed manual face caching (DeepFace handles encoding internally)

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
Liveness check (anti-spoofing: detects photo/video attacks)
   ├─ if spoof detected → block ignition
   └─ if live face → continue
   ↓
Full validation pipeline (early exit on failure):
   ├─ OCR on license → if fails, abort
   ├─ Face match (DeepFace) → if fails, abort
   ├─ License API → if fails, abort
   └─ Alcohol sensor → if detected, block
   ↓
Aggregate all results (AND gate)
   ↓
Ignition enabled or blocked
   ↓
Session data written to JSON log (all checks recorded)
```

### 🔧 Detailed function‑level flow

```text
main()
├─ start_alcohol_sensor()  (thread)
├─ IgnitionController().__init__()  # block by default
├─ session = create_session()
├─ cam = Camera()
│   ├─ capture_stable_image(face_img)
│   └─ capture_stable_image(license_img)
│
├─ liveness_ok = check_liveness(face_img)
│   # DeepFace.represent() with anti_spoofing=True
│   # Returns True if face is real, False if photo/video spoof detected
│
├─ cam.close()
├─ if not liveness_ok:
│     final_decision = False  # short-circuit
│     log remaining checks as skipped & goto summary
│
├─ else:
│   ├─ license_data = process_document(license_img, ...)
│   ├─ ocr_ok = license_data is not None
│   ├─ if not ocr_ok: goto summary
│   │
│   ├─ face_result = match_faces(license_img, face_img)
│   │   # DeepFace.verify() with:
│   │   # - detector_backend="yunet" (fast)
│   │   # - model_name="Facenet" (lightweight)
│   │   # - anti_spoofing=True (built-in check)
│   │
│   ├─ face_ok = face_result.get("match")
│   ├─ if not face_ok: goto summary
│   │
│   ├─ api_ok = verify_license(license_data)
│   ├─ if not api_ok: goto summary
│   │
│   ├─ alcohol_thread.join()
│   ├─ detected, value = alcohol_sensor.is_alcohol_detected()
│   └─ alcohol_ok = not detected
│
├─ final_decision = ocr_ok and liveness_ok and face_ok and api_ok and alcohol_ok
├─ logger.set_final_decision(final_decision)
├─ logger.write()
├─ ignition.allow_ignition() or ignition.block_ignition()
└─ ignition.cleanup()
```

**Note:** Flow is simplified from previous version: removed manual face caching (DeepFace handles encoding internally); liveness now uses anti-spoofing instead of EAR blink detection.

## Optimisations
``` text
⚙️ Optimizations Implemented (Section-wise)

📷 Camera (cam.py)
- PiCamera2 for Raspberry Pi optimisation
- Stable image capture with auto-adjustment delay
- Frame streaming for liveness checks

🪪 OCR (ocr_test.py)
- Adaptive thresholding for uneven lighting
- Fuzzy keyword detection (handles OCR noise)
- Date parsing with multiple format support

🧑 Face Recognition (face_match.py)
- DeepFace with yunet detector (CPU-friendly)
- Facenet model (compact, fast on Pi)
- Built-in anti-spoofing via FasNet
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