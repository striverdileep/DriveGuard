# alcohol_sensor.py
import spidev
import time

class AlcoholSensor:
    def __init__(self, channel=0, warmup=True):
        self.channel = channel
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 1350000

        if warmup:
            print("🔥 Alcohol sensor warming up (20s)...")
            time.sleep(20)

    def read_adc(self):
        adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
        return ((adc[1] & 3) << 8) + adc[2]

    def is_alcohol_detected(self, threshold=450):
        value = self.read_adc()
        return value >= threshold, value

    def close(self):
        self.spi.close()
