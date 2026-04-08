# session_logger.py

import json
import os
from datetime import datetime


class SessionLogger:
    def __init__(self, session_base_path="data/sessions"):
        """
        Creates:
        data/sessions/session_xxx/
            ├── images/
            └── session_result.json
        """

        # Create unique session folder
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_path = os.path.join(session_base_path, f"session_{timestamp}")

        self.images_path = os.path.join(self.session_path, "images")
        os.makedirs(self.images_path, exist_ok=True)

        # Log file path
        self.log_path = os.path.join(self.session_path, "session_result.json")

        # Data structure
        self.data = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "final_decision": None
        }

        print(f"📁 Session created: {self.session_path}")

    # ---------------- IMAGE PATH ----------------
    def get_image_path(self, filename):
        return os.path.join(self.images_path, filename)

    # ---------------- LOG CHECK ----------------
    def log_check(self, name, status, details=None):
        self.data["checks"][name] = {
            "status": bool(status),
            "details": details
        }

    # ---------------- LOG ERROR ----------------
    def log_error(self, name, exc):
        self.log_check(name, False, {"error": str(exc)})

    # ---------------- FINAL DECISION ----------------
    def set_final_decision(self, decision):
        self.data["final_decision"] = bool(decision)

    # ---------------- SAVE ----------------
    def write(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)

            print(f"📝 Session log written: {self.log_path}")

        except Exception as e:
            print(f"⚠️ Failed to write session log: {e}")
