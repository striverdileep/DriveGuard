import easyocr
import re

# Initialize reader (do this only once)
reader = easyocr.Reader(['en'], gpu=False)

def extract_license_number_from_image(img):

    if img is None:
        print("❌ Invalid image")
        return None

    # OCR
    results = reader.readtext(img)

    print("\n🔍 EasyOCR Results:")
    all_text = ""

    for (bbox, text, prob) in results:
        print(f"{text} (Confidence: {prob:.2f})")
        all_text += text + " "

    # ---------------- CLEANING ----------------
    text = all_text.upper()

    text = text.replace("O", "0")
    text = text.replace("I", "1")

    cleaned = re.sub(r'[^A-Z0-9]', '', text)

    print("🧹 Cleaned Text:", cleaned)

    # ---------------- REGEX ----------------
    pattern = r"(AP|TS|KA|TN|MH|DL|UP|RJ|WB|HR|GJ|MP|PB|BR)[0-9]{14}"

    match = re.search(pattern, cleaned)

    if match:
        return match.group(0)

    return None
