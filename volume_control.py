import argparse
import math
import sys
import time

import cv2
import numpy as np

WINDOW_NAME = "Hand Gesture Volume Control"

MIN_RATIO = 0.15
MAX_RATIO = 1.00

SMOOTHING = 0.25
MIN_VOLUME_STEP = 0.01

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

THUMB_TIP, INDEX_TIP = 4, 8
WRIST, MIDDLE_MCP = 0, 9


def get_volume_controller():
    if sys.platform != "win32":
        sys.exit("This project controls system volume through pycaw, "
                 "which only works on Windows.")

    try:
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError as exc:
        sys.exit(f"Missing dependency ({exc}). Run: pip install -r requirements.txt")

    speakers = AudioUtilities.GetSpeakers()
    if speakers is None:
        sys.exit("No audio output device found.")

    if hasattr(speakers, "EndpointVolume"):
        return speakers.EndpointVolume

    interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def create_hand_tracker():
    import mediapipe as mp

    if not hasattr(mp, "solutions"):
        sys.exit("Your mediapipe version no longer includes 'mp.solutions'. "
                 "Run: pip install mediapipe==0.10.14")

    hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )
    return mp, hands


def open_camera(index):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        sys.exit(f"Could not open camera {index}. Is it in use by another app?")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return cap


def landmark_xy(landmark, width, height):
    return landmark.x * width, landmark.y * height


def pinch_to_volume(thumb, index, wrist, middle_mcp):
    palm_size = math.dist(wrist, middle_mcp)
    if palm_size < 1e-6:
        return None
    ratio = math.dist(thumb, index) / palm_size
    return float(np.interp(ratio, [MIN_RATIO, MAX_RATIO], [0.0, 1.0]))


def draw_volume_bar(frame, volume):
    bar_top = int(np.interp(volume, [0.0, 1.0], [400, 150]))
    cv2.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(frame, (50, bar_top), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(frame, f"{int(round(volume * 100))} %", (40, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)


def run(camera_index, mirror):
    volume_controller = get_volume_controller()
    mp, hands = create_hand_tracker()
    cap = open_camera(camera_index)

    try:
        current_volume = volume_controller.GetMasterVolumeLevelScalar()
    except Exception:
        current_volume = 0.5
    smoothed = current_volume
    last_set = current_volume

    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera frame could not be read. Exiting.")
                break

            if mirror:
                frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                lm = hand.landmark

                thumb = landmark_xy(lm[THUMB_TIP], w, h)
                index = landmark_xy(lm[INDEX_TIP], w, h)
                wrist = landmark_xy(lm[WRIST], w, h)
                middle_mcp = landmark_xy(lm[MIDDLE_MCP], w, h)

                target = pinch_to_volume(thumb, index, wrist, middle_mcp)

                if target is not None:
                    smoothed += SMOOTHING * (target - smoothed)

                    if abs(smoothed - last_set) >= MIN_VOLUME_STEP:
                        try:
                            volume_controller.SetMasterVolumeLevelScalar(
                                float(np.clip(smoothed, 0.0, 1.0)), None)
                            last_set = smoothed
                        except Exception as exc:
                            print(f"Could not set volume: {exc}")

                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand, mp.solutions.hands.HAND_CONNECTIONS)

                p1 = (int(thumb[0]), int(thumb[1]))
                p2 = (int(index[0]), int(index[1]))
                cv2.circle(frame, p1, 10, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, p2, 10, (255, 0, 0), cv2.FILLED)
                cv2.line(frame, p1, p2, (0, 255, 0), 3)

            draw_volume_bar(frame, smoothed)

            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - prev_time, 1e-6))
            prev_time = now
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        hands.close()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Hand gesture volume control")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default 0)")
    parser.add_argument("--no-mirror", action="store_true", help="Do not mirror the video")
    args = parser.parse_args()
    run(args.camera, mirror=not args.no_mirror)


if __name__ == "__main__":
    main()
