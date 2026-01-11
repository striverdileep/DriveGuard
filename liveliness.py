# liveness.py
import cv2
import dlib
import time
import numpy as np
from scipy.spatial import distance

# Eye landmark indexes (dlib 68-point model)
LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))

EAR_THRESHOLD = 0.25
CONSEC_FRAMES = 2   # frames eyes must be closed to count as blink


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def check_blink(camera_index=0, duration=2):
    """
    Checks if a real person blinks within 'duration' seconds.
    Returns True if blink detected, else False.
    """

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    cap = cv2.VideoCapture(camera_index)
    start = time.time()

    blink_counter = 0
    closed_frames = 0

    while time.time() - start < duration:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)

        for face in faces:
            shape = predictor(gray, face)
            shape = np.array([[p.x, p.y] for p in shape.parts()])

            left_eye = shape[LEFT_EYE]
            right_eye = shape[RIGHT_EYE]

            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

            if ear < EAR_THRESHOLD:
                closed_frames += 1
            else:
                if closed_frames >= CONSEC_FRAMES:
                    blink_counter += 1
                closed_frames = 0

        if blink_counter >= 1:
            cap.release()
            return True

    cap.release()
    return False
