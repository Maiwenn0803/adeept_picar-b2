from mission_c import ANGLE_CENTRE
import cv2
import numpy as np
import time, sys, select
from Task4 import *
from Task3 import *
from Task9 import *
from Task1 import *
from mission_c import *
from threading import Event, Thread
import os
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"
channel = 0
import time
import socket


# PD gains
Kp = 24
Kd = 10

# 1. VITESSES REDUITES POUR LE DEBUG
SPEED_STRAIGHT = 50  # % vitesse ligne droite (baisse)
SPEED_TURNING  = 50   # % vitesse en virage (baisse)
MAX_STEERING_DELTA = 50

STOPPED = 0
RUNNING = 1
state = STOPPED

prev_error      = 0.0
last_steering = 0.0

obstacle_thread = None
obstacle_stop_event = None

vidcap = cv2.VideoCapture(0, cv2.CAP_V4L2)
vidcap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
vidcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

def apply_steering(user_angle):
    clamped = max(
        ANGLE_CENTRE - MAX_STEERING_DELTA,
        min(ANGLE_CENTRE + MAX_STEERING_DELTA, user_angle),
    )
    set_angle(channel, clamped)

def start_move():
    global state, obstacle_thread, obstacle_stop_event
    global prev_error, last_steering

    obstacle_stop_event = Event()
    obstacle_thread = Thread(
        target=auto_stop_distance,
        args=(),
        daemon=True,
    )
    obstacle_thread.start()
    set_throttle(0.3)
    state = RUNNING
    prev_error = 0.0
    last_steering = 0.0
    print("-> Suivi ligne par camera demarre (Vitesse reduite)")

def stop_robot(reason="manuel"):
    global state, obstacle_thread, obstacle_stop_event

    if obstacle_stop_event is not None:
        obstacle_stop_event.set()
    if obstacle_thread and obstacle_thread.is_alive():
        obstacle_thread.join(timeout=0.2)
    obstacle_thread = None
    obstacle_stop_event = None
    motorStop()
    apply_steering(ANGLE_CENTRE)
    state = STOPPED
    print("-> Arret (%s)" % reason)

def check_keyboard():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip().upper()
    return None

if __name__ == '__main__':
    set_angle(0, 105)
    switchSetup()
    set_angle(1, 100)
    set_angle(2, 70)
    print("=== Debug Vision - Suivi de ligne ===")
    print("  M : demarrer")
    print("  A : arret")
    print("  Ctrl-C : quitter")
    try:
        if not vidcap.isOpened():
            print("Erreur: Impossible d'ouvrir la camera")
            sys.exit(1)

        while True:
            cmd = check_keyboard()
            if cmd == "M" and state == STOPPED:
                start_move()
            elif cmd == "A" and state != STOPPED:
                stop_robot(reason="manuel")

            ret, frame = vidcap.read()
            if not ret:
                continue

            height, width, _ = frame.shape

            # Definition de la zone de recherche (Region of Interest)
            roi_top = int(height * 2/3)
            roi = frame[roi_top:height, 0:width]

            # Dessiner un rectangle bleu pour visualiser la zone de recherche (ROI)
            cv2.rectangle(frame, (0, roi_top), (width, height), (255, 0, 0), 2)

            if state == RUNNING:
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                lower_red = np.array([0, 150, 150])
                upper_red = np.array([10, 255, 255])
                mask = cv2.inRange(hsv, lower_red, upper_red)

                M = cv2.moments(mask)
                if M['m00'] > 0:
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    center_img = width / 2

                    error = center_img - cx
                    derivative = error - prev_error
                    steering = Kp * (error / (width/2)) + Kd * derivative
                    steering = max(-MAX_STEERING_DELTA, min(MAX_STEERING_DELTA, steering))

                    apply_steering(ANGLE_CENTRE + steering)
                    last_steering = steering
                    prev_error = error

                    speed = SPEED_STRAIGHT if abs(steering) < 8 else SPEED_TURNING
                    set_throttle(0.3)

                    # 2. AFFICHAGE DES DECISIONS SUR L'IMAGE
                    # Dessiner un cercle vert sur le centre detecte
                    cv2.circle(frame, (cx, roi_top + cy), 8, (0, 255, 0), -1)
                    # Afficher les valeurs mathematiques
                    cv2.putText(frame, f"Err: {error:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame, f"Braq: {steering:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    apply_steering(ANGLE_CENTRE + last_steering)
                    set_throttle(0.3)
                    # Afficher une alerte rouge si la ligne est perdue
                    cv2.putText(frame, "LIGNE PERDUE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # 3. AFFICHER LE RETOUR VIDEO EN DIRECT
                cv2.imshow("Debug Robot Vision", frame)

                # Necessaire pour que la fenetre cv2 s'actualise
                cv2.waitKey(1)
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nFin de programme par Ctrl-C")
    finally:
        set_angle(1, 100)
        set_angle(0, 105)
        motorStop()
        set_all_switch_off()
        vidcap.release()
        cv2.destroyAllWindows()
        print("Nettoyage final realise")
