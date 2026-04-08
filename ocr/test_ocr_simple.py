from ocr_test import extract_license_from_image

# Give your test image here
image_path = "captured_license.jpg"

result = extract_license_from_image(image_path)

print("\n================ RESULT ================\n")

if result:
    print("✅ Extracted License Number:", result)
else:
    print("❌ License Number NOT Detected")
