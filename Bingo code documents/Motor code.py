import time
from machine import Pin, I2C
import math
<<<<<<< Updated upstream


=======
from machine import Pin, I2C, SoftI2C, time_pulse_us



# ============================================================
# PCA9685 PWM CONTROLLER
# ============================================================

>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
        self.write(self.__MODE1, 0x00)
=======
        self.write(self.MODE1, 0x00)

    def write(self, register, value):
        self.i2c.writeto_mem(
            self.address,
            register,
            bytes([value & 0xFF])
        )
>>>>>>> Stashed changes

    def write(self, cmd, value):
        self.i2c.writeto_mem(self.address, cmd, bytes([value]))
        if self.debug:
<<<<<<< Updated upstream
            print(f"I2C Write: reg=0x{cmd:02X}, value=0x{value:02X}")

    def read(self, reg):
        data = self.i2c.readfrom_mem(self.address, reg, 1)
        return data[0]
=======
            print(
                "I2C Write: reg=0x{:02X}, value=0x{:02X}".format(
                    register, value
                )
            )

    def read(self, register):
        return self.i2c.readfrom_mem(
            self.address, register, 1
        )[0]
>>>>>>> Stashed changes

    def setPWMFreq(self, freq):
        if freq <= 0:
            raise ValueError("PWM frequency must be positive")

        prescaleval = 25000000.0
        prescaleval /= 4096.0
        prescaleval /= float(freq)
        prescaleval -= 1.0

        prescale = int(math.floor(prescaleval + 0.5))
        prescale = max(3, min(255, prescale))

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10  # sleep

<<<<<<< Updated upstream
        self.write(self.__MODE1, newmode)
        self.write(self.__PRESCALE, prescale)
        self.write(self.__MODE1, oldmode)

        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)
=======
        # Enter sleep mode
        self.write(self.MODE1, newmode)

        # Set PWM prescaler
        self.write(self.PRESCALE, prescale)

        # Restore previous mode
        self.write(self.MODE1, oldmode)
        time.sleep_ms(5)

        # Restart oscillator
        self.write(self.MODE1, oldmode | 0x80)
>>>>>>> Stashed changes

        if self.debug:
            actual_freq = 25000000 / (4096 * (prescale + 1))
            print("PWM frequency: {:.1f} Hz".format(actual_freq))

    def setPWM(self, channel, on, off):
<<<<<<< Updated upstream
        base = self.__LED0_ON_L + 4 * channel
        self.write(base, on & 0xFF)
        self.write(base + 1, on >> 8)
        self.write(base + 2, off & 0xFF)
        self.write(base + 3, off >> 8)
=======
        if not 0 <= channel <= 15:
            raise ValueError("PCA9685 channel must be 0-15")

        base = self.LED0_ON_L + (4 * channel)

        self.write(base, on & 0xFF)
        self.write(base + 1, (on >> 8) & 0x0F)
        self.write(base + 2, off & 0xFF)
        self.write(base + 3, (off >> 8) & 0x0F)
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        self.pwm.setPWMFreq(1000)  # ✅ Good for DC motors

        # Motor mapping: PWM, IN1, IN2
=======
        self.pwm.setPWMFreq(1000)

        # Motor: (PWM channel, IN1 channel, IN2 channel)
>>>>>>> Stashed changes
        self.MotorPin = {
            "MA": (0, 1, 2),
            "MB": (3, 4, 5),
            "MC": (6, 7, 8),
            "MD": (9, 10, 11)
        }

        # Direction mapping
        self.MotorDir = {
            "forward": (0, 1),
            "backward": (1, 0)
        }

<<<<<<< Updated upstream
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
=======
        # Ensure all motors start stopped
        self.ALLMotorStop()

    def MotorRun(self, motor, direction, speed):
        if motor not in self.MotorPin:
            raise ValueError("Invalid motor: " + str(motor))

        if direction not in self.MotorDir:
            raise ValueError("Invalid direction: " + str(direction))

        pwm_pin, in1, in2 = self.MotorPin[motor]
        dir1, dir2 = self.MotorDir[direction]

        speed = max(0, min(100, speed))

        if self.debug:
            print(
                "{}: direction={}, speed={}%".format(
                    motor, direction, speed
                )
            )

        # Set direction before applying motor power
        self.pwm.setLevel(in1, dir1)
        self.pwm.setLevel(in2, dir2)
        self.pwm.setDuty(pwm_pin, speed)
>>>>>>> Stashed changes

    def MotorStop(self, motor):
        if motor not in self.MotorPin:
            return

        pwm_pin, in1, in2 = self.MotorPin[motor]

        self.pwm.setDuty(pwm_pin, 0)
        self.pwm.setLevel(in1, 0)
        self.pwm.setLevel(in2, 0)

<<<<<<< Updated upstream

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
=======
    def ALLMotorGo(self, speed):
        for motor in ("MA", "MB", "MC", "MD"):
            self.MotorRun(motor, "forward", speed)

    def ALLMotorReverse(self, speed):
        for motor in ("MA", "MB", "MC", "MD"):
            self.MotorRun(motor, "backward", speed)

    def ALLMotorStop(self):
        for motor in ("MA", "MB", "MC", "MD"):
            self.MotorStop(motor)

    def MotorTurnLeft(self, speed):
        self.MotorRun("MA", "backward", speed)
        self.MotorRun("MB", "forward", speed)
        self.MotorRun("MC", "backward", speed)
        self.MotorRun("MD", "forward", speed)

    def MotorTurnRight(self, speed):
        self.MotorRun("MA", "forward", speed)
        self.MotorRun("MB", "backward", speed)
        self.MotorRun("MC", "forward", speed)
        self.MotorRun("MD", "backward", speed)


# ============================================================
# ULTRASONIC SENSOR
# ============================================================

class UltrasonicSensor:

    def __init__(self, trigPin=9, echoPin=8):
        self.trig = Pin(trigPin, Pin.OUT)
        self.echo = Pin(echoPin, Pin.IN)

        self.trig.value(0)
        time.sleep_ms(2)

    def measure_distance(self):
        self.trig.value(0)
        time.sleep_us(2)

        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        try:
            duration = time_pulse_us(
                self.echo,
                1,
                30000
            )
        except Exception:
            return None

        if duration < 0:
            return None

        return (duration * 0.0343) / 2


# ============================================================
# LCD DISPLAY
# ============================================================

class LCD_Display:

    I2C_ADDR = 0x27
    I2C_NUM_ROWS = 2
    I2C_NUM_COLS = 16

    def __init__(self):
        self.i2c = SoftI2C(
            sda=Pin(4),
            scl=Pin(5),
            freq=100000
        )

        devices = self.i2c.scan()
        print("LCD I2C devices:", devices)

        if self.I2C_ADDR not in devices:
            raise OSError(
                "LCD not found at address 0x27. "
                "Check wiring and I2C address."
            )

        self.lcd = I2cLcd(
            self.i2c,
            self.I2C_ADDR,
            self.I2C_NUM_ROWS,
            self.I2C_NUM_COLS
        )

    def display_message(self, message, line=0):
        if line < 0 or line >= self.I2C_NUM_ROWS:
            raise ValueError("Invalid LCD line number")

        self.lcd.move_to(0, line)

        text = str(message)[:self.I2C_NUM_COLS].ljust(
            self.I2C_NUM_COLS
        )

        self.lcd.putstr(text)

    def clear(self):
        self.lcd.clear()


# ============================================================
# LCD TEST
# ============================================================

def test_display():
    lcd = LCD_Display()

    try:
        while True:
            lcd.clear()
            lcd.display_message("Hello, World!", 0)
            lcd.display_message("Distance: 10cm", 1)
            time.sleep(2)

            lcd.clear()
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting display test.")

    finally:
        lcd.clear()


# ============================================================
# COURSE MODE
# ============================================================

def course_mode(motor, ultrasonic_sensor):
    print("Course mode activated.")

    try:
        # Drive forward at half speed
        distance = ultrasonic_sensor.measure_distance()

        if distance is None or distance < 10:
            print("Obstacle detected or sensor timeout.")
            return

        motor.ALLMotorGo(50)
        time.sleep(2)
        motor.ALLMotorStop()
        time.sleep_ms(300)

        # Turn left
        motor.MotorTurnLeft(50)
        time.sleep(1)
        motor.ALLMotorStop()
        time.sleep_ms(300)

        # Check for an obstacle before continuing
        distance = ultrasonic_sensor.measure_distance()

        if distance is None or distance < 10:
            print("Obstacle detected or sensor timeout.")
            return

        # Continue forward
        motor.ALLMotorGo(50)
        time.sleep(5)

    except KeyboardInterrupt:
        print("Course mode interrupted.")

    finally:
        motor.ALLMotorStop()
        print("Course mode finished. Motors stopped.")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    motor = None

    print("Starting robot...")

    try:
        # Initialize motor driver
        motor = MotorDriver(debug=True)

        # Initialize ultrasonic sensor
        ultrasonic_sensor = UltrasonicSensor(
            trigPin=9,
            echoPin=8
        )

        print("Robot ready.")

        while True:
            user_input = input(
                "\nEnter command "
                "(go, stop, left, right, reverse, "
                "distance, test_display, course, quit): "
            )
>>>>>>> Stashed changes

        print("Motor B foreward at 100% for 2 seconds")

<<<<<<< Updated upstream
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
        
=======
            # ------------------------------------------------
            # GO
            # ------------------------------------------------
            if command == "go":
                distance = ultrasonic_sensor.measure_distance()

                print("Distance:", distance, "cm")

                if distance is None:
                    print("Sensor timeout. Stopping for safety.")
                    motor.ALLMotorStop()

                elif distance < 10:
                    print("Obstacle detected! Stopping motors.")
                    motor.ALLMotorStop()

                else:
                    print("Going forward!")
                    motor.ALLMotorGo(100)

            # ------------------------------------------------
            # STOP
            # ------------------------------------------------
            elif command == "stop":
                print("Stopping!")
                motor.ALLMotorStop()

            # ------------------------------------------------
            # TURN LEFT
            # ------------------------------------------------
            elif command == "left":
                print("Turning left!")
                motor.MotorTurnLeft(100)

            # ------------------------------------------------
            # TURN RIGHT
            # ------------------------------------------------
            elif command == "right":
                print("Turning right!")
                motor.MotorTurnRight(100)

            # ------------------------------------------------
            # REVERSE
            # ------------------------------------------------
            elif command == "reverse":
                print("Reversing!")
                motor.ALLMotorReverse(100)

            # ------------------------------------------------
            # DISTANCE
            # ------------------------------------------------
            elif command == "distance":
                distance = ultrasonic_sensor.measure_distance()

                if distance is None:
                    print("Ultrasonic sensor timeout.")
                else:
                    print("Distance: {:.2f} cm".format(distance))

            # ------------------------------------------------
            # TEST LCD
            # ------------------------------------------------
            elif command == "test_display":
                print("LCD test activated.")
                test_display()

            # ------------------------------------------------
            # COURSE MODE
            # ------------------------------------------------
            elif command == "course":
                course_mode(motor, ultrasonic_sensor)

            # ------------------------------------------------
            # QUIT
            # ------------------------------------------------
            elif command == "quit":
                print("Stopping robot.")
                break

            # ------------------------------------------------
            # UNKNOWN COMMAND
            # ------------------------------------------------
            else:
                print(
                    "Unknown command. Use go, stop, left, right, "
                    "reverse, distance, test_display, course, or quit."
                )

    except KeyboardInterrupt:
        print("\nProgram interrupted.")

    except Exception as error:
        print("Program error:", error)

    finally:
        if motor is not None:
            try:
                motor.ALLMotorStop()
                print("Motors stopped.")
            except Exception as stop_error:
                print("Could not stop motors:", stop_error)


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
