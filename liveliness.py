# liveliness.py
"""
Liveness detection using DeepFace anti-spoofing module.
Detects photo/video attacks and spoofing attempts.
Replaces old dlib EAR blink detection.
"""

from deepface import DeepFace


def check_liveness(image_path):
    """
    Check if the face in the image is real (not a photo/video spoof).
    Uses DeepFace's FasNet anti-spoofing model.

    Args:
        image_path: path to the face image

    Returns:
        True if the face is real/live, False if spoofed or error.
    """
    try:
        # Use deepface represent with anti_spoofing=True
        # Returns a result; if spoofing is detected, is_real flag will be False
        objs = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            detector_backend="yunet",
            anti_spoofing=True,
            enforce_detection=True
        )

        if not objs:
            return False

        # Check anti-spoofing result (first/primary face)
        is_real = objs[0].get("is_real", False)
        return bool(is_real)

    except Exception as e:
        print(f"⚠️ Liveness check error: {e}")
        return False


def check_blink_from_frames(frame_stream):
    """
    Legacy interface: checks liveness from a stream of frames.
    The new deepface anti-spoofing is checked frame-by-frame.
    Returns True if any frame passes the liveness check.

    Note: This is a simplified version. For production, you'd want
    to accumulate confidence or require consistency across frames.
    """
    try:
        frame_count = 0
        liveness_ok = False

        for frame in frame_stream:
            frame_count += 1
            try:
                # Save frame temporarily
                temp_path = f"/tmp/liveness_frame_{frame_count}.jpg"
                import cv2
                cv2.imwrite(temp_path, frame)

                # Check liveness on this frame
                if check_liveness(temp_path):
                    liveness_ok = True
                    # Clean up
                    import os
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    break  # one clean liveness check is enough

            except Exception as e:
                print(f"⚠️ Frame liveness check error: {e}")
                continue

        return liveness_ok

    except Exception as e:
        print(f"⚠️ Liveness stream error: {e}")
        return False
