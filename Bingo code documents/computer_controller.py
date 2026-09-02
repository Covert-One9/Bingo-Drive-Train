#!/usr/bin/env python3
"""
computer_controller.py

Controls the Raspberry Pi Pico 2 W (running pico_main.py) over Bluetooth LE
from your computer.

Setup:
    pip install bleak

Run:
    python computer_controller.py

Works on Windows, macOS, and Linux (bleak is cross-platform).
"""

import asyncio
import sys

from bleak import BleakScanner, BleakClient

DEVICE_NAME = "PicoRemote"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # write -> Pico
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # notify <- Pico


def handle_notification(_, data: bytearray):
    print(f"[Pico] {data.decode().strip()}")


async def find_pico():
    print(f"Scanning for '{DEVICE_NAME}' (up to 15s)...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=15.0)
    if device is None:
        print("Could not find the Pico.")
        print("  - Make sure it's powered on and pico_main.py is running")
        print("  - Make sure your computer's Bluetooth is turned on")
        sys.exit(1)
    print(f"Found '{device.name}' at {device.address}")
    return device


def print_help():
    print(
        """
Commands you can type:
  LED ON / LED OFF        toggle the onboard LED
  PIN2 ON / PIN2 OFF      toggle GPIO2
  PIN3 ON / PIN3 OFF      toggle GPIO3
  PIN4 ON / PIN4 OFF      toggle GPIO4
  STATUS                  ask the Pico for its current state
  help                    show this message
  quit / exit             disconnect and quit
"""
    )


async def main():
    device = await find_pico()

    async with BleakClient(device) as client:
        print("Connected!\n")
        await client.start_notify(UART_TX_CHAR_UUID, handle_notification)
        print_help()

        loop = asyncio.get_event_loop()
        while True:
            cmd = await loop.run_in_executor(None, input, "> ")
            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd.lower() in ("quit", "exit"):
                break
            if cmd.lower() in ("help", "?"):
                print_help()
                continue

            await client.write_gatt_char(UART_RX_CHAR_UUID, (cmd + "\n").encode())
            await asyncio.sleep(0.1)  # give the Pico a moment to reply

        print("Disconnecting...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")
