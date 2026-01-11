# ocr_test.py
import cv2
import pytesseract
import re

def write_to_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def extract_text(image_path, doc_name):
    img = cv2.imread(image_path)
    if img is None:
        return ""

    scale = 2.0 if "DL" in doc_name else 1.5
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    psm = 6 if "DL" in doc_name else 3
    config = f"--oem 3 --psm {psm}"
    return pytesseract.image_to_string(thresh, config=config)

def clean_text(text):
    text = text.upper()
    text = re.sub(r'[^A-Z0-9/: \n-]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_fields(text):
    data = {}

    m = re.search(r'\b[A-Z]{2}\d{2}\d{4}\d{7}\b|\bDL[- ]?\d{13,16}\b', text)
    if m:
        data["LicenseNumber"] = m.group().replace(" ", "").replace("-", "")

    dob = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', text)
    if dob:
        data["DOB"] = dob.group()

    dates = re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)
    if len(dates) >= 2:
        dates = sorted(dates, key=lambda d: d[-4:])
        data["IssuedDate"] = dates[0]
        data["ExpiryDate"] = dates[-1]

    words = [w for w in text.split() if w.isalpha() and len(w) >= 3]
    if 1 < len(words) <= 4:
        data["Name"] = " ".join(words[:3])

    return data

def process_document(image_path, doc_name, output_txt):
    raw = extract_text(image_path, doc_name)
    if not raw:
        return None

    cleaned = clean_text(raw)
    fields = extract_fields(cleaned)

    if not fields:
        return None

    lines = [f"{k}: {v}" for k, v in fields.items()]
    write_to_file(output_txt, "\n".join(lines))
    return fields
