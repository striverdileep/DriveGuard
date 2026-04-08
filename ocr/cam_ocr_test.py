from picamera2 import Picamera2
import time
from datetime import datetime
import cv2
from ocr_test import extract_license_number_from_image

def capture_image():
    picam2 = Picamera2()

    picam2.configure(
        picam2.create_still_configuration(main={"size": (1640, 1232)})
    )

    picam2.start()
    print("📸 Camera started")

    time.sleep(1)

    print("📷 Capturing image at:", datetime.now().strftime("%H:%M:%S"))
    img = picam2.capture_array()

    picam2.stop()

    # Save for debugging
    cv2.imwrite("full_capture.jpg", img)

    return img


def main():
    img = capture_image()

    print("\n🔍 Running OCR on processed image...\n")
    result = extract_license_number_from_image(img)

    print("\n================ RESULT ================\n")
    if result:
        print("✅ Extracted License Number:", result)
    else:
        print("❌ License Number NOT Detected")


if __name__ == "__main__":
    main()
