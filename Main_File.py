# Main_File.py
import os
import threading
from datetime import datetime
import numpy as np
from session_logger import SessionLogger

from cam import Camera
from ocr_test import process_document
from face_match import match_faces, load_and_encode
from liveness import check_blink_from_frames
from alcohol_sensor import AlcoholSensor
from license_api import verify_license
from ignition_control import IgnitionController

BASE_DIR = "data/sessions"
alcohol_sensor = None

# ----- face cache (multiple users) -----
# We keep a 2‑D array of encodings, one per previously validated user.
# Shape = (n_users, 128). If the file does not exist we treat it as empty.
_face_cache_path = os.path.join(BASE_DIR, "face_cache.npy")
_previous_face_encodings = None  # np.ndarray of shape (m, 128)


def _load_face_cache():
    """Load saved encodings array or set to None if missing/invalid."""
    global _previous_face_encodings
    try:
        data = np.load(_face_cache_path)
        # ensure 2D array
        if data.ndim == 1:
            data = data.reshape(1, -1)
        _previous_face_encodings = data
    except Exception:
        _previous_face_encodings = None


def _save_face_cache(enc, max_entries=50, distance_threshold=0.6):
    """Add encoding to cache if not already present.

    Encodings very close to an existing entry (<= threshold) are
    considered duplicates and not re‑added. The cache is capped to
    ``max_entries`` most‑recent encodings by dropping oldest ones.
    """
    try:
        if _previous_face_encodings is None:
            arr = np.array([enc])
        else:
            # check duplicates
            dists = np.linalg.norm(_previous_face_encodings - enc, axis=1)
            if np.any(dists <= distance_threshold):
                return  # already cached
            arr = np.vstack([_previous_face_encodings, enc])

        # trim if too many
        if arr.shape[0] > max_entries:
            arr = arr[-max_entries:]

        np.save(_face_cache_path, arr)
        # update in-memory copy as well
        global _previous_face_encodings
        _previous_face_encodings = arr
    except Exception:
        pass



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

        # default result flags in case of early exit
        ocr_ok = False
        face_ok = False
        api_ok = False
        alcohol_ok = False

        # try load cached face encoding before any capture
        _load_face_cache()

        # 📸 Capture images
        cam = Camera()
        try:
            cam.capture_stable_image(session["face_img"])
            cam.capture_stable_image(session["license_img"])
        except Exception as e:
            print(f"⚠️ Camera capture exception: {e}")
            logger.log_error("camera", e)
            # unable to capture; abort early
            liveness_ok = False
            final_decision = False
            # mark remaining logs
            logger.log_check("liveness", False, {"skipped": True})
            logger.log_check("ocr", False, {"skipped": True})
            logger.log_check("face_match", False, {"skipped": True})
            logger.log_check("license_api", False, {"skipped": True})
            alcohol_thread.join()
            alcohol_ok = False
            logger.log_check("alcohol", False, {"skipped": True})
            cam.close()
            # jump to final decision below
            logger.set_final_decision(final_decision)
            logger.write()
            ignition.block_ignition()
            print("\n❌ IGNITION BLOCKED")
            print("\n🛑 System shutdown complete")
            return

        # 👁️ Liveness check (camera still running)
        try:
            print("\n👁️ Performing liveness check...")
            frame_stream = cam.get_frame_stream(duration_sec=3)
            liveness_ok = check_blink_from_frames(frame_stream)
            logger.log_check("liveness", liveness_ok)
        except Exception as e:
            print(f"⚠️ Liveness exception: {e}")
            logger.log_error("liveness", e)
            liveness_ok = False

        # close camera immediately after liveness
        try:
            cam.close()
        except Exception:
            pass

        # if liveness failed, short-circuit
        if not liveness_ok:
            print("❌ Liveness failed")
            final_decision = False
            # mark remaining checks as skipped
            logger.log_check("ocr", False, {"skipped": True})
            logger.log_check("face_match", False, {"skipped": True})
            logger.log_check("license_api", False, {"skipped": True})
            # wait for alcohol sensor and log skipped
            alcohol_thread.join()
            alcohol_ok = False
            logger.log_check("alcohol", alcohol_ok, {"skipped": True})
            # fall through to decision and cleanup
        else:
            # ----- face cache comparison -----
            current_encoding = load_and_encode(session["face_img"])
            face_cached = False
            if (
                current_encoding is not None
                and _previous_face_encodings is not None
            ):
                # compute distance to each stored encoding
                dists = np.linalg.norm(
                    _previous_face_encodings - current_encoding,
                    axis=1
                )
                min_dist = float(np.min(dists))
                if min_dist <= 0.6:
                    face_cached = True
                    print("♻️ Recognized cached face (distance %.4f)" % min_dist)

            # default state for subsequent flags
            ocr_ok = False
            api_ok = False
            face_ok = False
            alcohol_ok = False

            if face_cached:
                # bypass OCR & API; we already have face match
                ocr_ok = True
                api_ok = True
                face_ok = True
                logger.log_check("ocr", True, {"cached": True})
                logger.log_check("face_match", True, {"cached": True})
                logger.log_check("license_api", True, {"skipped": True})
            else:
                # 🔍 OCR
                try:
                    license_data = process_document(
                        session["license_img"],
                        "DRIVING LICENSE",
                        session["ocr_txt"]
                    )
                    ocr_ok = license_data is not None
                    logger.log_check("ocr", ocr_ok, license_data if ocr_ok else None)
                    if not ocr_ok:
                        print("❌ OCR failed")
                        # mark remaining as skipped
                        logger.log_check("face_match", False, {"skipped": True})
                        logger.log_check("license_api", False, {"skipped": True})
                except Exception as e:
                    print(f"⚠️ OCR exception: {e}")
                    logger.log_error("ocr", e)
                    ocr_ok = False
                    logger.log_check("face_match", False, {"skipped": True})
                    logger.log_check("license_api", False, {"skipped": True})

                if ocr_ok:
                    # 🧑‍🦰 Face match
                    try:
                        face_result = match_faces(
                            session["license_img"],
                            session["face_img"]
                        )
                        face_ok = face_result.get("match", False)
                        logger.log_check(
                            "face_match",
                            face_ok,
                            {"distance": face_result.get("distance")}
                        )
                        if not face_ok:
                            print("❌ Face match failed")
                    except Exception as e:
                        print(f"⚠️ Face match exception: {e}")
                        logger.log_error("face_match", e)
                        face_ok = False

                # license API only after OCR and face match
                if ocr_ok and face_ok:
                    try:
                        api_ok = verify_license(license_data)
                        logger.log_check("license_api", api_ok)
                        if not api_ok:
                            print("❌ License API failed")
                    except Exception as e:
                        print(f"⚠️ License API exception: {e}")
                        logger.log_error("license_api", e)
                        api_ok = False
                elif not (ocr_ok and face_ok):
                    # either OCR or face failed, ensure API logged as skipped
                    logger.log_check("license_api", False, {"skipped": True})

                # if first-time user passes all checks, update cache
                # (OCR, API and face match must all be OK)
                if ocr_ok and api_ok and face_ok and current_encoding is not None:
                    _save_face_cache(current_encoding)

            # ⏳ Ensure alcohol sensor ready
            alcohol_thread.join()
            try:
                detected, value = alcohol_sensor.is_alcohol_detected()
                alcohol_ok = not detected
                logger.log_check(
                    "alcohol",
                    alcohol_ok,
                    {"sensor_value": value}
                )
            except Exception as e:
                print(f"⚠️ Alcohol sensor exception: {e}")
                logger.log_error("alcohol", e)
                alcohol_ok = False
                logger.log_check("alcohol", alcohol_ok, {"error": str(e)})

            # compute final decision after all applicable checks
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
