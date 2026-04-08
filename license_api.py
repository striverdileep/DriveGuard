# license_api.py

import os
import threading
import time
import requests
import base64
from typing import Tuple

# ---------------- CONFIG ----------------
LICENSE_API_URL = os.getenv("LICENSE_API_URL", "http://localhost:5000")
LICENSE_API_ENDPOINT = f"{LICENSE_API_URL}/verify-license"
API_TIMEOUT = 10  # seconds

# Thread-safe lock
_api_lock = threading.Lock()

# Session
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})

# ---------------- VERIFY LICENSE ----------------
def verify_license(dl_number: str) -> Tuple[bool, bytes | None]:
    """
    Calls the License API and returns:
    - success (bool) -> True if license is valid
    - db_face_bytes (bytes) -> bytes of DB face image (None if invalid)
    """

    print("🔒 API: Acquiring lock for license verification...")
    with _api_lock:
        print("🔒 API: Lock acquired - starting verification")
        start_time = time.time()

        try:
            if not isinstance(dl_number, str) or not dl_number.strip():
                print("❌ API: Invalid input format")
                return False, None

            payload = {"LicenseNumber": dl_number.strip()}
            print(f"📤 API Payload: {payload}")

            response = _session.post(
                LICENSE_API_ENDPOINT,
                json=payload,
                timeout=API_TIMEOUT
            )

            elapsed = time.time() - start_time

            if response.status_code != 200:
                print(f"❌ API Error: Status {response.status_code}")
                print("Response:", response.text)
                return False, None

            data = response.json()
            success = data.get("success", False)
            db_face_bytes = None

            if success:
                # Decode base64 DB face
                image_base64 = data.get("image")
                if image_base64:
                    try:
                        if image_base64.startswith("data:image"):
                            header, base64_data = image_base64.split(",", 1)
                            db_face_bytes = base64.b64decode(base64_data)
                        else:
                            db_face_bytes = base64.b64decode(image_base64)
                        print("✅ DB face image decoded from API")
                    except Exception as e:
                        print("❌ Error decoding DB face image:", e)
                        db_face_bytes = None
                else:
                    print("⚠️ API returned success but no DB face image")
            else:
                print(f"❌ API: License invalid - {data.get('message', 'Unknown')}")

            print(f"⏱️ API Time: {elapsed:.2f}s")
            return success, db_face_bytes

        except Exception as e:
            print("❌ API Exception:", e)
            return False, None

        finally:
            print("🔓 API: Lock released")
            print("━" * 60)
