import face_recognition
import numpy as np


def load_and_encode(image_path):
    """
    Loads an image and returns a single face encoding.

    Returns:
        encoding -> numpy array (128)
        None     -> if no face or multiple faces detected
    """

    try:
        image = face_recognition.load_image_file(image_path)

        face_locations = face_recognition.face_locations(image)

        if len(face_locations) == 0:
            print(f"❌ No face detected in {image_path}")
            return None

        if len(face_locations) > 1:
            print(f"⚠️ Multiple faces detected in {image_path}")
            return None

        encodings = face_recognition.face_encodings(image, face_locations)

        if len(encodings) == 0:
            print(f"❌ Face encoding failed for {image_path}")
            return None

        return encodings[0]

    except Exception as e:
        print(f"⚠️ Face encoding error ({image_path}): {e}")
        return None


def match_faces(license_image_path, user_image_path, threshold=0.6):
    """
    Compare license photo and live user photo.

    Returns:
        {
            "match": True/False,
            "distance": float,
            "reason": optional
        }
    """

    try:
        print("🔍 Loading license face...")
        license_encoding = load_and_encode(license_image_path)

        print("🔍 Loading user face...")
        user_encoding = load_and_encode(user_image_path)

        if license_encoding is None or user_encoding is None:
            return {
                "match": False,
                "distance": None,
                "reason": "Face detection failed"
            }

        # Use official face_recognition distance
        distance = face_recognition.face_distance(
            [license_encoding], user_encoding
        )[0]

        match = distance <= threshold

        print(f"📏 Face distance: {distance:.4f}")

        if match:
            print("✅ Face MATCHED")
        else:
            print("❌ Face NOT matched")

        return {
            "match": bool(match),
            "distance": round(float(distance), 4)
        }

    except Exception as e:
        print(f"⚠️ Face matching error: {e}")

        return {
            "match": False,
            "distance": None,
            "reason": str(e)
        }