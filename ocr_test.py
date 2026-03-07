"""
DriveGuard OCR Extraction Module
Compatible with Main_File.py
"""

import pytesseract
import cv2
import re
import datetime


# ---------------- OCR CORE ----------------
def extract_text(image_path, doc_name):

    img = cv2.imread(image_path)

    if img is None:
        print(f"❌ Image not found: {image_path}")
        return ""

    # upscale for OCR accuracy
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    config = "--oem 3 --psm 6"

    text = pytesseract.image_to_string(thresh, config=config)

    return text


# ---------------- CLEAN TEXT ----------------
def clean_text(text):

    text = text.upper()

    text = text.replace("\n", " ")

    text = re.sub(r'[^A-Z0-9/: -]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text


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

        if len(w) < 3:
            return False

        if w in BLOCK_WORDS:
            return False

        if not w.isalpha():
            return False

    return True


# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text, lines):

    data = {}

    # ---------------- LICENSE NUMBER ----------------
    lic = re.search(
        r'\b[A-Z]{2}\d{2}\d{4}\d{7}\b|\bDL[- ]?\d{13,16}\b',
        text
    )

    if lic:
        data["LicenseNumber"] = re.sub(r'[\s-]', '', lic.group())

    # ---------------- DOB ----------------
    dob = re.search(
        r'(DOB|DATE OF BIRTH)[ :]*(\d{2}[/-]\d{2}[/-]\d{4})',
        text
    )

    if dob:
        data["DOB"] = dob.group(2).replace('-', '/')

    # ---------------- NAME ----------------
    for line in lines:

        if "NAME" in line:

            parts = line.split(":", 1)

            if len(parts) > 1:

                candidate = re.sub(r'[^A-Z\s]', '', parts[1]).strip()

                if is_valid_person_name(candidate):

                    data["Name"] = candidate

                    break

    # ---------------- DATES ----------------
    dates = re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)

    if "DOB" in data:
        dates = [d for d in dates if d != data["DOB"]]

    parsed_dates = []

    for d in dates:

        d_clean = d.replace('-', '/')

        try:

            parsed = datetime.datetime.strptime(
                d_clean,
                '%d/%m/%Y'
            )

            parsed_dates.append((d_clean, parsed))

        except Exception:
            continue

    if len(parsed_dates) >= 2:

        sorted_dates = sorted(parsed_dates, key=lambda x: x[1])

        data["IssuedDate"] = sorted_dates[0][0]

        data["ExpiryDate"] = sorted_dates[-1][0]

    return data


# ---------------- MAIN ENTRY ----------------
def process_document(image_path, doc_name, output_txt):
    """
    Used directly by Main_File.py
    DO NOT change function name
    """

    try:

        raw = extract_text(image_path, doc_name)

        if not raw:
            return None

        # save raw OCR text
        try:

            with open(output_txt, "w", encoding="utf-8") as f:

                f.write(raw)

        except Exception as e:

            print(f"⚠️ OCR: failed to write output text: {e}")

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

        print("📄 OCR extracted:", data)

        return data

    except Exception as e:

        print(f"⚠️ OCR processing error: {e}")

        return None


# ---------------- TEST MODE ----------------
if __name__ == "__main__":

    print("✅ OCR module test started")

    result = process_document(
        "DL.jpeg",
        "DRIVING LICENSE",
        "test_output.txt"
    )

    print("🔍 OCR Result:", result)