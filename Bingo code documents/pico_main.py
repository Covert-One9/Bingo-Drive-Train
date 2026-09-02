# main.py
# Runs on the Raspberry Pi Pico 2 W
#
# Turns the Pico into a Bluetooth LE peripheral that your computer can
# connect to and control. Uses the standard "Nordic UART Service" (NUS)
# pattern, so it works with almost any BLE UART app/library, including
# the companion computer_controller.py script.
#
# Copy this file to the Pico as "main.py" so it runs automatically on boot.

import bluetooth
import machine
import time
from micropython import const

# ---------------- BLE UART (Nordic UART Service) ----------------

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_NOTIFY)
_UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE)
_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX))

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)


class BLEUART:
    def __init__(self, ble, name="PicoRemote"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = self._advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Central connected:", conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            print("Central disconnected, advertising again")
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self._rx_handle:
                value = self._ble.gatts_read(self._rx_handle)
                if self._write_callback:
                    self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def on_write(self, callback):
        self._write_callback = callback

    def _advertising_payload(self, name=None, services=None):
        payload = bytearray()

        def _append(adv_type, value):
            nonlocal payload
            payload += bytes((len(value) + 1, adv_type)) + value

        _append(0x01, bytes([0x06]))  # flags: general discoverable, no BR/EDR
        if name:
            _append(0x09, name.encode())
        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 16:
                    _append(0x07, b)
                elif len(b) == 2:
                    _append(0x03, b)
        return payload

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)


# ---------------- Hardware setup ----------------
# Edit this section to match what you actually want to control.

onboard_led = machine.Pin("LED", machine.Pin.OUT)  # Pico 2 W onboard LED

# Extra GPIO pins available for relays, motors, LEDs, etc.
# Add/remove entries as needed for your project.
gpio_pins = {
    "2": machine.Pin(2, machine.Pin.OUT),
    "3": machine.Pin(3, machine.Pin.OUT),
    "4": machine.Pin(4, machine.Pin.OUT),
}
for p in gpio_pins.values():
    p.value(0)

ble = bluetooth.BLE()
uart = BLEUART(ble, name="PicoRemote")


def handle_command(cmd):
    cmd = cmd.strip().upper()
    print("Received:", cmd)

    if cmd == "LED ON":
        onboard_led.value(1)
        uart.send(b"OK: LED ON\n")

    elif cmd == "LED OFF":
        onboard_led.value(0)
        uart.send(b"OK: LED OFF\n")

    elif cmd.startswith("PIN"):
        # Format: "PIN2 ON" / "PIN3 OFF" etc.
        try:
            parts = cmd.split()
            pin_num = parts[0][3:]
            state = parts[1]
            if pin_num in gpio_pins:
                gpio_pins[pin_num].value(1 if state == "ON" else 0)
                uart.send(("OK: PIN%s %s\n" % (pin_num, state)).encode())
            else:
                uart.send(b"ERR: unknown pin\n")
        except Exception:
            uart.send(b"ERR: bad command\n")

    elif cmd == "STATUS":
        status = "LED=%d " % onboard_led.value()
        for k in sorted(gpio_pins):
            status += "PIN%s=%d " % (k, gpio_pins[k].value())
        uart.send((status + "\n").encode())

    else:
        uart.send(b"ERR: unknown command\n")


def on_rx(data):
    try:
        handle_command(data.decode())
    except Exception as e:
        print("error handling command:", e)


uart.on_write(on_rx)

print("BLE UART peripheral 'PicoRemote' advertising...")

while True:
    time.sleep_ms(200)
