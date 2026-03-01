# session_logger.py
import json
import os
from datetime import datetime


class SessionLogger:
    def __init__(self, session_base_path):
        """
        session_base_path: data/sessions/session_xxx/
        """
        self.log_path = os.path.join(session_base_path, "session_result.json")
        self.data = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "final_decision": None
        }

    def log_check(self, name, status, details=None):
        """
        name: str (e.g., 'ocr', 'face_match')
        status: bool
        details: optional dict
        """
        self.data["checks"][name] = {
            "status": bool(status),
            "details": details
        }

    def log_error(self, name, exc):
        """Convenience: record a failure with exception details."""
        self.log_check(name, False, {"error": str(exc)})

    def set_final_decision(self, decision):
        self.data["final_decision"] = bool(decision)

    def write(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            print(f"📝 Session log written: {self.log_path}")
        except Exception as e:
            print(f"⚠️ Failed to write session log: {e}")
