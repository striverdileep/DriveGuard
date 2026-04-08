import RPi.GPIO as GPIO
import time


class IgnitionSwitch:

    def __init__(self, pin=24):

        self.pin = pin

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print(f"🔧 Ignition button initialized on GPIO {self.pin}")


    def wait_for_on(self):

        print("🔑 Waiting for ignition button press...")

        while True:

            if GPIO.input(self.pin) == GPIO.LOW:

                print("🔑 Button pressed")

                time.sleep(0.4)

                while GPIO.input(self.pin) == GPIO.LOW:
                    time.sleep(0.05)

                time.sleep(0.3)

                return True


    # ✅ ADD THIS (FIX)
    def wait_for_press(self):
        return self.wait_for_on()


    def wait_for_off(self):

        print("⏹ Waiting for button release...")

        while True:

            if GPIO.input(self.pin) == GPIO.HIGH:
                print("⏹ Button released")

                time.sleep(1)

                if GPIO.input(self.pin) == GPIO.HIGH:
                    return True

            time.sleep(0.05)


    def cleanup(self):

        try:
            GPIO.cleanup(self.pin)
            print("🧹 Ignition switch GPIO cleaned")
        except:
            pass
