# liveliness.py

import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
import os

# ---------------- CONFIG ----------------
EYE_AR_THRESH = 0.25

# ---------------- LOAD MODELS ----------------
MODEL_READY = False
shape_predictor_path = "shape_predictor_68_face_landmarks.dat"

# dlib
if os.path.exists(shape_predictor_path):
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(shape_predictor_path)
    MODEL_READY = True
    print("✅ Dlib model loaded")
else:
    print("❌ Shape predictor missing")

# OpenCV backup face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Eye indexes
(lStart, lEnd) = (42, 48)
(rStart, rEnd) = (36, 42)

# ---------------- EAR FUNCTION ----------------
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# ---------------- GET LATEST IMAGE ----------------
def get_latest_face_image(base_path="data/sessions"):
    latest_file = None
    latest_time = 0

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file == "user_face.jpg":
                full_path = os.path.join(root, file)
                t = os.path.getmtime(full_path)

                if t > latest_time:
                    latest_time = t
                    latest_file = full_path

    return latest_file

# ---------------- MAIN FUNCTION ----------------
def check_liveness(cam):

    if not MODEL_READY:
        print("⚠️ Liveness unavailable")
        return False

    print("\n🟢 LIVENESS CHECK (Enhanced)")
    print("👉 Detecting face + eye validation...")

    face_path = get_latest_face_image()

    if face_path is None:
        print("❌ No face image found")
        return False

    print(f"📂 Using image: {face_path}")

    frame = cv2.imread(face_path)

    if frame is None:
        print("❌ Failed to load image")
        return False

    # ---------------- IMAGE IMPROVEMENT ----------------
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)   # 🔥 improves contrast

    # ---------------- STEP 1: Try DLIB ----------------
    rects = detector(gray, 0)

    # ---------------- STEP 2: FALLBACK TO OPENCV ----------------
    if len(rects) == 0:
        print("⚠️ Dlib failed → Trying OpenCV detector...")

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            print("❌ No face detected (both methods failed)")
            return False

        # Convert OpenCV face to dlib rectangle
        (x, y, w, h) = faces[0]
        rects = [dlib.rectangle(int(x), int(y), int(x+w), int(y+h))]

    # ---------------- LANDMARK PROCESS ----------------
    for rect in rects:
        shape = predictor(gray, rect)
        shape = np.array([[p.x, p.y] for p in shape.parts()])

        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]

        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0

        print(f"EAR: {ear:.3f}")

        if ear > EYE_AR_THRESH:
            print("✅ Eyes open → Real face")
            return True
        else:
            print("⚠️ Eyes closed → Try again")
            return False

    return False

# ---------------- TEST ----------------
if __name__ == "__main__":
    print("Run from Main_File.py")
