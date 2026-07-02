import cv2
import numpy as np
import time
import Task4
import Task3 as servo

ANGLE_CENTRE = 105
ANGLE_DROITE = 60
ANGLE_GAUCHE = 140
SPEED_FWD    = 0.3
DUREE_VIRAGE = 0.8

def detect_arrow(frame):
    """
    Retourne 'gauche', 'droite', ou None selon la flèche détectée.
    Principe : goodFeaturesToTrack → Xmin et Xmax → la pointe est du côté
    où il y a le moins de sommets (le côté de la flèche).
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    corners = cv2.goodFeaturesToTrack(blur, 10, qualityLevel=0.1, minDistance=10)
    if corners is None or len(corners) < 3:
        return None

    coords = corners.reshape(-1, 2)  # shape (N, 2) : colonnes x, y
    xs = coords[:, 0]

    x_min = int(np.min(xs))
    x_max = int(np.max(xs))
    x_mid = (x_min + x_max) / 2

    gauche = np.sum(xs < x_mid)
    droite = np.sum(xs >= x_mid)

    # La pointe de la flèche concentre moins de sommets
    if droite < gauche:
        return 'droite'
    elif gauche < droite:
        return 'gauche'
    return None

def tourner(direction):
    if direction == 'droite':
        print("[Arrow] → Virage DROITE")
        servo.set_angle(0, ANGLE_DROITE)
    else:
        print("[Arrow] → Virage GAUCHE")
        servo.set_angle(0, ANGLE_GAUCHE)
    Task4.set_throttle(SPEED_FWD)
    time.sleep(DUREE_VIRAGE)
    servo.set_angle(0, ANGLE_CENTRE)
    Task4.motorStop()

def run():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        print("[Arrow] Erreur : caméra inaccessible")
        return
    print("[Arrow] Caméra OK")
    if not cap.isOpened():
        print("[Arrow] Erreur : caméra inaccessible")
        return

    servo.set_angle(0, ANGLE_CENTRE)
    print("[Arrow] Démarrage - en attente d'une flèche...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            cv2.imshow("Arrow", frame)
            direction = detect_arrow(frame)

            if direction:
                print(f"[Arrow] Flèche détectée : {direction}")
                tourner(direction)
                time.sleep(1)  # pause avant prochaine détection
            else:
                print("[Arrow] → Tout droit")
                servo.set_angle(0, ANGLE_CENTRE)
                Task4.set_throttle(SPEED_FWD)

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        Task4.motorStop()
        cv2.destroyAllWindows()
        print("[Arrow] Arrêt")
