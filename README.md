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

### Default Behavior

With the included defaults, the program displays a centered 4×11 asymmetric circle grid in fullscreen on monitor 2 at 3840×2160. The grid alternates between white and black at 10 complete blink cycles per second (10 Hz) on a mid-gray background. The rendering loop targets 120 FPS; the actual visible update rate is limited by the display refresh rate and the operating system.

## How It Works

The script detects active Windows displays, moves an OpenCV window to the selected display, and switches it to fullscreen. It generates a centered asymmetric circle grid on a mid-gray background. All circles alternate between white and black according to `BLINK_HZ`, producing brightness transitions for a DVS camera.

## Files

```text
circle_blink.py    Main fullscreen blinking-pattern program
README.md          This guide
```

## Notes

- This program uses Windows display APIs and is intended for Windows.
- Match `TARGET_MONITOR` and `MONITOR_RESOLUTIONS` to the display numbers and resolutions shown in Windows display settings.
- This script is a preparation step for acquiring NRV DVS calibration data. The NRV sensor supports a global shutter, which makes it suitable for capturing the complete monitor pattern at a single pose.
- Use a flat monitor rather than a curved monitor. Calibration assumes that the pattern lies on one plane; a curved display bends the apparent circle-grid positions and can increase calibration error.
- Monitor refresh, operating-system window timing, OpenCV `waitKey`, and Python `sleep` are not as precise as a hardware trigger. Review the recorded data and select moments where the complete circle grid is clearly visible.
- Keep both the camera and monitor as still as possible during capture. Events from surrounding objects or motion blur at the grid boundary can reduce center-detection and calibration accuracy.
