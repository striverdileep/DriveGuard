# cam.py

import time
import cv2
from picamera2 import Picamera2


class Camera:
    """
    Single authoritative camera interface.
    Uses Picamera2 ONLY.
    Handles exposure stabilization automatically.

    Camera Connections:

    Raspberry Pi Camera Module (CSI Camera)

    Connection type:
        CSI Ribbon Cable (NOT GPIO)

    Steps:
        1. Connect camera ribbon cable to Raspberry Pi CSI port
        2. Blue side of ribbon faces Ethernet port
        3. Enable camera interface:
            sudo raspi-config
            Interface Options → Camera → Enable
        4. Reboot Raspberry Pi

    No GPIO pins are used by this module.
    """

    def __init__(self):
        try:
            print("📷 Initializing camera...")

            self.picam2 = Picamera2()

            config = self.picam2.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )

            self.picam2.configure(config)
            self.picam2.start()

            # Allow auto exposure / white balance to settle
            time.sleep(2)

            print("✅ Camera initialized successfully")

        except Exception as e:
            print(f"⚠️ Camera init error: {e}")
            self.picam2 = None


    def capture_stable_image(self, filename):
        """
        Capture stable still image after discarding garbage frame and stabilizing.
        
        Raspberry Pi cameras typically produce a garbage (unstable) first frame.
        This function:
        1. Captures and discards the first garbage frame
        2. Allows camera to stabilize for exposure/white balance
        3. Captures and returns the valid image
        """

        if self.picam2 is None:
            raise RuntimeError("Camera not initialized")

        try:
            # Step 1: Capture and discard first garbage frame from Raspberry Pi camera
            print("📷 Capturing garbage frame...")
            garbage_frame = self.picam2.capture_array()
            print("🗑️ Garbage frame discarded (Raspberry Pi camera warmup)")
            
            # Step 2: Allow camera to stabilize with additional frames
            print("⚙️ Stabilizing camera exposure and white balance...")
            for i in range(4):
                self.picam2.capture_array()
                time.sleep(0.2)
            
            # Step 3: Capture valid image
            print("📸 Capturing valid image...")
            frame = self.picam2.capture_array()

            if frame is None:
                raise RuntimeError("Failed to capture frame")

            # Convert RGB → BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            cv2.imwrite(filename, frame)

            print(f"✅ Valid image saved: {filename}")

            return filename

        except Exception as e:
            raise RuntimeError(f"Camera capture error: {e}")


    def get_frame_stream(self, duration_sec=6, fps=12):
        """
        Generator that yields frames for liveness detection
        Increased duration and FPS for better blink detection
        """

        if self.picam2 is None:
            raise RuntimeError("Camera not initialized")

        interval = 1.0 / fps
        end_time = time.time() + duration_sec

        frame_count = 0

        print("👁️ Starting frame stream for liveness detection...")
        print(f"⏱ Duration: {duration_sec} sec | FPS: {fps}")

        while time.time() < end_time:

            try:
                frame = self.picam2.capture_array()

                if frame is None:
                    continue

                # Convert RGB → BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                frame_count += 1

                yield frame

            except Exception as e:
                print(f"⚠️ Camera stream error: {e}")
                break

            time.sleep(interval)

        print(f"👁️ Frame stream ended | Frames captured: {frame_count}")


    def close(self):
        """
        Safely stop the camera
        """

        if self.picam2:
            try:
                self.picam2.stop()
                print("🛑 Camera stopped")
            except Exception:
                pass