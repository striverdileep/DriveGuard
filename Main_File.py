# Main_File.py
import os
from datetime import datetime
from cam import Camera
from ocr_test import process_document
from face_match import match_faces
from alcohol_sensor import AlcoholSensor



BASE_DIR = "data/sessions"

def create_session():
    session_id = datetime.now().strftime("session_%Y-%m-%d_%H-%M-%S")
    session_path = os.path.join(BASE_DIR, session_id)

    image_dir = os.path.join(session_path, "images")
    os.makedirs(image_dir, exist_ok=True)

    return {
        "session": session_id,
        "base": session_path,
        "images": image_dir,
        "license_img": os.path.join(image_dir, "license.jpg"),
        "face_img": os.path.join(image_dir, "user_face.jpg"),
        "ocr_txt": os.path.join(session_path, "license.txt")
    }

def main():
    print("\n🚗 DriveGuard – Advanced Session Mode\n")

    session = create_session()
    print(f"🆔 Session Created: {session['session']}")

    cam = Camera()

    print("📸 Capturing user face...")
    cam.capture_stable_image(session["face_img"])

    print("📸 Capturing license image...")
    cam.capture_stable_image(session["license_img"])

    cam.close()

    print("🔍 Running OCR...")
    license_data = process_document(
        image_path=session["license_img"],
        doc_name="DRIVING LICENSE",
        output_txt=session["ocr_txt"]
    )

    if not license_data:
        print("❌ OCR failed")
        return

    print("🧑‍🦰 Verifying face...")
    result = match_faces(
        session["license_img"],
        session["face_img"]
    )

    if not result["match"]:
        print("❌ Face verification failed")
        return

    print(f"✅ Face verified (distance={result['distance']})")
    print("\n🎯 SESSION SUCCESSFUL")
    print(f"📂 Data stored at: {session['base']}")

    print("\n🍺 Checking alcohol level...")
    sensor = AlcoholSensor(channel=0)

    alcohol_detected, value = sensor.is_alcohol_detected()

    sensor.close()

    print(f"Alcohol Sensor Value: {value}")

    if alcohol_detected:
        print("❌ Alcohol detected! Ignition blocked.")
        return
    else:
        print("✅ No alcohol detected.")

if __name__ == "__main__":
    main()
