import pytesseract
import cv2
import re
import datetime
import numpy as np


# ---------------- LICENSE AUTO CROP ----------------
def detect_and_crop_license(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Improve contrast
    gray = cv2.equalizeHist(gray)

    edges = cv2.Canny(gray, 50, 150)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    h_img, w_img = img.shape[:2]

    for c in contours:

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:

            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)

            if 1.2 < aspect_ratio < 2.8 and w > 200 and h > 120:

                pad = 30

                x = max(0, x - pad)
                y = max(0, y - pad)

                w = min(w_img - x, w + pad * 2)
                h = min(h_img - y, h + pad * 2)

                print("✅ License card detected and cropped")
                return img[y:y+h, x:x+w]

    # fallback
    print("⚠️ Auto-crop failed → using center crop")

    h, w = img.shape[:2]
    return img[int(h*0.25):int(h*0.75), int(w*0.15):int(w*0.85)]


# ---------------- OCR CORE ----------------
def extract_text(image_path):

    img = cv2.imread(image_path)

    if img is None:
        print("❌ Image not found")
        return ""

    img = detect_and_crop_license(img)

    # Resize for better OCR
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Two threshold methods
    thresh1 = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    thresh2 = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    config = "--oem 3 --psm 6"

    text1 = pytesseract.image_to_string(thresh1, config=config)
    text2 = pytesseract.image_to_string(thresh2, config=config)

    # Choose better result
    text = text1 if len(text1) > len(text2) else text2

    return text


# ---------------- OCR ERROR FIX ----------------
def fix_ocr_errors(text):

    replacements = {
        'O': '0', 'I': '1', 'L': '1',
        'Z': '2', 'S': '5', 'B': '8',
        '+': '/', '_': '', '~': '',
        '“': '', '”': '', '‘': '', '’': ''
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


# ---------------- CLEAN TEXT ----------------
def clean_text(text):

    text = text.upper()
    text = text.replace("\n", " ")

    text = re.sub(r'[^A-Z0-9/: .-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text


# ---------------- BLOCK WORDS ----------------
BLOCK_WORDS = {
    "GOVERNMENT","INDIA","INDIAN","UNION","STATE",
    "PRADESH","DEPARTMENT","ACCOUNT","CARD",
    "TRANSPORT","PERMANENT","AUTHORITY",
    "DRIVING","LICENCE","LICENSE","VALIDITY",
    "ISSUE","DATE","HOLDER","SIGNATURE",
    "ADDRESS","PRESENT","BLOOD","GROUP",
    "ORGAN","DONOR","WIFE","OF"
}


# ---------------- DATE FIX ----------------
def fix_invalid_day(day):

    day = int(day)

    if day > 31:
        day = int(str(day)[-2:])

    if day == 0:
        day = 1

    return f"{day:02d}"


# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text, lines):

    data = {}

    text = fix_ocr_errors(text)

    # -------- LICENSE NUMBER --------
    patterns = [
        r'\b[A-Z]{2}\d{10,15}\b',
        r'\b[A-Z]{2}-\d{4}-\d{10}\b',
        r'\b[A-Z]{2}\s?\d{2}\s?\d{11}\b'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            data["LicenseNumber"] = match.group().replace(" ", "")
            break

    # -------- NAME --------
    for line in lines:

        words = re.findall(r'[A-Z]{3,}', line)

        filtered = [
            w for w in words
            if w not in BLOCK_WORDS and len(w) > 3
        ]

        if 2 <= len(filtered) <= 4:
            data["Name"] = " ".join(filtered)
            break

    # -------- DATE EXTRACTION --------
    raw_dates = re.findall(r'\d{1,2}[^0-9]\d{1,2}[^0-9]\d{4}', text)

    print("🧪 Detected raw dates:", raw_dates)

    parsed = []

    for d in raw_dates:

        d = re.sub(r'[^0-9]', '/', d)
        parts = d.split('/')

        if len(parts) == 3:

            day, month, year = parts

            try:
                day = fix_invalid_day(day)

                if len(month) == 1:
                    month = '0' + month

                dt = datetime.datetime.strptime(
                    f"{day}/{month}/{year}",
                    "%d/%m/%Y"
                )

                if 1950 < dt.year < 2100:
                    parsed.append((f"{day}/{month}/{year}", dt))

            except:
                continue

    if parsed:

        parsed = sorted(parsed, key=lambda x: x[1])

        data["DOB"] = parsed[0][0]
        data["ExpiryDate"] = parsed[-1][0]

    # -------- DEBUG OUTPUT --------
    if "LicenseNumber" not in data:
        print("❌ License number not detected")

    if "Name" not in data:
        print("❌ Name not detected")

    if "DOB" not in data or "ExpiryDate" not in data:
        print("❌ Dates not detected")

    return data


# ---------------- MAIN ----------------
def process_document(image_path, doc_name, output_txt):

    try:

        print("\n📄 Running OCR on license...")

        raw = extract_text(image_path)

        print("\n📄 OCR RAW TEXT:\n", raw[:1000])  # limit print

        if not raw:
            return None

        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(raw)

        text = clean_text(raw)

        lines = [
            l.strip()
            for l in raw.upper().split("\n")
            if l.strip()
        ]

        data = extract_fields(text, lines)

        if not data:
            print("❌ OCR failed")
            return None

        print("\n📄 Extracted License Data")

        for k, v in data.items():
            print(f"{k}: {v}")

        return data

    except Exception as e:

        print(f"⚠️ OCR error: {e}")
        return None


# ---------------- TEST ----------------
if __name__ == "__main__":

    result = process_document(
        "license.jpg",
        "DRIVING LICENSE",
        "test_output.txt"
    )

    print("OCR Result:", result)
