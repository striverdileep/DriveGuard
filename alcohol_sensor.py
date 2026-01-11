# alcohol_sensor.py
import spidev
import time


class AlcoholSensor:
    def __init__(self, channel=0):
        """
        channel: MCP3008 channel (0–7)
        """
        self.channel = channel
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)   # SPI bus 0, CE0
        self.spi.max_speed_hz = 1350000

        # MQ-3 needs warm-up
        print("🔥 Warming up alcohol sensor (20 sec)...")
        time.sleep(20)

    def read_adc(self):
        """
        Reads raw ADC value from MCP3008
        """
        adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
        value = ((adc[1] & 3) << 8) + adc[2]
        return value

    def is_alcohol_detected(self, threshold=450):
        """
        Returns (detected: bool, value: int)
        """
        value = self.read_adc()
        detected = value >= threshold
        return detected, value

    def close(self):
        self.spi.close()
