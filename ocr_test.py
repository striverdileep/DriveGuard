"""
DriveGuard OCR Extraction Module
Compatible with Main_File.py (DO NOT change main file)
"""

import pytesseract
import cv2
import re
import datetime  # Added for date parsing

# ---------------- OCR CORE ----------------
def extract_text(image_path, doc_name):
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Image not found: {image_path}")
        return ""

    scale = 2.0 if "DRIVING" in doc_name or "DL" in doc_name else 1.5
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    psm = 6 if "DRIVING" in doc_name or "DL" in doc_name else 3
    config = f"--oem 3 --psm {psm}"

    return pytesseract.image_to_string(thresh, config=config)


# ---------------- CLEAN TEXT ----------------
def clean_text(text):
    text = text.upper().replace("\n", " ")
    text = re.sub(r'[^A-Z0-9/: -]', ' ', text)
    return re.sub(r'\s+', ' ', text)


# ---------------- NAME VALIDATION ----------------
BLOCK_WORDS = {
    "GOVERNMENT", "INDIA", "STATE", "DEPARTMENT",
    "TRANSPORT", "AUTHORITY", "DRIVING", "LICENCE",
    "VALID", "TILL", "DATE", "BIRTH", "ISSUED", "EXPIRY",
    "NAME", "DL", "NO"
}

def is_valid_person_name(line):
    words = line.split()
    if not (2 <= len(words) <= 4):
        return False
    for w in words:
        if len(w) < 3 or w in BLOCK_WORDS or not w.isalpha():
            return False
    return True


# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text, lines):
    data = {}

    # License number
    m = re.search(
        r'\b[A-Z]{2}\s?\d{2}\s?\d{4}\s?\d{7}\b|\bDL[- ]?\d{13,16}\b',
        text
    )
    if m:
        data["License_Num"] = re.sub(r'[\s-]', '', m.group())

    # DOB
    dob = re.search(r'(DOB|DATE OF BIRTH)[: ]*(\d{2}[/-]\d{2}[/-]\d{4})', text)
    if dob:
        data["DOB"] = dob.group(2)

    # Name
    for line in lines:
        if "NAME" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                candidate = re.sub(r'[^A-Z\s]', '', parts[1]).strip()
                if is_valid_person_name(candidate):
                    data["Name"] = candidate
                    break

    # Issued & Expiry - Fixed sorting by parsing dates chronologically
    dates = re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)
    if "DOB" in data:
        dates = [d for d in dates if d != data["DOB"]]

    parsed_dates = []
    for d in dates:
        d_clean = d.replace('-', '/')  # Normalize separator
        try:
            parsed = datetime.datetime.strptime(d_clean, '%d/%m/%Y')
            parsed_dates.append((d, parsed))
        except ValueError:
            pass  # Skip invalid dates

    if len(parsed_dates) >= 2:
        sorted_dates = sorted(parsed_dates, key=lambda x: x[1])  # Sort by datetime
        data["Issued_Date"] = sorted_dates[0][0]
        data["Expiry_Date"] = sorted_dates[-1][0]

    return data


# ---------------- MAIN ENTRY (USED BY Main_File.py) ----------------
def process_document(image_path, doc_name, output_txt):
    """
    DO NOT change signature — used directly by Main_File.py
    """
    raw = extract_text(image_path, doc_name)
    if not raw:
        return None

    # Save raw OCR output
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(raw)

    text = clean_text(raw)
    lines = [l.strip() for l in raw.upper().split("\n") if l.strip()]

    data = extract_fields(text, lines)

    if not data:
        return None

    return data

if __name__ == "__main__":
    print("✅ OCR module test started")

    result = process_document(
        "DL.jpeg",                 # image path
        "DRIVING LICENSE",         # document name
        "test_output.txt"          # output text file
    )

    print("🔍 OCR Result:", result)