import cv2
import numpy as np
import time

# =========================
# 화면 설정
# =========================
screen_w = 3840
screen_h = 2160

cols = 11
rows = 4

# =========================
# 패턴 크기 설정
# =========================
spacing_px = 160
circle_diameter_px = 115   # 여기 숫자만 바꾸면 원 크기 조절
radius_px = circle_diameter_px // 2

margin_x = 200
margin_y = 200

# =========================
# 밝기 설정
# =========================
bg_val = 128
bright_val = 255
dark_val = 0

fps = 60
frame_dt = 1.0 / fps

toggle_every = 2

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

points = make_points()

# =========================
# 창 생성
# =========================
win = "Blink Asymmetric Circle Grid"
cv2.namedWindow(win, cv2.WINDOW_NORMAL)
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
frame_idx = 0
state = 0

while True:

    start = time.time()

    frame = np.full((screen_h, screen_w), bg_val, dtype=np.uint8)

    # 모든 원 같은 색
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

    frame_idx += 1

    if frame_idx % toggle_every == 0:
        state = 1 - state

    elapsed = time.time() - start
    sleep = frame_dt - elapsed
    if sleep > 0:
        time.sleep(sleep)

if writer is not None:
    writer.release()

cv2.destroyAllWindows()
