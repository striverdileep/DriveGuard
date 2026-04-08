# cam.py
import time
import cv2
from picamera2 import Picamera2


class Camera:
    """
    Single authoritative camera interface.
    Uses Picamera2 ONLY.

    - Low resolution for streaming (fast)
    - High resolution for image capture (OCR)
    """

    def __init__(self):
        try:
            self.picam2 = Picamera2()

            # 🔹 Default: LOW RES for streaming (fast)
            self.picam2.configure(
                self.picam2.create_video_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
            )

            self.picam2.start()
            time.sleep(1.5)  # allow sensor to stabilize

            print("✅ Camera initialized successfully")

        except Exception as e:
            print(f"⚠️ Camera init error: {e}")
            self.picam2 = None

    # --------------------------------------------------
    # 📸 HIGH QUALITY IMAGE CAPTURE (FOR OCR / FACE IMAGE)
    # --------------------------------------------------
    def capture_stable_image(self, filename):
        """
        Capture a high-resolution image for OCR / face capture.
        Automatically switches resolution.
        """
        if self.picam2 is None:
            raise RuntimeError("Camera not initialized")

        try:
            print("⚙️ Switching to HIGH RES mode for capture...")

            # 🔴 Stop current stream
            self.picam2.stop()

            # 🔹 HIGH RES config (for OCR clarity)
            self.picam2.configure(
                self.picam2.create_still_configuration(
                    main={"size": (1640, 1232)}
                )
            )

            self.picam2.start()

            # 🔥 Let exposure + white balance settle
            print("⚙️ Stabilizing camera exposure and white balance...")
            time.sleep(2)

            # 📷 Capture frame
            frame = self.picam2.capture_array()
            cv2.imwrite(filename, frame)

            print(f"✅ Image saved: {filename}")

            # 🔄 Switch back to LOW RES mode
            print("⚙️ Switching back to LOW RES mode...")

            self.picam2.stop()

            self.picam2.configure(
                self.picam2.create_video_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
            )

            self.picam2.start()
            time.sleep(1)

            return filename

        except Exception as e:
            print(f"⚠️ Camera capture error: {e}")
            return None

    # --------------------------------------------------
    # 🎥 STREAM FRAMES (FOR LIVENESS / FACE DETECTION)
    # --------------------------------------------------
    def get_frame_stream(self, duration_sec=3, fps=10):
        """
        Generator that yields frames for liveness detection.
        Uses LOW RES mode for speed.
        """
        if self.picam2 is None:
            raise RuntimeError("Camera not initialized")

        interval = 1.0 / fps
        end_time = time.time() + duration_sec

        while time.time() < end_time:
            try:
                frame = self.picam2.capture_array()
            except Exception as e:
                print(f"⚠️ Camera stream error: {e}")
                break

            yield frame
            time.sleep(interval)

    # --------------------------------------------------
    # 🔴 CLEANUP
    # --------------------------------------------------
    def close(self):
        if self.picam2:
            self.picam2.stop()
            print("🛑 Camera stopped")
