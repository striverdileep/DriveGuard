import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist

# Blink detection parameters
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 2

# Load models safely
try:
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    MODEL_READY = True
except Exception as e:
    print(f"⚠️ Liveness model load error: {e}")
    detector = None
    predictor = None
    MODEL_READY = False

# Landmark indexes
(lStart, lEnd) = (42, 48)
(rStart, rEnd) = (36, 42)


def eye_aspect_ratio(eye):

    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])

    ear = (A + B) / (2.0 * C)
    return ear


def check_blink_from_frames(frame_stream):

    if not MODEL_READY:
        print("⚠️ Liveness check unavailable (model not loaded)")
        return False

    blink_counter = 0
    total_blinks = 0
    face_detected = False

    for frame in frame_stream:

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            rects = detector(gray, 0)

            if len(rects) > 0:
                face_detected = True

            for rect in rects:

                shape = predictor(gray, rect)
                shape = np.array([[p.x, p.y] for p in shape.parts()])

                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]

                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)

                ear = (leftEAR + rightEAR) / 2.0

                if ear < EYE_AR_THRESH:
                    blink_counter += 1
                else:
                    if blink_counter >= EYE_AR_CONSEC_FRAMES:
                        total_blinks += 1
                        print(f"👁️ Blink detected! Total: {total_blinks}")
                    blink_counter = 0

        except Exception as e:
            print(f"⚠️ Liveness frame error: {e}")
            continue

    if not face_detected:
        print("⚠️ No face detected during liveness check")
        return False

    print(f"👁️ Total blinks detected: {total_blinks}")

    return total_blinks > 0