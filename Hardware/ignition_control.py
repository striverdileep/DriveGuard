# ignition_control.py

import RPi.GPIO as GPIO
import time


class IgnitionController:
    """
    Controls:
    - Relay (ignition)
    - Buzzer
    - Green LED
    - Red LED
    """

    def __init__(
        self,
        relay_pin=25,
        buzzer_pin=23,
        green_led=22,
        red_led=27
    ):

        self.relay_pin = relay_pin
        self.buzzer_pin = buzzer_pin
        self.green_led = green_led
        self.red_led = red_led

        self.initialized = False

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            # Setup pins
            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            GPIO.setup(self.green_led, GPIO.OUT)
            GPIO.setup(self.red_led, GPIO.OUT)

            # Initial safe state
            self._safe_reset()

            self.initialized = True
            print("🔒 System initialized → Ignition BLOCKED")

        except Exception as e:
            print(f"⚠️ IgnitionController init error: {e}")

    # ---------------- SAFE RESET ----------------
    def _safe_reset(self):
        GPIO.output(self.relay_pin, GPIO.LOW)
        GPIO.output(self.buzzer_pin, GPIO.LOW)
        GPIO.output(self.green_led, GPIO.LOW)
        GPIO.output(self.red_led, GPIO.HIGH)  # red ON = blocked

    # ---------------- IGNITION ALLOW ----------------
    def allow_ignition(self):
        try:
            if not self.initialized:
                return

            GPIO.output(self.relay_pin, GPIO.HIGH)
            GPIO.output(self.green_led, GPIO.HIGH)
            GPIO.output(self.red_led, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)

            print("🟢 IGNITION ENABLED")

        except Exception as e:
            print(f"⚠️ Ignition allow error: {e}")

    # ---------------- IGNITION BLOCK ----------------
    def block_ignition(self):
        try:
            if not self.initialized:
                return

            GPIO.output(self.relay_pin, GPIO.LOW)
            GPIO.output(self.green_led, GPIO.LOW)
            GPIO.output(self.red_led, GPIO.HIGH)

            print("🔴 IGNITION BLOCKED")

            # 🔔 Buzzer pattern
            for _ in range(3):
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.3)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                time.sleep(0.2)

        except Exception as e:
            print(f"⚠️ Ignition block error: {e}")

    # ---------------- CONTINUOUS ALARM ----------------
    def alarm_continuous(self, duration=4):
        try:
            if not self.initialized:
                return

            end_time = time.time() + duration

            while time.time() < end_time:
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Alarm error: {e}")

    # ---------------- CLEANUP ----------------
    def cleanup(self):
        try:
            if not self.initialized:
                return

            # Turn everything OFF before cleanup
            GPIO.output(self.relay_pin, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            GPIO.output(self.green_led, GPIO.LOW)
            GPIO.output(self.red_led, GPIO.LOW)

            GPIO.cleanup()

            print("🧹 GPIO cleaned (all devices OFF)")

        except Exception as e:
            print(f"⚠️ Ignition cleanup error: {e}")
