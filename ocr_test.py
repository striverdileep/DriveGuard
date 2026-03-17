import pytesseract
import cv2
import re
import datetime


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

            if w > 300 and h > 150:

                pad = 40

                x = max(0, x - pad)
                y = max(0, y - pad)

                w = min(w_img - x, w + pad * 2)
                h = min(h_img - y, h + pad * 2)

                cropped = img[y:y+h, x:x+w]

                print("✅ License card detected and cropped safely")

                return cropped

    print("⚠️ License auto-crop failed")

    return img


# ---------------- OCR CORE ----------------
def extract_text(image_path):

    img = cv2.imread(image_path)

    if img is None:
        print("❌ Image not found")
        return ""

    img = detect_and_crop_license(img)

    img = cv2.resize(img, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)

    config = "--oem 3 --psm 6"

    text = pytesseract.image_to_string(thresh, config=config)

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
    "ORGAN","DONOR"
}


# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text, lines):

    data = {}

    # -------- LICENSE NUMBER --------
    lic = re.search(r'\b[A-Z]{2}\d{13,14}\b', text)

    if lic:
        data["LicenseNumber"] = lic.group()


    # -------- NAME DETECTION --------
    for line in lines:

        words = re.findall(r'[A-Z]{3,}', line)

        if len(words) >= 2:

            filtered = [w for w in words if w not in BLOCK_WORDS]

            if len(filtered) >= 2:

                name = " ".join(filtered[:3])

                if "DATE" not in name and "VALIDITY" not in name:

                    data["Name"] = name
                    break


    # -------- DOB DETECTION --------
    dob = re.search(
        r'DATE\s*OF\s*[A-Z]{2,6}\s*(\d{2}[./-]\d{2}[./-]\d{4})',
        text
    )

    if dob:

        d = dob.group(1)

        d = d.replace('.', '/')
        d = d.replace('-', '/')

        year = int(d[-4:])

        if year > datetime.datetime.now().year:
            year = year - 80

        d = d[:6] + str(year)

        data["DOB"] = d


    # -------- EXPIRY DATE DETECTION --------
    dates = re.findall(r'\d{2}[./-]\d{2}[./-]\d{4}', text)

    parsed = []

    for d in dates:

        d = d.replace('.', '/')
        d = d.replace('-', '/')

        try:

            dt = datetime.datetime.strptime(d, "%d/%m/%Y")

            parsed.append((d, dt))

        except:
            pass

    if parsed:

        parsed = sorted(parsed, key=lambda x: x[1])

        expiry = parsed[-1][0]

        data["ExpiryDate"] = expiry


    return data


# ---------------- MAIN PROCESS ----------------
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
            print("❌ OCR: No valid fields extracted")
            return None

        print("\n📄 Extracted License Data")

        for k, v in data.items():
            print(f"{k}: {v}")

        return data

    except Exception as e:

        print(f"⚠️ OCR processing error: {e}")

        return None


# ---------------- TEST MODE ----------------
if __name__ == "__main__":

    result = process_document(
        "license.jpg",
        "DRIVING LICENSE",
        "test_output.txt"
    )

    print("OCR Result:", result)
