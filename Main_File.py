# Main_File.py
import os
import threading
from datetime import datetime
from liveliness import check_blink

from cam import Camera
from ocr_test import process_document
from face_match import match_faces
from alcohol_sensor import AlcoholSensor
from license_api import verify_license

BASE_DIR = "data/sessions"
alcohol_sensor = None


# ---------------- SESSION ----------------
def create_session():
    session_id = datetime.now().strftime("session_%Y-%m-%d_%H-%M-%S")
    base = os.path.join(BASE_DIR, session_id)
    images = os.path.join(base, "images")

    os.makedirs(images, exist_ok=True)

    return {
        "base": base,
        "license_img": os.path.join(images, "license.jpg"),
        "face_img": os.path.join(images, "user_face.jpg"),
        "ocr_txt": os.path.join(base, "license.txt")
    }


# ---------------- ALCOHOL THREAD ----------------
def start_alcohol_sensor():
    global alcohol_sensor
    alcohol_sensor = AlcoholSensor(channel=0, warmup=True)


# ---------------- MAIN ----------------
def main():
    print("\n🚗 DriveGuard – Optimized Mode\n")

    # 🔥 Start alcohol sensor warm‑up immediately
    alcohol_thread = threading.Thread(target=start_alcohol_sensor)
    alcohol_thread.start()

    # 📂 Session
    session = create_session()

    # 📸 Camera capture
    cam = Camera()
    cam.capture_stable_image(session["face_img"])
    cam.capture_stable_image(session["license_img"])
    cam.close()

    # 🔍 OCR
    license_data = process_document(
        session["license_img"],
        "DRIVING LICENSE",
        session["ocr_txt"]
    )
    ocr_ok = license_data is not None

    print("\n👁️ Performing liveness check (blink)...")
    liveness_ok = check_blink()

    if not liveness_ok:
        print("❌ Liveness check failed (no blink detected)")
        return

    # 🧑‍🦰 Face match
    face_result = match_faces(
        session["license_img"],
        session["face_img"]
    )
    face_ok = face_result["match"]

    # 🌐 License API
    api_ok = verify_license(license_data) if ocr_ok else False

    # ⏳ Ensure alcohol sensor is ready
    alcohol_thread.join()

    detected, value = alcohol_sensor.is_alcohol_detected()
    alcohol_sensor.close()
    alcohol_ok = not detected

    # 🎯 Final decision (ECU‑style AND gate)
    final_decision = (
    ocr_ok
    and liveness_ok
    and face_ok
    and api_ok
    and alcohol_ok
)

    # ---------------- RESULT ----------------
    print("\n========== FINAL RESULT ==========")
    print(f"OCR OK        : {ocr_ok}")
    print(f"Face Match   : {face_ok}")
    print(f"License API  : {api_ok}")
    print(f"Alcohol OK   : {alcohol_ok}")
    print(f"Liveness OK   : {liveness_ok}")
    print("---------------------------------")

    if final_decision:
        print("✅ IGNITION ALLOWED")
    else:
        print("❌ IGNITION BLOCKED")

    print("=================================\n")


if __name__ == "__main__":
    main()
