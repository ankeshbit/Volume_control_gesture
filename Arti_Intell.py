import cv2
import mediapipe as mp
import numpy as np
import math

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


devices = AudioUtilities.GetSpeakers()

interface = devices.Activate(
    IAudioEndpointVolume._iid_,
    CLSCTX_ALL,
    None
)

volume_controller = cast(interface, POINTER(IAudioEndpointVolume))

min_volume, max_volume, _ = volume_controller.GetVolumeRange()


mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


cap = cv2.VideoCapture(0)


while True:

    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            landmark_list = []

            h, w, _ = frame.shape

            for idx, lm in enumerate(hand_landmarks.landmark):
                x = int(lm.x * w)
                y = int(lm.y * h)
                landmark_list.append((idx, x, y))

            thumb_x, thumb_y = landmark_list[4][1], landmark_list[4][2]
            index_x, index_y = landmark_list[8][1], landmark_list[8][2]

            cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (index_x, index_y), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (0, 255, 0), 3)

            distance = math.hypot(index_x - thumb_x, index_y - thumb_y)

            volume_level = np.interp(distance, [20, 200], [min_volume, max_volume])
            volume_controller.SetMasterVolumeLevel(volume_level, None)

            volume_percent = np.interp(distance, [20, 200], [0, 100])
            volume_bar = np.interp(distance, [20, 200], [400, 150])

            cv2.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 3)
            cv2.rectangle(frame, (50, int(volume_bar)), (85, 400), (0, 255, 0), cv2.FILLED)

            cv2.putText(
                frame,
                f"{int(volume_percent)} %",
                (40, 450),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                3
            )

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("Hand Gesture Volume Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break


cap.release()
cv2.destroyAllWindows()