import pytesseract
import cv2
import re
import datetime
import numpy as np


# ---------------- LICENSE AUTO CROP ----------------
def detect_and_crop_license(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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

            if 1.2 < aspect_ratio < 2.8 and w > 180 and h > 100:

                pad = 40

                x = max(0, x - pad)
                y = max(0, y - pad)

                w = min(w_img - x, w + pad * 2)
                h = min(h_img - y, h + pad * 2)

                print("✅ License card detected and cropped safely")
                return img[y:y+h, x:x+w]

    # ✅ Fallback crop (center crop)
    print("⚠️ Auto-crop failed → using fallback crop")

    h, w = img.shape[:2]
    return img[int(h*0.2):int(h*0.8), int(w*0.1):int(w*0.9)]


# ---------------- OCR CORE ----------------
def extract_text(image_path):

    img = cv2.imread(image_path)

    if img is None:
        print("❌ Image not found")
        return ""

    img = detect_and_crop_license(img)

    img = cv2.resize(img, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    thresh = cv2.filter2D(thresh, -1, kernel)

    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(thresh, config=config)

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


# ---------------- WORD FILTER ----------------
BLOCK_WORDS = {
    "GOVERNMENT","INDIA","INDIAN","UNION","STATE",
    "PRADESH","DEPARTMENT","ACCOUNT","CARD",
    "TRANSPORT","PERMANENT","AUTHORITY",
    "DRIVING","LICENCE","LICENSE","VALIDITY",
    "ISSUE","DATE","HOLDER","SIGNATURE",
    "ADDRESS","PRESENT","BLOOD","GROUP",
    "ORGAN","DONOR","STONE","WIFE","OF"
}


# ---------------- DATE FIX ----------------
def fix_invalid_day(day):

    day = int(day)

    if day > 31:
        # Fix common OCR issue (44 → 24, 84 → 04)
        day = int(str(day)[-2:])  # take last 2 digits

    if day == 0:
        day = 1

    return f"{day:02d}"


# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text, lines):

    data = {}

    text = fix_ocr_errors(text)

    # -------- LICENSE NUMBER --------
    lic = re.search(r'\b[A-Z]{2}\d{10,15}\b', text)

    if lic:
        data["LicenseNumber"] = lic.group()


    # -------- NAME --------
    for line in lines:

        words = re.findall(r'[A-Z]{3,}', line)

        filtered = [
            w for w in words
            if w not in BLOCK_WORDS and len(w) > 3
        ]

        if len(filtered) >= 2:

            name = " ".join(filtered[:4])

            # remove trailing garbage words
            name_parts = name.split()
            cleaned = []

            for w in name_parts:
                if w in BLOCK_WORDS:
                    break
                cleaned.append(w)

            if len(cleaned) >= 2:
                data["Name"] = " ".join(cleaned)
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

            # ✅ Fix invalid values
            day = fix_invalid_day(day)

            if len(month) == 1:
                month = '0' + month

            try:
                dt = datetime.datetime.strptime(
                    f"{day}/{month}/{year}",
                    "%d/%m/%Y"
                )

                if 1950 < dt.year < 2100:
                    parsed.append((f"{day}/{month}/{year}", dt))

            except:
                pass

    if parsed:

        parsed = sorted(parsed, key=lambda x: x[1])

        data["DOB"] = parsed[0][0]
        data["ExpiryDate"] = parsed[-1][0]

    return data


# ---------------- MAIN ----------------
def process_document(image_path, doc_name, output_txt):

    try:

        print("\n📄 Running OCR on license...")

        raw = extract_text(image_path)

        print("\n📄 OCR RAW TEXT:\n", raw)

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
