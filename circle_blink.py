import cv2
import numpy as np
import time
import ctypes
import re
from ctypes import wintypes

# =========================
# Easy-to-edit settings
# =========================
# Enter the Windows monitor number to use, for example 1 or 2.
TARGET_MONITOR = 2

# Output resolution for each monitor. Add another number/resolution pair for more displays.
MONITOR_RESOLUTIONS = {
    1: (2560, 1440),
    2: (3840, 2160),
}

REFERENCE_RESOLUTION = (3840, 2160)  # Pattern dimensions scale proportionally from this resolution.
GRID_RC = (4, 11)                   # (rows, columns)
BLINK_HZ = 10                       # Complete bright-to-dark-to-bright cycles per second.

# =========================
# Display setup
# =========================
# When only one monitor is active, it is used in fullscreen regardless of TARGET_MONITOR.


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


def get_monitors():
    """Return active monitors in Windows display-number order (DISPLAY1, DISPLAY2, ...)."""
    user32 = ctypes.windll.user32

    # Use physical pixels so a high-DPI secondary monitor is positioned correctly.
    try:
        user32.SetProcessDPIAware()
    except AttributeError:
        pass

    monitors = []
    monitor_enum_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )

    def callback(hmonitor, _hdc, _rect, _data):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            rect = info.rcMonitor
            number_match = re.search(r"DISPLAY(\d+)$", info.szDevice)
            display_number = int(number_match.group(1)) if number_match else 9999
            monitors.append({
                "number": display_number,
                "device": info.szDevice,
                "x": rect.left,
                "y": rect.top,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top,
                "primary": bool(info.dwFlags & 1),
            })
        return True

    user32.EnumDisplayMonitors(None, None, monitor_enum_proc(callback), 0)
    return sorted(monitors, key=lambda monitor: monitor["number"])


def select_monitor(monitors, target_number):
    if not monitors:
        raise RuntimeError("Could not find an active monitor.")

    # Always use the only available monitor.
    if len(monitors) == 1:
        return monitors[0]

    for monitor in monitors:
        if monitor["number"] == target_number:
            return monitor

    available = ", ".join(str(monitor["number"]) for monitor in monitors)
    raise ValueError(f"Could not find monitor {target_number}. Available monitors: {available}")


monitors = get_monitors()
monitor = select_monitor(monitors, TARGET_MONITOR)

# For a single monitor, use its detected physical fullscreen resolution.
if len(monitors) == 1:
    screen_w = monitor["width"]
    screen_h = monitor["height"]
else:
    try:
        screen_w, screen_h = MONITOR_RESOLUTIONS[TARGET_MONITOR]
    except KeyError as error:
        raise ValueError(
            f"Add a resolution for monitor {TARGET_MONITOR} to MONITOR_RESOLUTIONS."
        ) from error
print(
    f"Monitor {monitor['number']} ({monitor['device']}): "
    f"{screen_w}x{screen_h} @ ({monitor['x']}, {monitor['y']})"
)

# The pattern was originally sized for a 3840x2160 display.
# It scales proportionally for the selected output resolution.
REFERENCE_WIDTH, REFERENCE_HEIGHT = REFERENCE_RESOLUTION
pattern_scale = min(screen_w / REFERENCE_WIDTH, screen_h / REFERENCE_HEIGHT)

rows, cols = GRID_RC

# =========================
# Pattern size settings
# =========================
spacing_px = round(160 * pattern_scale)
circle_diameter_px = round(115 * pattern_scale)   # Circle size at the 3840-pixel reference width.
radius_px = circle_diameter_px // 2

margin_x = round(200 * pattern_scale)
margin_y = round(200 * pattern_scale)

# =========================
# Brightness settings
# =========================
bg_val = 128
bright_val = 255
dark_val = 0

# The bright/dark state switches every half period of BLINK_HZ.
fps = 120
frame_dt = 1.0 / fps

# =========================
# Asymmetric circle-grid point generator
# =========================
def make_points():
    points = []

    for r in range(rows):
        y = margin_y + r * spacing_px
        x_offset = 0 if r % 2 == 0 else spacing_px

        for c in range(cols):
            x = margin_x + x_offset + 2 * c * spacing_px
            points.append((x, y))

    # Center the pattern.
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    pattern_w = max(xs) - min(xs)
    pattern_h = max(ys) - min(ys)

    shift_x = (screen_w - pattern_w) // 2 - min(xs)
    shift_y = (screen_h - pattern_h) // 2 - min(ys)

    return [(x + shift_x, y + shift_y) for (x, y) in points]


def blink_state(elapsed_seconds):
    """Return 0 for bright and 1 for dark at the requested complete blink rate."""
    return int(elapsed_seconds * BLINK_HZ * 2) % 2


points = make_points()

# =========================
# Window setup
# =========================
win = "Blink Asymmetric Circle Grid"
cv2.namedWindow(win, cv2.WINDOW_NORMAL)
# Move the window to the target monitor before switching to fullscreen.
cv2.resizeWindow(win, screen_w, screen_h)
cv2.moveWindow(win, monitor["x"], monitor["y"])
cv2.waitKey(50)
cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# =========================
# Video recording settings
# Uncomment the recording lines below when a video file is needed.
# =========================
# recording = True
# fourcc = cv2.VideoWriter_fourcc(*"mp4v")
# writer = cv2.VideoWriter(
#     "circle_grid_blink.mp4",
#     fourcc,
#     fps,
#     (screen_w, screen_h),
#     True
# )

# Default when recording is disabled.
recording = False
writer = None

# =========================
# Main loop
# =========================
start_time = time.perf_counter()

while True:

    frame_start = time.perf_counter()

    frame = np.full((screen_h, screen_w), bg_val, dtype=np.uint8)

    # All circles use the same color in a frame.
    state = blink_state(frame_start - start_time)
    circle_color = bright_val if state == 0 else dark_val

    for (x, y) in points:
        cv2.circle(frame, (x, y), radius_px, int(circle_color), -1, lineType=cv2.LINE_AA)

    cv2.imshow(win, frame)

    # =========================
    # Optional recording.
    # Enable it by setting recording = True and creating the writer above.
    # =========================
    if recording and writer is not None:
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        writer.write(frame_bgr)

    key = cv2.waitKey(1) & 0xFF

    # Keyboard exit.
    if key == ord('q'):
        break

    elapsed = time.perf_counter() - frame_start
    sleep = frame_dt - elapsed
    if sleep > 0:
        time.sleep(sleep)

if writer is not None:
    writer.release()

cv2.destroyAllWindows()
