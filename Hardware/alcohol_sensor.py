# alcohol_sensor.py

import spidev
import time


class AlcoholSensor:
    """
    MQ-3 Alcohol Sensor with Raspberry Pi

    Connections:

    MQ3 Sensor:
        VCC -> 5V (Pin 2)
        GND -> GND (Pin 6)
        D0  -> GPIO17 (Pin 11)
        A0  -> MCP3208 CH0

    MCP3208 ADC Converter (SPI):

        VDD  -> 3.3V (Pin 1)
        VREF -> 3.3V (Pin 1)
        AGND -> GND (Pin 6)
        DGND -> GND (Pin 6)

        CLK  -> GPIO11 (Pin 23)
        DOUT -> GPIO9  (Pin 21)
        DIN  -> GPIO10 (Pin 19)
        CS   -> GPIO8  (Pin 24)

    """

    def __init__(self, channel=0, threshold=800, warmup=True):

        self.channel = channel
        self.threshold = threshold

        try:
            # Initialize SPI
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)  # Bus 0, Device 0 (CE0 -> GPIO8)

            self.spi.max_speed_hz = 1350000

            print("✅ MCP3208 SPI initialized")
            print(f"✅ Alcohol sensor connected on CH{self.channel}")

        except Exception as e:
            print(f"⚠️ SPI init error: {e}")

        # MQ3 warmup
        if warmup:
            print("🔥 Alcohol sensor warming up (20 seconds)...")
            time.sleep(20)
            print("✅ Alcohol sensor ready")

    def read_adc(self, channel):

        """
        Read raw value from MCP3208 channel
        """

        if channel < 0 or channel > 7:
            return -1

        try:
            cmd = 0b11000000 | ((channel & 0x07) << 3)
            adc = self.spi.xfer2([cmd, 0x00, 0x00])

            value = ((adc[1] & 0x0F) << 8) | adc[2]

            return value

        except Exception as e:
            print(f"⚠️ ADC read error: {e}")
            return None

    def read_value(self):
        """
        Read alcohol sensor analog value
        """

        value = self.read_adc(self.channel)

        return value

    def is_alcohol_detected(self):
        """
        Returns:
        (True/False, raw_value)
        """

        try:

            value = self.read_value()

            if value is None:
                return False, None

            # Compare with threshold
            if value > self.threshold:
                return True, value
            else:
                return False, value

        except Exception as e:
            print(f"⚠️ Alcohol detection error: {e}")
            return False, None

    def close(self):

        try:
            self.spi.close()
        except Exception:
            pass