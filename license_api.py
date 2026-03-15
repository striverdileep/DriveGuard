# license_api.py
"""
License Verification API Module

This module verifies driver's licenses against the License Verification API.
It communicates with the external REST API running on localhost:5000.

IMPORTANT: This module is SYNCHRONOUS and BLOCKING.
All API calls are thread-safe and will block the current thread until completion.
No concurrent API calls can occur.
"""

import datetime
import requests
import os
import threading
import time
from typing import Dict, Any

# Configuration
LICENSE_API_URL = os.getenv("LICENSE_API_URL", "http://localhost:5000")
LICENSE_API_ENDPOINT = f"{LICENSE_API_URL}/verify-license"
API_TIMEOUT = 10  # seconds

# Thread-safe lock to ensure only one API call at a time
_api_lock = threading.Lock()

# Session with connection pooling for better performance
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})


def verify_license(license_data: Dict[str, Any]) -> bool:
    """
    Verifies a driver's license against the License Verification API.

    BLOCKING OPERATION: This function will block the current thread until:
    1. The lock is acquired (ensuring no concurrent API calls)
    2. The API response is received or timeout occurs

    No other code will execute while this function runs.

    Args:
        license_data (dict): Extracted OCR fields with keys:
            - LicenseNumber: Driver's license number
            - Name: Driver's name
            - DOB: Date of birth (DD/MM/YYYY format)
            - ExpiryDate: License expiry date (DD/MM/YYYY format)

    Returns:
        bool: True if license is valid and verified, False otherwise
    """

    required_fields = ["LicenseNumber", "Name", "DOB", "ExpiryDate"]

    # ACQUIRE LOCK - No other code runs until this completes
    print("🔒 API: Acquiring lock for license verification (blocking operation)...")
    with _api_lock:
        print("🔒 API: Lock acquired - starting verification (no other code can run)")

        api_start_time = time.time()

        try:
            # ---------- VALIDATE INPUT ----------
            if not isinstance(license_data, dict):
                print("❌ API: Invalid license data format")
                return False

            # Check required fields and ensure they are strings
            payload = {}
            for field in required_fields:
                if field not in license_data or license_data[field] is None:
                    print(f"❌ API: Missing field -> {field}")
                    return False

                # Convert to string and strip whitespace
                field_value = str(license_data[field]).strip()
                if not field_value:
                    print(f"❌ API: Empty field -> {field}")
                    return False

                payload[field] = field_value

            print("🔎 API: All required fields present")

            # ---------- VALIDATE DATE FORMATS ----------
            try:
                datetime.datetime.strptime(payload["DOB"], "%d/%m/%Y")
                datetime.datetime.strptime(payload["ExpiryDate"], "%d/%m/%Y")
            except ValueError:
                print(f"❌ API: Invalid date format. Expected DD/MM/YYYY")
                return False

            # ---------- CALL LICENSE VERIFICATION API ----------
            print(f"🌐 API: Connecting to {LICENSE_API_ENDPOINT}...")
            print(f"⏱️  API: Request started at {datetime.datetime.now().strftime('%H:%M:%S')}")

            response = _session.post(
                LICENSE_API_ENDPOINT,
                json=payload,
                timeout=API_TIMEOUT
            )

            api_elapsed = time.time() - api_start_time

            # ---------- PROCESS RESPONSE ----------
            if response.status_code == 200:
                api_response = response.json()

                if api_response.get("success"):
                    print(f"✅ API: {api_response.get('message', 'License verified successfully')}")
                    print(f"⏱️  API: Request completed in {api_elapsed:.2f}s")
                    return True
                else:
                    print(f"❌ API: {api_response.get('message', 'License verification failed')}")
                    print(f"⏱️  API: Request completed in {api_elapsed:.2f}s")
                    return False
            else:
                print(f"❌ API: Request failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                print(f"⏱️  API: Request completed in {api_elapsed:.2f}s")
                return False

        except requests.exceptions.ConnectionError:
            api_elapsed = time.time() - api_start_time
            print(f"❌ API: Cannot connect to {LICENSE_API_ENDPOINT}")
            print(f"   Ensure the License Verification API is running on port 5000")
            print(f"⏱️  API: Request failed after {api_elapsed:.2f}s")
            return False

        except requests.exceptions.Timeout:
            api_elapsed = time.time() - api_start_time
            print(f"❌ API: Request timeout (>{API_TIMEOUT}s)")
            print(f"⏱️  API: Request timed out after {api_elapsed:.2f}s")
            return False

        except requests.exceptions.RequestException as e:
            api_elapsed = time.time() - api_start_time
            print(f"❌ API: Request error: {e}")
            print(f"⏱️  API: Request failed after {api_elapsed:.2f}s")
            return False

        except Exception as e:
            api_elapsed = time.time() - api_start_time
            print(f"⚠️ API error: {e}")
            print(f"⏱️  API: Error occurred after {api_elapsed:.2f}s")
            return False

        finally:
            print("🔓 API: Lock released - other code can now execute")
            print("━" * 60)