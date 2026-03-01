# face_match.py
"""
Face matching using DeepFace library.
Lightweight variant optimized for Raspberry Pi deployment.
"""

from deepface import DeepFace


def match_faces(license_image_path, user_image_path, threshold=0.6):
    """
    Compares face from license image with live user image using DeepFace.

    Args:
        license_image_path: path to license/ID image
        user_image_path: path to user's live face image
        threshold: distance threshold for match (lower = stricter)

    Returns:
        {
            "match": True / False,
            "distance": float or None,
            "confidence": float (0-1)
        }
    """
    try:
        # DeepFace.verify uses yunet (fast detector) & Facenet (lightweight model)
        # anti_spoofing=True detects photo/video attacks
        result = DeepFace.verify(
            img1_path=license_image_path,
            img2_path=user_image_path,
            model_name="Facenet",
            detector_backend="yunet",
            distance_metric="euclidean",
            enforce_detection=True,
            align=True,
            anti_spoofing=True
        )

        distance = float(result.get("distance", 1.0))
        match = result.get("verified", False)

        # confidence: inverse of normalized distance
        confidence = 1.0 - min(distance / 2.0, 1.0)

        return {
            "match": match,
            "distance": round(distance, 4),
            "confidence": round(confidence, 4)
        }

    except Exception as e:
        print(f"⚠️ Face matching error: {e}")
        return {
            "match": False,
            "distance": None,
            "confidence": 0.0,
            "reason": str(e)
        }
