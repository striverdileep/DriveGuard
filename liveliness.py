"""
Liveness detection using DeepFace anti-spoofing module.
Optimized for Raspberry Pi.
"""

from deepface import DeepFace
import cv2
import os


def check_liveness(image_path):
    """
    Check if the face in the image is real (not spoofed).
    """
    try:
        print(f"🔍 Checking liveness for: {image_path}")

        objs = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            detector_backend="opencv",
            anti_spoofing=True,
            enforce_detection=False
        )

        if not objs:
            print("⚠️ No face detected → liveness failed")
            return False

        is_real = objs[0].get("is_real", False)

        print(f"🧠 Liveness result: {is_real}")

        return bool(is_real)

    except Exception as e:
        print(f"⚠️ Liveness check error: {e}")
        return False


def check_blink_from_frames(frame_stream):
    """
    Liveness check from multiple frames.
    """
    try:
        frame_count = 0

        for frame in frame_stream:
            frame_count += 1

            try:
                temp_path = f"/tmp/liveness_frame_{frame_count}.jpg"

                cv2.imwrite(temp_path, frame)

                if check_liveness(temp_path):
                    print(f"✅ Liveness passed on frame {frame_count}")

                    try:
                        os.remove(temp_path)
                    except:
                        pass

                    return True

                try:
                    os.remove(temp_path)
                except:
                    pass

            except Exception as e:
                print(f"⚠️ Frame error: {e}")
                continue

        print("❌ Liveness failed for all frames")
        return False

    except Exception as e:
        print(f"⚠️ Liveness stream error: {e}")
        return False
