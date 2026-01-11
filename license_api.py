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

    # ---------- BASIC SANITY CHECK ----------
    required_fields = ["LicenseNumber", "Name", "DOB", "ExpiryDate"]

    for field in required_fields:
        if field not in license_data:
            print(f"❌ API: Missing field {field}")
            return False

    # ---------- EXPIRY CHECK ----------
    try:
        expiry = datetime.datetime.strptime(
            license_data["ExpiryDate"], "%d/%m/%Y"
        ).date()
    except ValueError:
        print("❌ API: Invalid expiry date format")
        return False

    today = datetime.date.today()

    if expiry < today:
        print("❌ API: License expired")
        return False

    # ---------- MOCK API LOGIC ----------
    # Here we assume:
    # - License exists
    # - License is not suspended
    # - Details match government records
    #
    # In real life → HTTP API call happens here

    print("✅ API: License verified successfully")
    return True
