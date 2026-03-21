# cam.py
import time
import cv2
from picamera2 import Picamera2


class Camera:
    """
    Single authoritative camera interface.
    Uses Picamera2 ONLY.
    """

    def __init__(self):
        try:
            self.picam2 = Picamera2()
            self.picam2.configure(
                self.picam2.create_video_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
            )
            self.picam2.start()
            time.sleep(1)  # sensor settle
        except Exception as e:
            print(f"⚠️ Camera init error: {e}")
            self.picam2 = None

    def capture_stable_image(self, filename):
        """
        Capture a stable still image after auto-adjustment.
        """
        if self.picam2 is None:
            raise RuntimeError("Camera not initialized")
        try:
            time.sleep(1.5)
            frame = self.picam2.capture_array()
            cv2.imwrite(filename, frame)
            return filename
        except Exception as e:
            print(f"⚠️ Camera capture error: {e}")
            return None

    def get_frame_stream(self, duration_sec=3, fps=10):
        """
        Generator that yields frames for liveness detection.
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

    def close(self):
        self.picam2.stop()
