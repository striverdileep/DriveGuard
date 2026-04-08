# face_match.py
import face_recognition
import numpy as np
import cv2
import tempfile
from liveliness import check_liveness

def load_and_encode(image_input):
    """
    image_input: either path (str) or bytes (BLOB)
    Returns face encoding or None
    """
    try:
        if isinstance(image_input, bytes):
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp_file.write(image_input)
            tmp_file.close()
            image_path = tmp_file.name
        else:
            image_path = image_input

        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)

        if len(face_locations) == 0:
            print(f"❌ No face found in {image_path}")
            return None

        encoding = face_recognition.face_encodings(image, face_locations)[0]
        return encoding

    except Exception as e:
        print("❌ Encoding error:", e)
        return None

def match_faces(db_face_input, user_image_path, user_video_path=None):
    """
    db_face_input: bytes or path from API
    user_image_path: path to user captured image
    user_video_path: optional video for liveness
    """
    try:
        print("🧠 Running LOCAL face recognition...")
        db_encoding = load_and_encode(db_face_input)
        user_encoding = load_and_encode(user_image_path)

        if db_encoding is None or user_encoding is None:
            return {"match": False, "distance": None, "confidence": 0.0, "liveness": False}

        # Compare faces
        distance_val = np.linalg.norm(db_encoding - user_encoding)
        match = distance_val < 0.6
        confidence = round(1 - distance_val, 4)

        print(f"📊 Distance: {distance_val}")
        print(f"📊 Confidence: {confidence}")

        # Liveness detection
        if user_video_path:
            liveness_ok = check_liveness(user_video_path)
        else:
            liveness_ok = False

        return {
            "match": match,
            "distance": distance_val,
            "confidence": confidence,
            "liveness": liveness_ok
        }

    except Exception as e:
        print("❌ Face match error:", e)
        return {"match": False, "distance": None, "confidence": 0.0, "liveness": False}
