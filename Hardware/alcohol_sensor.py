import RPi.GPIO as GPIO
import time


class AlcoholSensor:
    """
    MQ3 Alcohol Sensor using DIGITAL output (D0)

    Connections:

    MQ3 Sensor:
        VCC -> 5V
        GND -> GND
        D0  -> GPIO17
    """

    def __init__(self, pin=17, warmup=True):

        self.pin = pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

        print(f"✅ Alcohol sensor connected on GPIO {self.pin}")

        if warmup:
            print("🔥 Alcohol sensor warming up (20 seconds)...")
            time.sleep(20)
            print("✅ Alcohol sensor ready")

    def is_alcohol_detected(self):
        """
        Returns:
        (True/False, raw_value)
        """

        try:

            state = GPIO.input(self.pin)

            if state == 0:
                return True, 1   # alcohol detected
            else:
                return False, 0  # no alcohol

        except Exception as e:
            print(f"⚠ Alcohol detection error: {e}")
            return False, None

    def close(self):

        try:
            GPIO.cleanup(self.pin)
        except:
            pass