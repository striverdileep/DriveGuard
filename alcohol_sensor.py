# alcohol_sensor.py
import spidev
import time

class AlcoholSensor:
    def __init__(self, channel=0, warmup=True):
        self.channel = channel
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 1350000
        except Exception as e:
            print(f"⚠️ AlcoholSensor init error: {e}")
            self.spi = None

        if warmup and self.spi is not None:
            print("🔥 Alcohol sensor warming up (20s)...")
            try:
                time.sleep(20)
            except Exception:
                pass

    def read_adc(self):
        if self.spi is None:
            raise RuntimeError("SPI device not initialized")
        try:
            adc = self.spi.xfer2([1, (8 + self.channel) << 4, 0])
            return ((adc[1] & 3) << 8) + adc[2]
        except Exception as e:
            print(f"⚠️ AlcoholSensor read error: {e}")
            return None

    def is_alcohol_detected(self, threshold=450):
        try:
            value = self.read_adc()
            if value is None:
                return False, None
            return value >= threshold, value
        except Exception as e:
            print(f"⚠️ AlcoholSensor detection error: {e}")
            return False, None

    def close(self):
        try:
            if self.spi:
                self.spi.close()
        except Exception:
            pass
