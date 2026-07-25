# Blinking Circle Grid for DVS Calibration

A fullscreen, blinking asymmetric circle grid for collecting calibration patterns with DVS cameras.

## Run

This program requires Windows, Python 3, OpenCV, and NumPy.

```bash
pip install opencv-python numpy
python circle_blink.py
```

Press `q` while the pattern window is focused to quit.

## Configuration

Edit the constants at the top of `circle_blink.py`.

| Setting | Purpose |
| --- | --- |
| `TARGET_MONITOR` | Windows display number to use, such as `1` or `2`. |
| `MONITOR_RESOLUTIONS` | Output resolution for each display number. Add an entry when using another monitor. |
| `REFERENCE_RESOLUTION` | Resolution used as the reference for proportional pattern sizing. |
| `GRID_RC` | Circle-grid dimensions as `(rows, columns)`. Use the same dimensions in the downstream detector/calibration setup. |
| `BLINK_HZ` | Complete bright-to-dark-to-bright cycles per second. |

The spacing, circle diameter, and margins are scaled from the reference resolution. With only one active monitor, the script uses that monitor's detected resolution automatically.

## How It Works

The script detects active Windows displays, moves an OpenCV window to the selected display, and switches it to fullscreen. It generates a centered asymmetric circle grid on a mid-gray background. All circles alternate between white and black according to `BLINK_HZ`, producing brightness transitions for a DVS camera.

## Files

```text
circle_blink.py    Main fullscreen blinking-pattern program
README.md          This guide
legacy/            Previous README, script, and image assets
```

## Notes

- This program uses Windows display APIs and is intended for Windows.
- Match `TARGET_MONITOR` and `MONITOR_RESOLUTIONS` to the display numbers and resolutions shown in Windows display settings.
- The visible timing is limited by the monitor refresh rate, the operating system, and OpenCV window scheduling; it is not a hardware trigger.
- Keep the camera and monitor still during capture, and use a flat monitor for calibration.
