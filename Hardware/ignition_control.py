# ignition_control.py

import RPi.GPIO as GPIO


class IgnitionController:
    """
    Controls ignition system including:
    - Relay (vehicle ignition)
    - Buzzer
    - Green LED
    - Red LED

    Connections:

    Relay Module:
        IN  -> GPIO25 (Pin 22)
        VCC -> 5V
        GND -> GND

    Buzzer:
        + -> GPIO23 (Pin 16)
        - -> GND

    Green LED:
        + -> GPIO22 (Pin 15) through 220Ω resistor
        - -> GND

    Red LED:
        + -> GPIO27 (Pin 13) through 220Ω resistor
        - -> GND
    """

    def __init__(
        self,
        relay_pin=25,      # GPIO25 (Pin 22)
        buzzer_pin=23,     # GPIO23 (Pin 16)
        green_led=22,      # GPIO22 (Pin 15)
        red_led=27         # GPIO27 (Pin 13)
    ):

        self.relay_pin = relay_pin
        self.buzzer_pin = buzzer_pin
        self.green_led = green_led
        self.red_led = red_led

        try:
            GPIO.setmode(GPIO.BCM)

            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            GPIO.setup(self.green_led, GPIO.OUT)
            GPIO.setup(self.red_led, GPIO.OUT)

            # Default FAIL SAFE STATE
            GPIO.output(self.relay_pin, GPIO.LOW)   # ignition OFF
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            GPIO.output(self.green_led, GPIO.LOW)
            GPIO.output(self.red_led, GPIO.HIGH)

            print("🔒 System initialized → Ignition BLOCKED")

        except Exception as e:
            print(f"⚠️ IgnitionController init error: {e}")

    def allow_ignition(self):
        """
        Driver is valid → start vehicle
        """

        try:
            GPIO.output(self.relay_pin, GPIO.HIGH)
            GPIO.output(self.green_led, GPIO.HIGH)
            GPIO.output(self.red_led, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)

            print("✅ IGNITION ALLOWED")

        except Exception as e:
            print(f"⚠️ Ignition allow error: {e}")

    def block_ignition(self):
        """
        Driver invalid → block vehicle
        """

        try:
            GPIO.output(self.relay_pin, GPIO.LOW)
            GPIO.output(self.green_led, GPIO.LOW)
            GPIO.output(self.red_led, GPIO.HIGH)

            # buzzer alert
            GPIO.output(self.buzzer_pin, GPIO.HIGH)

            print("❌ IGNITION BLOCKED")

        except Exception as e:
            print(f"⚠️ Ignition block error: {e}")

    def cleanup(self):
        """
        Clean GPIO safely
        """

        try:
            GPIO.output(self.relay_pin, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            GPIO.cleanup()

            print("🧹 GPIO cleaned")

        except Exception as e:
            print(f"⚠️ Ignition cleanup error: {e}")