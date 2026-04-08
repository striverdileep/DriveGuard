import cv2
import pytesseract
import re


def extract_license_number_from_image(img):

    if img is None:
        print("❌ Invalid image")
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Improve OCR
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    text = pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')

    print("\n🔍 Raw OCR:\n", text)

    # ---------------- CLEAN ----------------
    text = text.upper()

    text = text.replace("O", "0")
    text = text.replace("I", "1")
    text = text.replace("L", "1")

    cleaned = re.sub(r'[^A-Z0-9]', '', text)

    print("\n🧹 Cleaned:", cleaned)

    # ---------------- SMART SEARCH ----------------
    best_match = None

    for i in range(len(cleaned) - 10):

        chunk = cleaned[i:i+20]

        # Fix OCR mistakes
        chunk = chunk.replace("4P", "AP")
        chunk = chunk.replace("A0", "AP")
        chunk = chunk.replace("AI", "AP")

        match = re.search(r'(AP|TS|KA|TN)[0-9]{13,16}', chunk)

        if match:
            dl = match.group(0)

            # choose longest match
            if best_match is None or len(dl) > len(best_match):
                best_match = dl

    if best_match:
        print("📤 Final DL Sent to API:", best_match)
        return best_match

    print("❌ No valid license detected")
    return None
