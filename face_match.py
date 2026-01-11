import face_recognition
import cv2
import numpy as np

def load_and_encode(image_path):
    """
    Loads an image, detects ONE face, and returns its encoding.
    Returns None if no face or multiple faces detected.
    """
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if len(face_locations) == 0:
        print(f"❌ No face detected in {image_path}")
        return None

    if len(face_locations) > 1:
        print(f"⚠️ Multiple faces detected in {image_path}")
        return None

    encoding = face_recognition.face_encodings(image, face_locations)[0]
    return encoding


def match_faces(license_image_path, user_image_path, threshold=0.6):
    """
    Compares face from license image with live user image.

    Returns:
        {
            "match": True / False,
            "distance": float
        }
    """

    license_encoding = load_and_encode(license_image_path)
    user_encoding = load_and_encode(user_image_path)

    if license_encoding is None or user_encoding is None:
        return {
            "match": False,
            "distance": None,
            "reason": "Face detection failed"
        }

    # Compute distance (lower = more similar)
    distance = np.linalg.norm(license_encoding - user_encoding)

    match = distance <= threshold

    return {
        "match": match,
        "distance": round(float(distance), 4)
    }
