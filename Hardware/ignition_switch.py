# ignition_switch.py

import RPi.GPIO as GPIO
import time


class IgnitionSwitch:
    """
    Push button ignition trigger

    Connections:

    Push Button (Momentary Switch):

        Button Pin 1 -> GPIO24 (Pin 18)
        Button Pin 2 -> GND (Pin 20)

    Internal pull-up resistor is used.

    Logic:
        NOT PRESSED → GPIO HIGH
        PRESSED     → GPIO LOW
    """

    def __init__(self, pin=24):

        self.pin = pin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Internal pull-up resistor
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print(f"🔧 Ignition button initialized on GPIO {self.pin}")


    def wait_for_on(self):

        print("🔑 Waiting for ignition button press...")

        while True:

            if GPIO.input(self.pin) == GPIO.LOW:

                print("🔑 Button pressed")

                # debounce delay
                time.sleep(0.4)

                # wait until button released
                while GPIO.input(self.pin) == GPIO.LOW:
                    time.sleep(0.05)

                # extra debounce
                time.sleep(0.3)

                return True


    def wait_for_off(self):
        """
        Wait until button released
        """

        print("⏹ Waiting for button release...")

        while True:

            state = GPIO.input(self.pin)

            if state == GPIO.HIGH:
                print("⏹ Button released")

                time.sleep(1)

                if GPIO.input(self.pin) == GPIO.HIGH:
                    return True

            time.sleep(0.05)


    def cleanup(self):
        """
        Cleanup GPIO for this pin
        """

        try:
            GPIO.cleanup(self.pin)
            print("🧹 Ignition switch GPIO cleaned")
        except:
            pass