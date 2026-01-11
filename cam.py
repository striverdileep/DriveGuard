# cam.py
import time
from picamera2 import Picamera2

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
        Captures a stable image using a dummy frame for auto-adjustment.
        Total time ≈ 3 seconds.
        """
        # Warm-up phase
        time.sleep(1.5)
        self.picam2.capture_file("dummy.jpg")  # garbage image

        # Final capture
        time.sleep(1.5)
        self.picam2.capture_file(filename)

        return filename

    def close(self):
        self.picam2.stop()
