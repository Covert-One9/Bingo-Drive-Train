import time
from machine import Pin, I2C
import math


class PCA9685:
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06

    def __init__(self, address=0x40, debug=False):
        self.i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=100000)
        self.address = address
        self.debug = debug

        if self.debug:
            print("Resetting PCA9685")

        self.write(self.__MODE1, 0x00)

    def write(self, cmd, value):
        self.i2c.writeto_mem(self.address, cmd, bytes([value]))
        if self.debug:
            print(f"I2C Write: reg=0x{cmd:02X}, value=0x{value:02X}")

    def read(self, reg):
        data = self.i2c.readfrom_mem(self.address, reg, 1)
        return data[0]

    def setPWMFreq(self, freq):
        prescaleval = 25000000.0
        prescaleval /= 4096.0
        prescaleval /= float(freq)
        prescaleval -= 1.0

        prescale = int(math.floor(prescaleval + 0.5))

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10  # sleep

        self.write(self.__MODE1, newmode)
        self.write(self.__PRESCALE, prescale)
        self.write(self.__MODE1, oldmode)

        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

        if self.debug:
            print(f"PWM frequency set to {freq} Hz")

    def setPWM(self, channel, on, off):
        base = self.__LED0_ON_L + 4 * channel
        self.write(base, on & 0xFF)
        self.write(base + 1, on >> 8)
        self.write(base + 2, off & 0xFF)
        self.write(base + 3, off >> 8)

    def setDuty(self, channel, percent):
        percent = max(0, min(100, percent))
        value = int(percent * 4095 / 100)
        self.setPWM(channel, 0, value)

    def setLevel(self, channel, value):
        if value:
            self.setPWM(channel, 0, 4095)
        else:
            self.setPWM(channel, 0, 0)


class MotorDriver:
    def __init__(self, debug=False):
        self.debug = debug

        self.pwm = PCA9685(debug=debug)
        self.pwm.setPWMFreq(1000)  # ✅ Good for DC motors

        # Motor mapping: PWM, IN1, IN2
        self.MotorPin = {
            'MA': (0, 1, 2),
            'MB': (3, 4, 5),
            'MC': (6, 7, 8),
            'MD': (9, 10, 11)
        }

        # Direction mapping
        self.MotorDir = {
            'forward': (0, 1),
            'backward': (1, 0)
        }

    def MotorRun(self, motor, mdir, speed):
        if motor not in self.MotorPin:
            raise ValueError("Invalid motor")
        if mdir not in self.MotorDir:
            raise ValueError("Invalid direction")

        pwm_pin, in1, in2 = self.MotorPin[motor]
        dir1, dir2 = self.MotorDir[mdir]

        if self.debug:
            print(f"{motor} -> PWM:{pwm_pin}, IN1:{in1}, IN2:{in2}")
            print(f"Direction: {mdir}, Speed: {speed}%")

        self.pwm.setDuty(pwm_pin, speed)
        self.pwm.setLevel(in1, dir1)
        self.pwm.setLevel(in2, dir2)

    def MotorStop(self, motor):
        if motor not in self.MotorPin:
            return

        pwm_pin, in1, in2 = self.MotorPin[motor]

        self.pwm.setDuty(pwm_pin, 0)
        self.pwm.setLevel(in1, 0)
        self.pwm.setLevel(in2, 0)


# =========================
# TEST CODE
# =========================
if __name__ == '__main__':
    m = MotorDriver(debug=True)

    print("Motor driver test")

    try:
        print("Motor A forward at 100% for 2 seconds")

        m.MotorRun('MA', 'forward', 100)
        time.sleep(2)  # ✅ timing handled here
        m.MotorStop('MA')

        time.sleep(1)

        print("Motor B foreward at 100% for 2 seconds")

        m.MotorRun('MB', 'backward', 100)
        time.sleep(2)
        m.MotorStop('MB')
        
        time.sleep(1)
        
        print("Motor C forward at 100% for 2 seconds")
        
        m.MotorRun('MC', 'backward', 100)
        time.sleep(3)
        m.MotorStop('MC')
        
        time.sleep(1)

        print("Motor D forward at 100% for 2 seconds")
        
        m.MotorRun('MD', 'backward', 100)
        time.sleep(3)
        m.MotorStop('MD')

    except KeyboardInterrupt:
        print("Stopped")
        
        m.MotorStop('MD')
        
