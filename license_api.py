# license_api.py
"""
License Verification API Module (Mock)

This module simulates an external license verification API.
Later, this can be replaced with a real REST API call.
"""

import datetime


def verify_license(license_data):
    """
    Simulates license verification.

    Args:
        license_data (dict): Extracted OCR fields

    Returns:
        bool: True if license is valid, False otherwise
    """

    required_fields = ["LicenseNumber", "Name", "DOB", "ExpiryDate"]

    try:
        if not isinstance(license_data, dict):
            print("❌ API: Invalid license data format")
            return False

        # ---------- CHECK REQUIRED FIELDS ----------
        for field in required_fields:
            if field not in license_data or not license_data[field]:
                print(f"❌ API: Missing or empty field -> {field}")
                return False

        print("🔎 API: All required fields present")

        # ---------- PARSE EXPIRY DATE ----------
        expiry_str = license_data["ExpiryDate"]

        try:
            expiry = datetime.datetime.strptime(
                expiry_str.strip(), "%d/%m/%Y"
            ).date()
        except Exception:
            print(f"❌ API: Invalid expiry date format -> {expiry_str}")
            return False

        today = datetime.date.today()

        # ---------- CHECK EXPIRY ----------
        if expiry < today:
            print(f"❌ API: License expired on {expiry}")
            return False

        # ---------- MOCK GOVERNMENT VALIDATION ----------
        # In a real system this section would call:
        # Government Transport API / RTO database

        print("✅ API: License verified successfully")

        return True

    except Exception as e:
        print(f"⚠️ API error: {e}")
        return False