# Reusing an Ultimaker S5 touchscreen with a Raspberry Pi 4

Verified on 3 November 2026 with the Robo-Recycle hardware. This guide explains the investigation, the working setup, and how to reproduce it. The complete source files are embedded below so this document can be used independently.

## Result and validation limits

The user confirmed a full desktop on the Ultimaker screen and correctly positioned touch input, including taps near the corners. Linux's native touchscreen driver is bound and the startup service has successfully run in the current desktop session.

The startup files have been saved for normal boots, but **a fresh normal boot has not yet been verified**. The first KMS boot also logged VC4 HVS warnings while starting the desktop; the desktop subsequently worked. Do not describe the system as fully reboot-validated until that check is completed.

The screen's previous working condition in the printer was unknown. The successful image and touch tests establish that this particular module can work with this Pi. They do not establish that every S5 screen revision uses identical controls.

## Hardware and observed specifications

| Item | Verified value or qualification |
| --- | --- |
| Host | Raspberry Pi 4 Model B Rev 1.1 |
| OS | Debian 12 Bookworm, 64-bit, kernel `6.12.25+rpt-rpi-v8` |
| Desktop compositor | labwc / Wayland |
| Screen identity | EDID model name `Ultcntrl_3.1` |
| Screen connection | First Pi micro-HDMI output → micro-HDMI/HDMI adapter → HDMI cable → Ultimaker display module |
| Other monitor | HP E240 on the second output, 1920 × 1080 at 60 Hz |
| Screen resolution | 800 × 320 pixels |
| EDID preferred refresh | Approximately 55.3427 Hz |
| EDID pixel clock | 26 MHz |
| EDID physical dimensions | 100 × 40 mm; reported metadata, not a physical measurement |
| Identification block | Valid 128-byte EDID with checksum zero |
| Screen control bus | HDMI DDC / I²C, exposed as adapter 20 on this boot |
| GPIO expander | PCA9570-compatible device, address `0x24` |
| Touch controller | FocalTech FT5426-compatible device, address `0x38` |
| Light controller | PCA9632-compatible device, address `0x60`; channel 3 is used for backlight control |
| Working brightness | PWM value 128 out of 256 duty-cycle steps, approximately 50% |
| USB touch cable | None used |
| HDMI cable | User identified an Antsig 1.5 m 4K lead, believed to be model AP454B; model was not independently verified |

The LCD panel manufacturer's part number and the module's detailed power consumption were not established. An illuminated screen or a clean Pi undervoltage report alone does not prove correct panel power or initialization.

All I²C addresses in this document are **7-bit device addresses**, not connector pin numbers. Bus number 20 is an observed Linux identifier and should be checked on another machine.

## Why HDMI carries both picture and touch

A normal HDMI connection includes high-speed picture channels and a separate low-speed control connection called DDC, based on I²C. Computers normally use DDC to read the display's EDID: a small identification record that describes video modes and related information.

This Ultimaker module also places its touch controller, GPIO expander, and light controller on that control bus. Consequently, one physical cable can carry the video and the communications needed to initialize the module and read touches. Its original printer software knew how to operate those extra devices; an ordinary desktop display setup does not automatically know that they exist.

Conceptually:

```text
Pi graphics output ── HDMI picture channels ──> display image
Pi I²C adapter    <── same cable's DDC bus ──> EDID + GPIO + lights + touch
                                               0x24   0x60   0x38
```

This does not mean arbitrary HDMI monitors support touch over DDC. This is a feature of the module examined here.

## Why the original settings did not work

The Pi originally used `vc4-fkms-v3d`, the older firmware-backed Fake KMS graphics driver. The first output was forced to 800 × 480 by manually added `hdmi_*` settings. The operating system reported the output as connected, but that status was forced and did not prove that the panel was responding. No EDID or HDMI I²C adapters were exposed in the checks performed under that configuration.

A temporary switch to 800 × 320 alone still produced a white panel with blinking black lines. Disabling the output made the panel go dark, which showed a reaction to output disable but did not distinguish loss of picture from loss of screen power.

Switching to `vc4-kms-v3d`, the standard kernel-managed graphics driver, exposed the DDC adapters and a valid `Ultcntrl_3.1` EDID. The compositor then selected the screen's own preferred timing. The image was still white until the control initialization below was applied.

The observed fix was therefore the **combination of usable driver/control-bus access, appropriate timing, and module initialization**. The tests did not isolate every register write's individual contribution.

A cable swap demonstrated that the original screen port and adapter could drive the HP monitor using the monitor's cable. It did not verify the Ultimaker cable, because the adapters stayed at the Pi while the HDMI plugs were exchanged. The live swap left the desktop unusable and the user power-cycled the Pi. The logs did not establish the cause. Make future physical changes after a clean shutdown.

## Video timing, beyond resolution

Resolution specifies the visible pixels, but a panel also needs a pixel clock and intervals between lines and frames. These intervals include front porch, sync pulse, and back porch, collectively called blanking.

The screen's EDID preferred timing is:

| Timing component | Value |
| --- | --- |
| Horizontal active / front porch / sync / back porch | 800 / 10 / 48 / 42 pixels |
| Vertical active / front porch / sync / back porch | 320 / 10 / 3 / 189 lines |
| Horizontal / vertical sync polarity | Negative / negative |
| Pixel clock | 26,000,000 pixels per second |

There are 900 total pixel periods per line and 522 total lines per frame, including blanking. Therefore:

```text
refresh = 26,000,000 / (900 × 522) ≈ 55.3427 frames per second
```

An automatically generated “800 × 320 at 60 Hz” mode can have different porches and pixel clock. It is not equivalent to the EDID timing merely because the active dimensions match. The successful KMS session used the EDID preferred mode, approximately 55.34 Hz.

## What the initialization changes

The initial readbacks were GPIO `0xff` and light-controller registers MODE1 `0x11`, MODE2 `0x01`, PWM3 `0x00`, LEDOUT `0x00`.

| Device / register | Working change | Meaning |
| --- | --- | --- |
| GPIO device `0x24`, output byte | `value & ~0x04`; initially `0xff → 0xfb` | Clears bit 2 while preserving the other outputs |
| Light device `0x60`, MODE1 register `0x00` | Clear bit `0x10`; initially `0x11 → 0x01` | Wakes the oscillator from sleep |
| MODE2 register `0x01` | Set bit `0x04`; initially `0x01 → 0x05` | Selects totem-pole output drive |
| PWM3 register `0x05` | Set to `0x80` | Approximately 50% duty cycle for channel 3 |
| LEDOUT register `0x08` | `(value & 0x3f) | 0x80` | Selects individual PWM for channel 3 while preserving channels 0–2 |

Bit 2 is named `PWR_DWN` in a related UltiMaker controller configuration. The exact schematic for this `Ultcntrl_3.1` board was not obtained. Clearing the bit together with the light-controller settings was empirically verified to produce the desktop. It is **not Raspberry Pi GPIO header pin 2**, and no wiring to that header was added.

The masks preserve unrelated bits. For example, `0x04` is binary `00000100`; ANDing a value with its complement clears only that bit. Hexadecimal is used because these registers are bytes and their control fields are individual bits.

The light-controller definitions are documented in the [NXP PCA9632 datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9632.pdf). The screen wiring and touch-controller selection are supported by [UltiMaker's original controller configuration](https://github.com/Ultimaker/um-kernel/blob/cfef5650688ad2322e3b6388080a24f40e99e756/dts/part201258-ulticontroller3.dtsi). The related GPIO names appear in [UltiMaker's later controller configuration](https://github.com/Ultimaker/um-kernel/blob/1f6a8dca98b470ceb7ef5a92b62d8c471e3d6976/dts/ulticontroller3.2-lvds-800x320.dts); its LVDS video timings were not substituted for this screen's HDMI EDID timing.

## How touch reaches applications

The touch sensor/controller converts finger contact into coordinates. The Pi's kernel driver reads those coordinates over I²C and publishes standard Linux input events. libinput passes them to the labwc compositor, which maps them onto the chosen display. Applications receive normal touchscreen events.

```text
Finger → FocalTech controller → HDMI I²C bus → edt_ft5x06 kernel driver
       → Linux input device → libinput → labwc → application
```

The device-tree overlay tells Linux facts it cannot infer from an arbitrary I²C address: the device at `0x38` is compatible with `focaltech,ft5426`, and its coordinate area is 800 × 320. A device tree describes hardware; the overlay adds this description to the running system. It does not emulate the touchscreen.

The installed `edt_ft5x06` driver supports polling without a dedicated interrupt connection. That polling support is present in this Pi's installed module and was checked before binding the device. On another kernel, verify that support rather than assuming that the same instructions will work. The [Raspberry Pi kernel driver source](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/input/touchscreen/edt-ft5x06.c) includes this polling path.

The device appeared as `20-0038 generic ft5x06 (79)`. The compositor was explicitly told to associate it with `HDMI-A-1`; otherwise absolute touch coordinates may be associated with the wrong output or span the combined desktop. Correct tap placement was confirmed by the user. Multitouch capacity was not tested.

## Reproducing the installation

These instructions target a Pi 4 and this identified screen, using a compatible Bookworm / labwc installation. Do not overwrite another Pi's full boot files with this Pi's copies: settings such as the root filesystem's PARTUUID belong to the individual installation. Save work and shut down before changing cables.

### 1. Record the baseline and prepare tools

Commands run in a terminal; `sudo` is required for system files, services, overlays, and some device access.

```sh
mkdir -p "$HOME/ultimaker-s5-backup"
sudo cp /boot/firmware/config.txt "$HOME/ultimaker-s5-backup/config.txt"
sudo cp /boot/firmware/cmdline.txt "$HOME/ultimaker-s5-backup/cmdline.txt"
cp "$HOME/.config/labwc/rc.xml" "$HOME/ultimaker-s5-backup/labwc-rc.xml"
uname -a
wlr-randr
modinfo edt_ft5x06
```

If missing, install `i2c-tools` and `device-tree-compiler` with the package manager. This setup also uses Python 3, `dtoverlay`, systemd, and labwc. The module must support operation without an IRQ. The exact backup command assumes an existing labwc configuration; skip that copy if the file does not exist.

### 2. Configure standard KMS

Edit `/boot/firmware/config.txt`. Replace the existing FKMS line with the KMS line; do not load both:

```ini
dtoverlay=vc4-kms-v3d
```

Remove the experimental `hdmi_force_hotplug:0`, `hdmi_group:0`, `hdmi_mode:0`, `hdmi_cvt:0`, and `hdmi_drive:0` assignments used for the earlier firmware-driven test. They are not the control initialization described here.

The tested setup also appends the following to the **existing single line** in `/boot/firmware/cmdline.txt`, preserving its other contents:

```text
video=HDMI-A-1:800x320M@60D video=HDMI-A-2:1920x1080@60D
```

The second parameter is specific to the HP monitor in this two-screen setup. Adapt or omit it for another arrangement. The first provides a forced alternative mode; the running compositor actually selected the EDID preferred 55.34 Hz mode. Do not assume the `@60` text proves the screen is running at 60 Hz: check `wlr-randr` or `kmsprint`.

During diagnosis, these changes were first placed in separate `tryboot.txt` and command-line files. `sudo reboot '0 tryboot'` selected them for one boot. A subsequent normal restart uses normal `config.txt` again. After the image worked, the tested KMS configuration was copied into the normal boot files. See [Raspberry Pi's tryboot documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#fail-safe-os-updates-tryboot). On Pi 4 Rev 1.0/1.1, tryboot requires the EEPROM not to be write-protected.

### 3. Create and install the three source files below

Save the embedded listings as `ultimaker-s5-init.py`, `ultimaker-s5-touch-overlay.dts`, and `ultimaker-s5-display.service` in a working directory, then run from that directory:

```sh
dtc -@ -I dts -O dtb -o ultimaker-s5-touch.dtbo ultimaker-s5-touch-overlay.dts
sudo install -d /usr/local/share/ultimaker-s5
sudo install -m 644 ultimaker-s5-touch.dtbo /usr/local/share/ultimaker-s5/
sudo install -m 755 ultimaker-s5-init.py /usr/local/sbin/ultimaker-s5-init
sudo install -m 644 ultimaker-s5-display.service /etc/systemd/system/
sudo systemd-analyze verify /etc/systemd/system/ultimaker-s5-display.service
sudo systemctl daemon-reload
sudo systemctl enable ultimaker-s5-display.service
```

If already running KMS with this screen connected, `sudo systemctl start ultimaker-s5-display.service` initializes it now. If still running FKMS, save work and reboot normally first; the enabled service will run after the new driver loads. Enabling a service persists it for later boots; starting one runs it in the current session.

The service waits for this specific screen's valid EDID, discovers its DDC adapter, changes the control registers, and then loads the touchscreen overlay. The order matters: before initialization, the touch controller did not respond to our initial ID read. Loading the overlay only after initialization avoids probing the chip while it is unavailable.

The service runs once per boot, before the display manager. It is not a cable hotplug monitor. If the module loses power after boot, the service may need restarting.

### 4. Map touch to its display

Find the actual device name with `libinput list-devices` (use `sudo` if device permissions require it). Add this child element inside the existing `<openbox_config>` element in `~/.config/labwc/rc.xml`, preserving the existing configuration:

```xml
<touch deviceName="20-0038 generic ft5x06 (79)" mapToOutput="HDMI-A-1" mouseEmulation="no" />
```

Use the actual name if the bus number or firmware string differs. Then reload labwc:

```sh
labwc --reconfigure
```

Touchscreen events remain native touch events; this setting does not turn the screen into an emulated mouse.

### 5. Verify function and a normal boot

```sh
systemctl status ultimaker-s5-display.service --no-pager
journalctl -b -u ultimaker-s5-display.service --no-pager
wlr-randr
libinput list-devices
```

Verify a visible desktop, taps at the expected locations, a working second monitor, and then a fresh normal boot. Keep the distinction between “driver detected a device” and “a person verified image and touch.” The latter was confirmed in the current session; the final normal-boot check is outstanding as of this document's date.

## Troubleshooting and recovery

- **White panel with blinking lines:** check service status and EDID timing, rather than only forcing a resolution. Reapply initialization with `sudo systemctl restart ultimaker-s5-display.service`.
- **No EDID / no matching screen:** the initialization script exits without changing device registers. Check KMS is active, the connection is on HDMI-A-1, and the cable/adapter arrangement matches the setup.
- **Image works but no touch:** check the overlay and kernel driver with `dtoverlay -l` and `readlink /sys/bus/i2c/devices/20-0038/driver`. Adjust the observed bus number as needed. Inspect the service and kernel logs. A native driver that requires an IRQ is not equivalent to the polling-capable driver used here.
- **Taps reach the wrong place:** verify the device name, 800 × 320 coordinate description, labwc mapping, and display orientation. Do not add a calibration matrix without evidence that calibration is needed.
- **Screen loses power after startup:** reconnect with the Pi shut down where practical, then boot; or restart the initialization service after a deliberate controlled reconnection.
- **Black desktop after a cable swap:** the cause of the observed incident was not proven. Avoid further live swaps. Use a normal shutdown before moving cables.

To undo a reproduction setup, disable the service, restore your own saved boot files, remove the added touch mapping, and reboot normally:

```sh
sudo systemctl disable --now ultimaker-s5-display.service
sudo cp "$HOME/ultimaker-s5-backup/config.txt" /boot/firmware/config.txt
sudo cp "$HOME/ultimaker-s5-backup/cmdline.txt" /boot/firmware/cmdline.txt
```

Remove only the added `<touch>` element if you have made other desktop configuration changes since the backup. Disabling the service does not immediately reset hardware or unload the running overlay; the reboot returns to the original boot configuration.

On the Pi configured during this investigation, the pre-change boot files are instead stored at `/usr/local/share/ultimaker-s5/original-config.txt` and `original-cmdline.txt`. The installed files are listed by name below; normal boot files and the labwc configuration are the only existing configuration files modified. There were no firmware updates, kernel builds, GPIO-header wiring changes, or changes to the Robo-Recycle motion-control application.

## Complete initialization script: ultimaker-s5-init.py

The script deliberately identifies the screen before writing. It preserves unrelated GPIO/light bits, uses the tested 50% brightness, and avoids creating a duplicate touchscreen device when restarted.

```python
#!/usr/bin/python3
"""Initialize the identified Ulticontroller 3.1 on Raspberry Pi 4 HDMI DDC0."""
from pathlib import Path
import subprocess
import time

I2C = '/usr/sbin/i2ctransfer'

def transfer(bus, *args):
    return subprocess.run([I2C, '-y', str(bus), *args], check=True,
                          capture_output=True, text=True, timeout=5).stdout.strip()

def read(bus, address, register):
    return int(transfer(bus, f'w1@{address:#x}', f'{register:#x}', 'r1'), 16)

def write(bus, address, register, value):
    transfer(bus, f'w2@{address:#x}', f'{register:#x}', f'{value:#x}')

subprocess.run(['/usr/sbin/modprobe', 'i2c-dev'], check=True)
bus = None
for attempt in range(30):
    for connector in Path('/sys/class/drm').glob('card*-HDMI-A-1'):
        try:
            edid = (connector / 'edid').read_bytes()
            if len(edid) != 128 or sum(edid) % 256 or b'Ultcntrl_3.1' not in edid:
                continue
            adapter = (connector / 'ddc').resolve()
            if adapter.name.startswith('i2c-'):
                candidate = int(adapter.name[4:])
                if Path(f'/dev/i2c-{candidate}').exists():
                    bus = candidate
                    break
        except (OSError, ValueError):
            continue
    if bus is not None:
        break
    time.sleep(1)
if bus is None:
    raise SystemExit('Ultcntrl_3.1 not identified on HDMI-A-1; no device registers changed.')

# This combination was visually verified to produce the desktop on this board.
gpio = int(transfer(bus, 'r1@0x24'), 16)
transfer(bus, 'w1@0x24', hex(gpio & ~0x04))
write(bus, 0x60, 0x00, read(bus, 0x60, 0x00) & ~0x10)
time.sleep(0.001)
write(bus, 0x60, 0x01, read(bus, 0x60, 0x01) | 0x04)
write(bus, 0x60, 0x05, 128)
write(bus, 0x60, 0x08, (read(bus, 0x60, 0x08) & 0x3f) | 0x80)

subprocess.run(['/usr/sbin/modprobe', 'edt-ft5x06'], check=True)
client = Path(f'/sys/bus/i2c/devices/{bus}-0038')
if not client.exists():
    subprocess.run(['/usr/bin/dtoverlay', '-d', '/usr/local/share/ultimaker-s5',
                    'ultimaker-s5-touch'], check=True)
for attempt in range(30):
    if (client / 'driver').exists():
        print(f'Ultimaker screen initialized on I2C {bus}; backlight 50%; native touch driver bound.')
        break
    time.sleep(0.1)
else:
    raise SystemExit('Display initialized, but native touchscreen driver did not bind.')
```

## Complete device-tree overlay: ultimaker-s5-touch-overlay.dts


```dts
/dts-v1/;
/plugin/;
/ {
    compatible = "brcm,bcm2711";
    fragment@0 {
        target = <&ddc0>;
        __overlay__ {
            #address-cells = <1>;
            #size-cells = <0>;
            ultimaker_touch: touchscreen@38 {
                compatible = "focaltech,ft5426";
                reg = <0x38>;
                touchscreen-size-x = <800>;
                touchscreen-size-y = <320>;
                status = "okay";
            };
        };
    };
};
```

## Complete startup service: ultimaker-s5-display.service


```ini
[Unit]
Description=Initialize Ultimaker S5 display and native touch input
After=systemd-udev-trigger.service
Before=display-manager.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/ultimaker-s5-init
RemainAfterExit=yes
TimeoutStartSec=60

[Install]
WantedBy=graphical.target
```

The overlay targets `ddc0`, the first HDMI DDC controller on this Pi 4. The compiled overlay is installed at `/usr/local/share/ultimaker-s5/ultimaker-s5-touch.dtbo`. The initialization script loads it dynamically after waking the screen; do not also add a duplicate boot overlay. The service's `RemainAfterExit=yes` means a completed one-shot service remains marked active; it does not mean a background initialization process keeps running. Kernel touch polling continues independently.
