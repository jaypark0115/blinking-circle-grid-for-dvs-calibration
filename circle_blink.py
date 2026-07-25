import cv2
import numpy as np
import time
import ctypes
import re
from ctypes import wintypes

# =========================
# 쉽게 수정하는 설정값
# =========================
# 사용할 모니터 번호를 입력하세요. 예: 1 또는 2
TARGET_MONITOR = 2

# 모니터별 출력 해상도입니다. 모니터를 추가하면 같은 형식으로 번호와 해상도를 넣으세요.
MONITOR_RESOLUTIONS = {
    1: (2560, 1440),
    2: (3840, 2160),
}

REFERENCE_RESOLUTION = (3840, 2160)  # 이 해상도를 기준으로 패턴 크기를 비율 조정
GRID_RC = (4, 11)                # (행, 열)
BLINK_HZ = 10                  # 밝음->어두움->밝음 완전한 한 주기의 초당 횟수

# =========================
# 화면 설정
# =========================
# 모니터가 1대뿐이면 이 값과 관계없이 그 모니터를 전체 화면으로 사용합니다.


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
        raise RuntimeError("활성 모니터를 찾지 못했습니다.")

    # 한 대뿐이면 항상 그 모니터를 사용합니다.
    if len(monitors) == 1:
        return monitors[0]

    for monitor in monitors:
        if monitor["number"] == target_number:
            return monitor

    available = ", ".join(str(monitor["number"]) for monitor in monitors)
    raise ValueError(f"모니터 {target_number}번을 찾지 못했습니다. 사용 가능 번호: {available}")


monitors = get_monitors()
monitor = select_monitor(monitors, TARGET_MONITOR)

# 모니터가 한 대면 설정표와 무관하게 실제 전체 화면을 사용합니다.
if len(monitors) == 1:
    screen_w = monitor["width"]
    screen_h = monitor["height"]
else:
    try:
        screen_w, screen_h = MONITOR_RESOLUTIONS[TARGET_MONITOR]
    except KeyError as error:
        raise ValueError(
            f"MONITOR_RESOLUTIONS에 모니터 {TARGET_MONITOR}번 해상도를 추가하세요."
        ) from error
print(
    f"모니터 {monitor['number']} ({monitor['device']}): "
    f"{screen_w}x{screen_h} @ ({monitor['x']}, {monitor['y']})"
)

# 원래 3840x2160 화면에서 맞춘 패턴입니다.
# 대상 해상도에 맞춰 비율을 유지한 채 확대/축소합니다.
REFERENCE_WIDTH, REFERENCE_HEIGHT = REFERENCE_RESOLUTION
pattern_scale = min(screen_w / REFERENCE_WIDTH, screen_h / REFERENCE_HEIGHT)

rows, cols = GRID_RC

# =========================
# 패턴 크기 설정
# =========================
spacing_px = round(160 * pattern_scale)
circle_diameter_px = round(115 * pattern_scale)   # 3840 기준 원 크기
radius_px = circle_diameter_px // 2

margin_x = round(200 * pattern_scale)
margin_y = round(200 * pattern_scale)

# =========================
# 밝기 설정
# =========================
bg_val = 128
bright_val = 255
dark_val = 0

# BLINK_HZ 값의 절반 주기마다 밝음/어두움 상태가 바뀝니다.
fps = 120
frame_dt = 1.0 / fps

# =========================
# 비대칭 원 위치 생성 함수
# =========================
def make_points():
    points = []

    for r in range(rows):
        y = margin_y + r * spacing_px
        x_offset = 0 if r % 2 == 0 else spacing_px

        for c in range(cols):
            x = margin_x + x_offset + 2 * c * spacing_px
            points.append((x, y))

    # 패턴 중앙 정렬
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
# 창 생성
# =========================
win = "Blink Asymmetric Circle Grid"
cv2.namedWindow(win, cv2.WINDOW_NORMAL)
# 전체 화면으로 바꾸기 전에 대상 모니터로 창을 옮깁니다.
cv2.resizeWindow(win, screen_w, screen_h)
cv2.moveWindow(win, monitor["x"], monitor["y"])
cv2.waitKey(50)
cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# =========================
# 비디오 저장 설정
# 필요하면 아래 녹화 관련 주석을 풀어서 사용
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

# 녹화 안 할 때 기본값
recording = False
writer = None

# =========================
# 루프
# =========================
start_time = time.perf_counter()

while True:

    frame_start = time.perf_counter()

    frame = np.full((screen_h, screen_w), bg_val, dtype=np.uint8)

    # 모든 원 같은 색
    state = blink_state(frame_start - start_time)
    circle_color = bright_val if state == 0 else dark_val

    for (x, y) in points:
        cv2.circle(frame, (x, y), radius_px, int(circle_color), -1, lineType=cv2.LINE_AA)

    cv2.imshow(win, frame)

    # =========================
    # 녹화 기능
    # 위쪽 recording = True / writer 생성 주석을 풀면 작동
    # =========================
    if recording and writer is not None:
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        writer.write(frame_bgr)

    key = cv2.waitKey(1) & 0xFF

    # 종료만 키보드로 조작
    if key == ord('q'):
        break

    elapsed = time.perf_counter() - frame_start
    sleep = frame_dt - elapsed
    if sleep > 0:
        time.sleep(sleep)

if writer is not None:
    writer.release()

cv2.destroyAllWindows()
