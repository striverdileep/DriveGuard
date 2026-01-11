# cam.py
import time
from picamera2 import Picamera2
from io import BytesIO

class Camera:
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_still_configuration()
        )
        self.picam2.start()
        time.sleep(1)  # initial sensor settle

    def capture_stable_image(self, filename):
        """
        Captures a stable image.
        Warm-up frame is captured in-memory (no SD card write).
        Only the final image is saved to disk.
        Total time ≈ 3 seconds.
        """

        # ---- Warm-up capture (in memory) ----
        time.sleep(1.5)
        buffer = BytesIO()
        self.picam2.capture_file(buffer, format="jpeg")
        buffer.close()  # discard warm-up frame

        # ---- Final capture (persisted) ----
        time.sleep(1.5)
        self.picam2.capture_file(filename)

        return filename

    def close(self):
        self.picam2.stop()
