# Main_File.py
import os
from datetime import datetime
from cam import Camera
from ocr_test import process_document
from face_match import match_faces
from alcohol_sensor import AlcoholSensor
from license_api import verify_license

BASE_DIR = "data/sessions"


def create_session():
    session_id = datetime.now().strftime("session_%Y-%m-%d_%H-%M-%S")
    session_path = os.path.join(BASE_DIR, session_id)
    image_dir = os.path.join(session_path, "images")

    os.makedirs(image_dir, exist_ok=True)

    return {
        "session": session_id,
        "base": session_path,
        "license_img": os.path.join(image_dir, "license.jpg"),
        "face_img": os.path.join(image_dir, "user_face.jpg"),
        "ocr_txt": os.path.join(session_path, "license.txt")
    }


def main():
    print("\n🚗 DriveGuard – Advanced Session Mode\n")

    # ---------------- SESSION ----------------
    session = create_session()

    # ---------------- CAMERA ----------------
    cam = Camera()
    cam.capture_stable_image(session["face_img"])
    cam.capture_stable_image(session["license_img"])
    cam.close()

    # ---------------- OCR ----------------
    license_data = process_document(
        image_path=session["license_img"],
        doc_name="DRIVING LICENSE",
        output_txt=session["ocr_txt"]
    )
    ocr_ok = license_data is not None

    # ---------------- FACE MATCH ----------------
    face_result = match_faces(
        session["license_img"],
        session["face_img"]
    )
    face_ok = face_result["match"]

    # ---------------- ALCOHOL CHECK ----------------
    sensor = AlcoholSensor(channel=0)
    alcohol_detected, alcohol_value = sensor.is_alcohol_detected()
    sensor.close()

    alcohol_ok = not alcohol_detected

    # ---------------- LICENSE API ----------------
    api_ok = False
    if ocr_ok:
        api_ok = verify_license(license_data)

    # ---------------- FINAL DECISION ----------------
    final_decision = (
        ocr_ok
        and face_ok
        and alcohol_ok
        and api_ok
    )

    # ---------------- RESULT ----------------
    print("\n========== FINAL RESULT ==========")
    print(f"OCR OK           : {ocr_ok}")
    print(f"Face Match OK    : {face_ok}")
    print(f"Alcohol OK       : {alcohol_ok}")
    print(f"License API OK   : {api_ok}")

    if final_decision:
        print("\n✅ IGNITION ALLOWED")
    else:
        print("\n❌ IGNITION BLOCKED")

    print("=================================\n")


if __name__ == "__main__":
    main()
