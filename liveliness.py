# liveness.py
import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist

# EAR parameters
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 2

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = (42, 48)
(rStart, rEnd) = (36, 42)


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def check_blink_from_frames(frame_stream):
    """
    Performs blink detection from a frame generator.
    Returns True if at least one blink is detected.
    """
    blink_counter = 0
    total_blinks = 0

    for frame in frame_stream:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        rects = detector(gray, 0)

        for rect in rects:
            shape = predictor(gray, rect)
            shape = np.array([[p.x, p.y] for p in shape.parts()])

            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]

            ear = (eye_aspect_ratio(leftEye) +
                   eye_aspect_ratio(rightEye)) / 2.0

            if ear < EYE_AR_THRESH:
                blink_counter += 1
            else:
                if blink_counter >= EYE_AR_CONSEC_FRAMES:
                    total_blinks += 1
                blink_counter = 0

    return total_blinks > 0
