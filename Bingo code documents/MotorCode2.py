import time
import math
import machine 
from machine import Pin, I2C #ignore 


# ============================================================
# PCA9685
# ============================================================

class PCA9685:
    MODE1 = 0x00
    PRESCALE = 0xFE
    LED0_ON_L = 0x06

    def __init__(self, address=0x40, debug=False):
        self.i2c = I2C(
            0,
            scl=Pin(21),
            sda=Pin(20),
            freq=100000
        )

        self.address = address
        self.debug = debug

        if self.debug:
            print("Resetting PCA9685")

        self.write(self.MODE1, 0x00)

    def write(self, register, value):
        self.i2c.writeto_mem(
            self.address,
            register,
            bytes([value])
        )

        if self.debug:
            print(
                f"I2C Write: reg=0x{register:02X}, "
                f"value=0x{value:02X}"
            )

    def read(self, register):
        data = self.i2c.readfrom_mem(
            self.address,
            register,
            1
        )

        return data[0]

    def setPWMFreq(self, freq):
        prescaleval = 25000000.0
        prescaleval /= 4096.0
        prescaleval /= float(freq)
        prescaleval -= 1.0

        prescale = int(math.floor(prescaleval + 0.5))

        oldmode = self.read(self.MODE1)
        newmode = (oldmode & 0x7F) | 0x10

        # Sleep
        self.write(self.MODE1, newmode)

        # Set prescaler
        self.write(self.PRESCALE, prescale)

        # Wake up
        self.write(self.MODE1, oldmode)

        time.sleep_ms(5)

        # Restart
        self.write(self.MODE1, oldmode | 0x80)

        if self.debug:
            print(f"PWM frequency set to {freq} Hz")

    def setPWM(self, channel, on, off):
        base = self.LED0_ON_L + (4 * channel)

        self.write(base, on & 0xFF)
        self.write(base + 1, (on >> 8) & 0xFF)

        self.write(base + 2, off & 0xFF)
        self.write(base + 3, (off >> 8) & 0xFF)

    def setDuty(self, channel, percent):
        percent = max(0, min(100, percent))

        value = int(percent * 4095 / 100)

        self.setPWM(channel, 0, value)

    def setLevel(self, channel, value):
        if value:
            self.setPWM(channel, 0, 4095)
        else:
            self.setPWM(channel, 0, 0)


# ============================================================
# MOTOR DRIVER
# ============================================================

class MotorDriver:

    def __init__(self, debug=False):
        self.debug = debug

        self.pwm = PCA9685(debug=debug)

        # 1000 Hz PWM
        self.pwm.setPWMFreq(1000)

        # Motor mapping:
        # motor: (PWM, IN1, IN2)
        self.MotorPin = {
            'MA': (0, 1, 2),
            'MB': (3, 4, 5),
            'MC': (6, 7, 8),
            'MD': (9, 10, 11)
        }

        self.MotorDir = {
            'forward': (0, 1),
            'backward': (1, 0)
        }

    # --------------------------------------------------------
    # Run one motor
    # --------------------------------------------------------

    def MotorRun(self, motor, direction, speed):

        if motor not in self.MotorPin:
            raise ValueError("Invalid motor")

        if direction not in self.MotorDir:
            raise ValueError("Invalid direction")

        pwm_pin, in1, in2 = self.MotorPin[motor]

        dir1, dir2 = self.MotorDir[direction]

        speed = max(0, min(100, speed))

        if self.debug:
            print(
                f"{motor}: direction={direction}, "
                f"speed={speed}%"
            )

        self.pwm.setDuty(pwm_pin, speed)

        self.pwm.setLevel(in1, dir1)
        self.pwm.setLevel(in2, dir2)

    # --------------------------------------------------------
    # Stop one motor
    # --------------------------------------------------------

    def MotorStop(self, motor):

        if motor not in self.MotorPin:
            return

        pwm_pin, in1, in2 = self.MotorPin[motor]

        self.pwm.setDuty(pwm_pin, 0)

        self.pwm.setLevel(in1, 0)
        self.pwm.setLevel(in2, 0)

    # --------------------------------------------------------
    # All motors forward
    # --------------------------------------------------------

    def ALLMotorGo(self, speed):

        self.MotorRun('MA', 'forward', speed)
        self.MotorRun('MB', 'forward', speed)
        self.MotorRun('MC', 'forward', speed)
        self.MotorRun('MD', 'forward', speed)

    # --------------------------------------------------------
    # All motors backward
    # --------------------------------------------------------

    def ALLMotorReverse(self, speed):

        self.MotorRun('MA', 'backward', speed)
        self.MotorRun('MB', 'backward', speed)
        self.MotorRun('MC', 'backward', speed)
        self.MotorRun('MD', 'backward', speed)

    # --------------------------------------------------------
    # Stop all motors
    # --------------------------------------------------------

    def ALLMotorStop(self):

        self.MotorStop('MA')
        self.MotorStop('MB')
        self.MotorStop('MC')
        self.MotorStop('MD')

    # --------------------------------------------------------
    # Turn left
    # --------------------------------------------------------

    def MotorTurnLeft(self, speed):

        self.MotorRun('MA', 'backward', speed)
        self.MotorRun('MB', 'forward', speed)
        self.MotorRun('MC', 'backward', speed)
        self.MotorRun('MD', 'forward', speed)

    # --------------------------------------------------------
    # Turn right
    # --------------------------------------------------------

    def MotorTurnRight(self, speed):

        self.MotorRun('MA', 'forward', speed)
        self.MotorRun('MB', 'backward', speed)
        self.MotorRun('MC', 'forward', speed)
        self.MotorRun('MD', 'backward', speed)


# ============================================================
# ULTRASONIC SENSOR
# ============================================================

class UltrasonicSensor:

    def __init__(self, trigPin=9, echoPin=8):

        self.trig = Pin(trigPin, Pin.OUT)
        self.echo = Pin(echoPin, Pin.IN)

        # Make sure trigger starts LOW
        self.trig.value(0)

    def measure_distance(self):

        # Make sure trigger is LOW
        self.trig.value(0)
        time.sleep_us(2)

        # Send 10 us trigger pulse
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        try:
            # Measure HIGH pulse duration
            duration = machine.time_pulse_us(
                self.echo,  1,  30000
            )

        except Exception as e:
            print("Error measuring distance:", e)
            return None

        # Timeout/error
        if duration < 0:
            return None

        # Speed of sound:
        # approximately 0.0343 cm/us
        distance_cm = (duration * 0.0343) / 2

        return distance_cm
#=============================================================
#LCD Display
#=============================================================
from machine import Pin, SoftI2C
from pico_i2c_lcd import I2cLcd
from time import sleep

class LCD_Display:
    I2C_ADDR = 0x27
    I2C_NUM_ROWS = 2
    I2C_NUM_COLS = 16

    def __init__(self):
        self.12c = SoftI2C
            sda=pin(4)
            scl=pin(5)
            freq=100000
        )
        print("LCD I2C devices", self.i2c.scan())

        self.lcd =I2cLcd(
            self.i2c,
            self.I2c_ADDR,
            self.I2c_NUM_ROWS,
            self.I2c_NUM_COLS
        )

    def display_message(self, message, line=0):
        if line < 0 or line >= self.I2C_NUM_ROWS:
            raise ValueError("Invalid line number")

        self.lcd.move_to(0, line)
        self.lcd.putstr(
            str(message)[:self.I2C_Num_COLS].ljust(
                self.I2C_NUM_C
            )
        )
    def clear(self):
        self.lcd.clear()

#=============================================================
#Test display
#=============================================================
    def test_display():
        lcd = LCD_Display()
        try:
            while True:
                lcd.display_message("Hello, World!", line=0)
                sleep(2)
                lcd.display_message("Distance: 10cm", line=1)
                sleep(2)
                lcd.clear()
                sleep(1)
        except KeyboardInterrupt:
            lcd.clear()
            print("Exiting test display.")




# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("Starting robot...")

    # --------------------------------------------------------
    # Create motor driver
    # --------------------------------------------------------

    motor = MotorDriver(debug=True)

    # --------------------------------------------------------
    # Create ultrasonic sensor
    # --------------------------------------------------------

    ultrasonic_sensor = UltrasonicSensor(
        trigPin=9,
        echoPin=8
    )

    print("Robot ready.")

    try:

        while True:

            command = input(
                "\nEnter command "
                "(go, stop, left, right, reverse, distance, quit, test_display, course): "
            ).strip().lower()

            

            # =================================================
            # GO
            # =================================================

            if command == "go":

                distance = ultrasonic_sensor.measure_distance()

                print("Distance:", distance, "cm")

                if distance is not None and distance < 10:

                    print(
                        "Obstacle detected! "
                        "Stopping motors."
                    )

                    motor.ALLMotorStop()

                else:

                    print("Going forward!")

                    motor.ALLMotorGo(100)

            # =================================================
            # STOP
            # =================================================

            elif command == "stop":

                print("Stopping!")

                motor.ALLMotorStop()

            # =================================================
            # TURN LEFT
            # =================================================

            elif command == "left":

                print("Turning left!")

                motor.MotorTurnLeft(100)

            # =================================================
            # TURN RIGHT
            # =================================================

            elif command == "right":

                print("Turning right!")

                motor.MotorTurnRight(100)

            # =================================================
            # REVERSE
            # =================================================

            elif command == "reverse":

                print("Reversing!")

                motor.ALLMotorReverse(100)

            # =================================================
            # DISTANCE
            # =================================================

            elif command == "distance":

                distance = ultrasonic_sensor.measure_distance()

                if distance is None:
                    print("Ultrasonic sensor timeout.")

                else:
                    print(
                        "Distance:",
                        distance,
                        "cm"
                    )

            # =================================================
            # QUIT
            # =================================================

            elif command == "quit":

                print("Stopping robot.")

                motor.ALLMotorStop()

                break

            # =================================================
            # TEST DISPLAY
            # =================================================

            elif command == "test_display":

                print("Test display activated.")

            # =================================================
            # COURSE MODE
            # =================================================

            elif command == "course":

                course_mode(motor)

            # =================================================
            # UNKNOWN COMMAND
            # =================================================

            else:

                print(
                    "Unknown command. "
                    "Use go, stop, left, right, "
                    "reverse, distance, test_display, or course."
                )

    except KeyboardInterrupt:
        print("\nEmergency stop!")
        motor.ALLMotorStop()

    finally:
        motor.ALLmotorStop()
        print("motors Stopped.")

if __name__ == "__main__":
    main()
#=============================================================
#Couse mode
#=============================================================
def course_mode(motor):
    print("cource mode activated."):

    try:
        motor.ALLMotorGo(100)
        time.sleep(2)

        motor.motorTurnLeft(100)
        time.sleep(1)

        motor.ALLMotorGo(100)
        time.sleep(5)

    finally:
        motor.ALLMotorStop()
        print("Course mode finished. Motors stopped.")

# ============================================================
# Blue tooth control
# ============================================================
import bluetooth
from machine import UART

    # Initialize UART for Bluetooth communication
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

print("Bluetooth control mode activated.")

try:
     while True:
            if uart.any():
                command = uart.readline().decode('utf-8').strip().lower()

                if command == "go":
                    motor.ALLMotorGo(100)
                elif command == "stop":
                    motor.ALLMotorStop()
                elif command == "left":
                    motor.MotorTurnLeft(100)
                elif command == "right":
                    motor.MotorTurnRight(100)
                elif command == "reverse":
                    motor.ALLMotorReverse(100)
                elif command == "distance":
                    distance = ultrasonic_sensor.measure_distance()
                    if distance is not None:
                        uart.write(f"Distance: {distance} cm\n")
                    else:
                        uart.write("Ultrasonic sensor timeout.\n")
                elif command == "quit":
                    motor.ALLMotorStop()
                    break
                else:
                    uart.write("Unknown command.\n")

except KeyboardInterrupt:
    print("\nEmergency stop!")
    motor.ALLMotorStop()