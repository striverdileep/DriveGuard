# Main_File.py
import os
import threading
from datetime import datetime
from session_logger import SessionLogger

from cam import Camera
from ocr_test import process_document
from face_match import match_faces
from liveliness import check_blink
from alcohol_sensor import AlcoholSensor
from license_api import verify_license
from ignition_control import IgnitionController

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
    print("\n🚗 DriveGuard – Full System Mode\n")

    # 🔥 Start alcohol sensor warm‑up immediately
    alcohol_thread = threading.Thread(target=start_alcohol_sensor)
    alcohol_thread.start()

    # 🔌 Initialize ignition (FAIL‑SAFE BLOCKED by default)
    ignition = IgnitionController(pin=17)

    try:
        # 📂 Session
        session = create_session()
        logger = SessionLogger(session["base"])
        # 📸 Capture images
        cam = Camera()
        cam.capture_stable_image(session["face_img"])
        cam.capture_stable_image(session["license_img"])
        cam.close()

        # 👁️ Liveness check
        print("\n👁️ Checking liveness...")
        liveness_ok = check_blink()
        logger.log_check("liveness", liveness_ok)
        if not liveness_ok:
            print("❌ Liveness failed")
            ignition.block_ignition()
            return

        # 🔍 OCR
        license_data = process_document(
            session["license_img"],
            "DRIVING LICENSE",
            session["ocr_txt"]
        )
        logger.log_check("ocr", ocr_ok, license_data if ocr_ok else None)
        ocr_ok = license_data is not None

        # 🧑‍🦰 Face match
        face_result = match_faces(
            session["license_img"],
            session["face_img"]
        )
        logger.log_check(
            "face_match",
            face_ok,
            {"distance": face_result.get("distance")}
        )
        face_ok = face_result["match"]

        # 🌐 License API
        api_ok = verify_license(license_data) if ocr_ok else False
        logger.log_check("license_api", api_ok)

        # ⏳ Ensure alcohol sensor ready
        alcohol_thread.join()
        detected, value = alcohol_sensor.is_alcohol_detected()
        alcohol_sensor.close()
        alcohol_ok = not detected
        logger.log_check(
            "alcohol",
            alcohol_ok,
            {"sensor_value": value}
        )


        # 🎯 FINAL DECISION (ECU‑style AND gate)
        final_decision = (
            ocr_ok
            and liveness_ok
            and face_ok
            and api_ok
            and alcohol_ok
        )

        logger.set_final_decision(final_decision)
        logger.write()


        # 🔥 IGNITION CONTROL
        if final_decision:
            ignition.allow_ignition()
            print("\n✅ IGNITION ENABLED")
        else:
            ignition.block_ignition()
            print("\n❌ IGNITION BLOCKED")

        # 📊 Summary
        print("\n========== SESSION SUMMARY ==========")
        print(f"OCR OK        : {ocr_ok}")
        print(f"Liveness OK   : {liveness_ok}")
        print(f"Face Match   : {face_ok}")
        print(f"License API  : {api_ok}")
        print(f"Alcohol OK   : {alcohol_ok}")
        print("====================================")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")

    except Exception as e:
        print(f"\n❌ System Error: {e}")
        ignition.block_ignition()

    finally:
        ignition.cleanup()
        print("\n🛑 System shutdown complete")


if __name__ == "__main__":
    main()
