# Pico 2 W Bluetooth Control

Two files:

- **`pico_main.py`** – runs on the Raspberry Pi Pico 2 W. Turns it into a
  Bluetooth LE peripheral you can send commands to.
- **`computer_controller.py`** – runs on your computer. Scans for the Pico,
  connects, and gives you a prompt to type commands.

## 1. Set up the Pico

1. Flash the Pico 2 W with MicroPython if you haven't already:
   - Download the latest **Pico 2 W** firmware `.uf2` from
     https://micropython.org/download/RPI_PICO2_W/
   - Hold the **BOOTSEL** button while plugging the Pico into USB, then drag
     the `.uf2` file onto the drive that appears.
2. Install **Thonny** (https://thonny.org) if you don't have it, and set it
   to use the "MicroPython (Raspberry Pi Pico)" interpreter.
3. Open `pico_main.py` in Thonny, then **File → Save As → Raspberry Pi Pico**
   and save it as `main.py` (the name matters — `main.py` runs automatically
   on boot).
4. Run it once from Thonny to confirm you see:
   ```
   BLE UART peripheral 'PicoRemote' advertising...
   ```
   After that, it will start automatically every time the Pico powers on.

## 2. Set up the computer side

You need Python 3.8+ on your computer.

```bash
pip install bleak
```

Then run:

```bash
python computer_controller.py
```

It will scan for a device named `PicoRemote`, connect, and give you a `>`
prompt. Type commands like:

```
LED ON
LED OFF
PIN2 ON
PIN2 OFF
STATUS
```

Type `help` to see the command list again, or `quit` to disconnect.

## 3. Customize it

- **Add more pins**: in `pico_main.py`, add entries to the `gpio_pins`
  dictionary, e.g. `"5": machine.Pin(5, machine.Pin.OUT)`.
- **Add new commands**: extend the `handle_command()` function on the Pico
  side — it just receives whatever text string you send from the computer.
- **Control motors/servos**: swap `machine.Pin(...)` for a `machine.PWM(...)`
  object and add commands that set duty cycle instead of just on/off.

## Troubleshooting

- **Pico not found**: make sure `pico_main.py` is actually running (check
  Thonny's console), and that your computer's Bluetooth is on.
- **Connects then instantly disconnects**: unplug/replug the Pico's power
  and re-run `computer_controller.py` — this is a normal BLE reconnect
  hiccup.
- **macOS asks for Bluetooth permission**: grant it to your terminal/Python
  in System Settings → Privacy & Security → Bluetooth.
