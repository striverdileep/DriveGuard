# ocr_test.py

import cv2
import numpy as np
import pytesseract
import re

# ---------------- TEXT REGION CROP ----------------
def crop_text_region(image, pad=10):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return image

    x_min, y_min = 99999, 99999
    x_max, y_max = 0, 0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h < 500:
            continue
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x + w)
        y_max = max(y_max, y + h)

    if x_max <= x_min or y_max <= y_min:
        return image

    # Add padding
    h, w = image.shape[:2]
    x_min = max(0, x_min - pad)
    y_min = max(0, y_min - pad)
    x_max = min(w, x_max + pad)
    y_max = min(h, y_max + pad)

    return image[y_min:y_max, x_min:x_max]

# ---------------- SKEW CORRECTION ----------------
def deskew_projection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    angles = np.arange(-15, 16, 1)
    best_angle = 0
    max_score = -1
    h, w = thresh.shape
    center = (w // 2, h // 2)

    for angle in angles:
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(thresh, M, (w, h))
        projection = np.sum(rotated, axis=1)
        score = np.var(projection)
        if score > max_score:
            max_score = score
            best_angle = angle

    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    corrected = cv2.warpAffine(image, M, (w, h))
    return corrected

# ---------------- DL EXTRACTION ----------------
def extract_dl_number(text):
    text = text.upper()
    # Fix common OCR mistakes
    text = text.replace("O", "0").replace("I", "1").replace("Z", "2").replace("S", "5")
    cleaned = re.sub(r'[^A-Z0-9]', '', text)
    # Pattern: 2-letter state code + 13 digits
    pattern = r"(AP|TS|KA|TN|MH|DL|UP|RJ|WB|HR|GJ|MP|PB|BR)[0-9]{13}"
    match = re.search(pattern, cleaned)
    if match:
        dl = match.group(0)
        return dl[:15]  # Ensure exactly 15 chars
    return None

# ---------------- MAIN OCR FUNCTION ----------------
def process_license_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("❌ OCR: Image not found")
        return None

    print("🔍 OCR Processing started...")

    # Step 1: Crop text region with padding
    img = crop_text_region(img, pad=10)

    # Step 2: Deskew image
    img = deskew_projection(img)

    # Step 3: Preprocess for Tesseract
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    gray = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Step 4: OCR with whitelist (letters + digits)
    config = r'--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text1 = pytesseract.image_to_string(gray, config=config)
    text2 = pytesseract.image_to_string(255 - gray, config=config)  # optional inverted pass
    text = (text1 + "\n" + text2).replace(" ", "").replace("\n", "").upper()

    print("\n📄 OCR RAW:\n", text)

    # Step 5: Extract DL number
    dl_number = extract_dl_number(text)
    print("📤 Extracted DL:", dl_number)
    return dl_number
