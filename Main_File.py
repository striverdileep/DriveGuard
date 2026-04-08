# Main_File.py

import os
import threading
import time
from datetime import datetime
import cv2
import base64

from session_logger import SessionLogger

# Hardware
from Hardware.cam import Camera
from Hardware.alcohol_sensor import AlcoholSensor
from Hardware.ignition_control import IgnitionController
from Hardware.ignition_switch import IgnitionSwitch

# AI / API
from ocr.ocr_test import extract_license_number_from_image
from face_match import match_faces
from liveliness import check_liveness as check_blink_from_camera  # Updated to blink-based liveness
from license_api import verify_license

BASE_DIR = "data/sessions"

# ---------- SESSION ----------
def create_session():
    session_id = datetime.now().strftime("session_%Y-%m-%d_%H-%M-%S")
    base = os.path.join(BASE_DIR, session_id)
    images = os.path.join(base, "images")
    os.makedirs(images, exist_ok=True)

    return {
        "base": base,
        "license_img": os.path.join(images, "license.jpg"),
        "face_img": os.path.join(images, "user_face.jpg")
    }

# ---------- ALCOHOL ----------
alcohol_sensor = None

def start_alcohol_sensor(pin=17):
    global alcohol_sensor
    alcohol_sensor = AlcoholSensor(pin=pin, warmup=True)

# ---------- OCR ----------
def run_ocr(path):
    img = cv2.imread(path)
    if img is None:
        print("❌ License image not found")
        return None
    return extract_license_number_from_image(img)

# ---------- LICENSE API ----------
def verify_license_api(license_number):
    api_ok = False
    db_face_bytes = None
    try:
        success, db_face_path_or_blob = verify_license(license_number)
        if not success:
            print("❌ License API failed")
            return api_ok, db_face_bytes

        if isinstance(db_face_path_or_blob, bytes):
            db_face_bytes = db_face_path_or_blob
            api_ok = True
        elif isinstance(db_face_path_or_blob, str):
            if db_face_path_or_blob.startswith("data:image"):
                header, base64_data = db_face_path_or_blob.split(",")
                db_face_bytes = base64.b64decode(base64_data)
                api_ok = True
        else:
            print("⚠️ API returned success but no usable DB face image")
            api_ok = False

        if api_ok:
            print("✅ License API verified and DB face image obtained")
        else:
            print("⚠️ License API returned success but no DB face image")

    except Exception as e:
        print("❌ License API Exception:", e)
        api_ok = False

    return api_ok, db_face_bytes

# ---------- FACE MATCH + LIVENESS ----------
def run_face_and_liveness(db_face_bytes, user_img_path, cam, logger=None):
    # Face match
    try:
        print("\n🧠 Running LOCAL face recognition...")
        face_ok = match_faces(db_face_bytes, user_img_path).get("match", False)
        print(f"Face Match: {face_ok}")
    except Exception as e:
        print("❌ Face match error:", e)
        face_ok = False

    # Liveness via blink detection
    liveness_ok = False
    try:
        print("🟢 Please look at the camera and blink when prompted...")
        liveness_ok = check_blink_from_camera(cam)
        print(f"Liveness : {liveness_ok}")
    except Exception as e:
        print("⚠️ Liveness check error:", e)

    if logger:
        logger.log_check("face_match", face_ok)
        logger.log_check("liveness", liveness_ok)

    return face_ok, liveness_ok

# ---------- ALCOHOL ----------
def check_alcohol(logger=None):
    try:
        detected, value = alcohol_sensor.is_alcohol_detected()
        print("\n🍺 Alcohol Value:", value)
        alcohol_ok = not detected
        if alcohol_ok:
            print("✅ No alcohol detected")
        else:
            print("🚫 Alcohol detected")
    except Exception as e:
        print("⚠️ Alcohol error:", e)
        alcohol_ok = False

    if logger:
        logger.log_check("alcohol", alcohol_ok)

    return alcohol_ok

# ---------- MAIN ----------
def main():
    print("\n🚗 DriveGuard – Integrated Mode\n")

    ignition = IgnitionController(relay_pin=25, buzzer_pin=23, green_led=22, red_led=27)
    switch = IgnitionSwitch(pin=24)

    # Start alcohol sensor in a thread
    t = threading.Thread(target=start_alcohol_sensor)
    t.start()
    print("🔥 Warming alcohol sensor while waiting for button...")

    cam = Camera()

    switch.wait_for_on()

    try:
        session = create_session()
        logger = SessionLogger(session["base"])

        # ---------- FACE ----------
        print("\n📸 Capturing DRIVER FACE...")
        for i in range(6, 0, -1):
            print(f"📷 {i} sec...")
            time.sleep(1)
        cam.capture_stable_image(session["face_img"])

        # ---------- LICENSE ----------
        print("\n📄 Capturing LICENSE...")
        for i in range(6, 0, -1):
            print(f"📄 {i} sec...")
            time.sleep(1)
        cam.capture_stable_image(session["license_img"])

        # ---------- OCR ----------
        print("\n📄 Running OCR...")
        license_number = run_ocr(session["license_img"])
        ocr_ok = license_number is not None
        logger.log_check("ocr", ocr_ok)
        if ocr_ok:
            print("📄 License Number:", license_number)
        else:
            print("❌ OCR FAILED")

        # ---------- LICENSE API ----------
        api_ok = False
        db_face_bytes = None
        if ocr_ok:
            print("\n🌐 Verifying license via API...")
            api_ok, db_face_bytes = verify_license_api(license_number)
        logger.log_check("license_api", api_ok)

        # ---------- FACE + LIVENESS ----------
        face_ok = liveness_ok = False
        if api_ok and db_face_bytes:
            face_ok, liveness_ok = run_face_and_liveness(db_face_bytes, session["face_img"], cam, logger)

        # ---------- ALCOHOL ----------
        t.join()
        alcohol_ok = check_alcohol(logger)

        # ---------- FINAL DECISION ----------
        final = ocr_ok and api_ok and face_ok and liveness_ok and alcohol_ok
        logger.set_final_decision(final)
        logger.write()

        if final:
            ignition.allow_ignition()
            print("\n✅ IGNITION ENABLED")
        else:
            ignition.block_ignition()
            print("\n❌ IGNITION BLOCKED")

        print("\n========== SUMMARY ==========")
        print(f"OCR        : {ocr_ok}")
        print(f"Face Match : {face_ok}")
        print(f"Liveness   : {liveness_ok}")
        print(f"License API: {api_ok}")
        print(f"Alcohol    : {alcohol_ok}")
        print("============================")

    except Exception as e:
        print("\n❌ SYSTEM ERROR:", e)
        ignition.block_ignition()

    finally:
        cam.close()
        ignition.cleanup()
        print("\n🛑 System shutdown complete")


if __name__ == "__main__":
    main()
