# ignition_control.py
import RPi.GPIO as GPIO
import time

class IgnitionController:
    """
    Controls ignition using a relay via GPIO.
    FAIL-SAFE DESIGN:
    - GPIO LOW  -> Ignition BLOCKED
    - GPIO HIGH -> Ignition ALLOWED
    """

    def __init__(self, pin=17):
        """
        pin: GPIO pin connected to relay IN pin
        """
        self.pin = pin

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)

            # FAIL-SAFE DEFAULT
            GPIO.output(self.pin, GPIO.LOW)  # ignition blocked
            print("🔒 Ignition BLOCKED (default state)")
        except Exception as e:
            print(f"⚠️ IgnitionController init error: {e}")

    def allow_ignition(self):
        try:
            GPIO.output(self.pin, GPIO.HIGH)
            print("✅ Ignition ALLOWED")
        except Exception as e:
            print(f"⚠️ Ignition allow error: {e}")

    def block_ignition(self):
        try:
            GPIO.output(self.pin, GPIO.LOW)
            print("❌ Ignition BLOCKED")
        except Exception as e:
            print(f"⚠️ Ignition block error: {e}")

    def cleanup(self):
        """
        Ensure ignition is blocked and GPIO is cleaned up
        """
        try:
            GPIO.output(self.pin, GPIO.LOW)
            GPIO.cleanup()
            print("🧹 GPIO cleaned, ignition safely blocked")
        except Exception as e:
            print(f"⚠️ Ignition cleanup error: {e}")
