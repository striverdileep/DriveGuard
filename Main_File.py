import os
import threading
import time
from datetime import datetime
from session_logger import SessionLogger

from cam import Camera
from ocr_test import process_document
from face_match import match_faces
from liveliness import check_liveness

from Hardware.alcohol_sensor import AlcoholSensor
from Hardware.ignition_control import IgnitionController

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
    alcohol_sensor = AlcoholSensor()


# ---------------- MAIN ----------------

def main():
    print("\n🚗 DriveGuard – Full System Mode (DeepFace Backend)\n")

    # Start alcohol sensor
    alcohol_thread = threading.Thread(target=start_alcohol_sensor)
    alcohol_thread.start()

    # Ignition setup
    ignition = IgnitionController()

    try:
        session = create_session()
        logger = SessionLogger(session["base"])

        ocr_ok = False
        face_ok = False
        api_ok = False
        alcohol_ok = False
        liveness_ok = False

        # 📸 CAMERA
        cam = Camera()

        try:
            print("📸 Capturing DRIVER FACE...")
            cam.capture_stable_image(session["face_img"])

            time.sleep(2)

            print("📸 Capturing LICENSE IMAGE...")
            cam.capture_stable_image(session["license_img"])

        except Exception as e:
            print(f"⚠️ Camera error: {e}")
            logger.log_error("camera", e)

            ignition.block_ignition()
            red_on()
            buzzer_on()

            return

        # 👁️ LIVENESS
        try:
            print("\n👁️ Performing liveness check...")
            liveness_ok = check_liveness(session["face_img"])
            logger.log_check("liveness", liveness_ok)
        except Exception as e:
            print(f"⚠️ Liveness error: {e}")
            logger.log_error("liveness", e)
            liveness_ok = False

        cam.close()

        # 🔴 If liveness fails → stop early
        if not liveness_ok:
            print("❌ Liveness failed")

            alcohol_thread.join()
            logger.log_check("alcohol", False, {"skipped": True})

            ignition.block_ignition()
            red_on()
            buzzer_on()

            return

        # 🔍 OCR
        try:
            license_data = process_document(
                session["license_img"],
                "DRIVING LICENSE",
                session["ocr_txt"]
            )

            ocr_ok = license_data is not None
            logger.log_check("ocr", ocr_ok)

            if not ocr_ok:
                print("❌ OCR failed")

        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            logger.log_error("ocr", e)
            ocr_ok = False

        # 🧠 FACE MATCH
        if ocr_ok:
            try:
                print("\n🧠 Performing face match...")

                face_result = match_faces(
                    session["license_img"],
                    session["face_img"]
                )

                face_ok = face_result.get("match", False)

                logger.log_check("face_match", face_ok)

                if not face_ok:
                    print("❌ Face match failed")

            except Exception as e:
                print(f"⚠️ Face match error: {e}")
                logger.log_error("face_match", e)
                face_ok = False

        # 🌐 API
        if ocr_ok and face_ok:
            try:
                api_ok = verify_license(license_data)
                logger.log_check("license_api", api_ok)

                if not api_ok:
                    print("❌ License API failed")

            except Exception as e:
                print(f"⚠️ API error: {e}")
                logger.log_error("license_api", e)
                api_ok = False

        # 🍺 ALCOHOL
        alcohol_thread.join()

        try:
            detected, value = alcohol_sensor.is_alcohol_detected()
            alcohol_ok = not detected

            logger.log_check("alcohol", alcohol_ok)

            if not alcohol_ok:
                print("❌ Alcohol detected")

        except Exception as e:
            print(f"⚠️ Alcohol error: {e}")
            logger.log_error("alcohol", e)
            alcohol_ok = False

        # ✅ FINAL DECISION
        final_decision = (
            liveness_ok and
            ocr_ok and
            face_ok and
            api_ok and
            alcohol_ok
        )

        logger.set_final_decision(final_decision)
        logger.write()

        # 🔥 HARDWARE OUTPUT
        if final_decision:
            ignition.allow_ignition()
            green_on()
            red_on(False)
            print("\n✅ IGNITION ENABLED")
        else:
            ignition.block_ignition()
            red_on()
            green_on(False)
            buzzer_on()
            print("\n❌ IGNITION BLOCKED")

        # 📊 SUMMARY
        print("\n========== SESSION SUMMARY ==========")
        print(f"Liveness OK   : {liveness_ok}")
        print(f"OCR OK        : {ocr_ok}")
        print(f"Face Match    : {face_ok}")
        print(f"License API   : {api_ok}")
        print(f"Alcohol OK    : {alcohol_ok}")
        print("====================================")

    except Exception as e:
        print(f"\n❌ System Error: {e}")
        ignition.block_ignition()
        red_on()
        buzzer_on()

    finally:
        # 🔧 RESET HARDWARE (VERY IMPORTANT)
        try:
            green_on(False)
            red_on(False)
        except:
            pass

        ignition.cleanup()
        print("\n🛑 System shutdown complete")


if __name__ == "__main__":
    main()
