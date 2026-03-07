# Main_File.py

import os
import threading
from datetime import datetime
import numpy as np

from session_logger import SessionLogger

# Hardware imports
from Hardware.cam import Camera
from Hardware.liveliness import check_blink_from_frames
from Hardware.alcohol_sensor import AlcoholSensor
from Hardware.ignition_control import IgnitionController
from Hardware.ignition_switch import IgnitionSwitch

# AI modules
from ocr_test import process_document
from face_match import match_faces, load_and_encode
from license_api import verify_license


BASE_DIR = "data/sessions"

alcohol_sensor = None

# ---------- FACE CACHE ----------
_face_cache_path = os.path.join(BASE_DIR, "face_cache.npy")
_previous_face_encodings = None


def _load_face_cache():

    global _previous_face_encodings

    try:
        if os.path.exists(_face_cache_path):

            data = np.load(_face_cache_path)

            if data.ndim == 1:
                data = data.reshape(1, -1)

            _previous_face_encodings = data

        else:
            _previous_face_encodings = None

    except Exception:
        _previous_face_encodings = None


def _save_face_cache(enc, max_entries=50, distance_threshold=0.6):

    global _previous_face_encodings

    try:

        if _previous_face_encodings is None:
            arr = np.array([enc])

        else:

            dists = np.linalg.norm(_previous_face_encodings - enc, axis=1)

            if np.any(dists <= distance_threshold):
                return

            arr = np.vstack([_previous_face_encodings, enc])

        if arr.shape[0] > max_entries:
            arr = arr[-max_entries:]

        os.makedirs(BASE_DIR, exist_ok=True)

        np.save(_face_cache_path, arr)

        _previous_face_encodings = arr

    except Exception as e:
        print("⚠️ Face cache save error:", e)


# ---------- SESSION ----------
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


# ---------- ALCOHOL SENSOR THREAD ----------
def start_alcohol_sensor():

    global alcohol_sensor

    # Updated: MQ3 connected to MCP3208 CH0
    alcohol_sensor = AlcoholSensor(channel=0, warmup=True)


# ---------- MAIN ----------
def main():

    print("\n🚗 DriveGuard – Full System Mode\n")

    # ignition controller (LED + buzzer + relay)
    ignition = IgnitionController(
        relay_pin=25,
        buzzer_pin=23,
        green_led=22,
        red_led=27
    )

    # ignition switch button
    switch = IgnitionSwitch(pin=24)

    # wait for button press
    switch.wait_for_on()

    # start alcohol sensor warmup
    alcohol_thread = threading.Thread(target=start_alcohol_sensor)
    alcohol_thread.start()

    try:

        session = create_session()

        logger = SessionLogger(session["base"])

        ocr_ok = False
        face_ok = False
        api_ok = False
        alcohol_ok = False
        liveness_ok = False

        _load_face_cache()

        cam = Camera()

        # ---------- CAMERA CAPTURE ----------
        try:

            print("📸 Capturing driver face...")
            cam.capture_stable_image(session["face_img"])

            print("📸 Capturing license image...")
            cam.capture_stable_image(session["license_img"])

        except Exception as e:

            print("⚠️ Camera error:", e)

            logger.log_error("camera", e)

            cam.close()

            ignition.block_ignition()

            return

        # ---------- LIVENESS ----------
        try:

            print("\n👁️ Performing liveness check...")

            frame_stream = cam.get_frame_stream(duration_sec=3)

            liveness_ok = check_blink_from_frames(frame_stream)

            logger.log_check("liveness", liveness_ok)

        except Exception as e:

            print("⚠️ Liveness error:", e)

            logger.log_error("liveness", e)

            liveness_ok = False

        cam.close()

        if not liveness_ok:

            print("❌ Liveness failed")

        else:

            current_encoding = load_and_encode(session["face_img"])

            face_cached = False

            if current_encoding is not None and _previous_face_encodings is not None:

                dists = np.linalg.norm(
                    _previous_face_encodings - current_encoding,
                    axis=1
                )

                min_dist = float(np.min(dists))

                if min_dist <= 0.6:

                    face_cached = True

                    print("♻️ Cached face recognized")

            # ---------- SKIP OCR IF FACE CACHED ----------
            if face_cached:

                ocr_ok = True
                api_ok = True
                face_ok = True

            else:

                # ---------- OCR ----------
                try:

                    license_data = process_document(
                        session["license_img"],
                        "DRIVING LICENSE",
                        session["ocr_txt"]
                    )

                    ocr_ok = license_data is not None

                except Exception as e:

                    logger.log_error("ocr", e)

                    ocr_ok = False

                # ---------- FACE MATCH ----------
                if ocr_ok:

                    try:

                        face_result = match_faces(
                            session["license_img"],
                            session["face_img"]
                        )

                        face_ok = face_result.get("match", False)

                    except Exception as e:

                        logger.log_error("face_match", e)

                        face_ok = False

                # ---------- LICENSE API ----------
                if ocr_ok and face_ok:

                    try:

                        api_ok = verify_license(license_data)

                    except Exception as e:

                        logger.log_error("license_api", e)

                        api_ok = False

                if ocr_ok and api_ok and face_ok and current_encoding is not None:

                    _save_face_cache(current_encoding)

       # ---------- ALCOHOL CHECK ----------
        alcohol_thread.join()

        try:

            detected, value = alcohol_sensor.is_alcohol_detected()

            print("\n🍺 Alcohol Sensor Reading:", value)

            if detected:
                print("🚫 Alcohol detected! Ignition will be blocked.")
                alcohol_ok = False
            else:
                print("✅ No alcohol detected")
                alcohol_ok = True

            logger.log_check("alcohol", alcohol_ok)

        except Exception as e:

            print("⚠️ Alcohol sensor error:", e)

            alcohol_ok = False

            logger.log_error("alcohol", e)

        # ---------- FINAL DECISION ----------
        final_decision = (
            ocr_ok
            and liveness_ok
            and face_ok
            and api_ok
            and alcohol_ok
        )

        logger.set_final_decision(final_decision)

        logger.write()

        # ---------- IGNITION ----------
        if final_decision:

            ignition.allow_ignition()

            print("\n✅ IGNITION ENABLED")

        else:

            ignition.block_ignition()

            print("\n❌ IGNITION BLOCKED")

    except KeyboardInterrupt:

        print("\n⚠️ Interrupted")

    except Exception as e:

        print("❌ System Error:", e)

        ignition.block_ignition()

    finally:

        ignition.cleanup()

        print("\n🛑 System shutdown complete")


if __name__ == "__main__":
    main()