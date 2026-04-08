import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.OUT)

GPIO.output(22, GPIO.HIGH)
print("LED ON")
time.sleep(5)

GPIO.output(22, GPIO.LOW)
print("LED OFF")

GPIO.cleanup()
