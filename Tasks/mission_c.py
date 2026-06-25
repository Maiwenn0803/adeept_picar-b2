import time
import Task4
import Task3 as servo
from Task5 import checkdist
from Task11 import left, middle, right

OBSTACLE_DIST_CM = 20
SPEED_FWD        = 0.3
SPEED_BACK       = -0.3
ANGLE_CENTRE     = 105
ANGLE_DROITE     = 60   # roues → droite
ANGLE_GAUCHE     = 140  # roues → gauche
DUREE_VIRAGE     = 0.6
DUREE_RECUL      = 0.4

# Angles du servo tête pour le balayage
TETE_CENTRE = 100
TETE_DROITE = 70
TETE_GAUCHE = 130

def get_dist():
    return checkdist() / 10  # mm → cm

def bord_detecte():
    return left.value == 0 or middle.value == 0 or right.value == 0

def mesurer_cote(angle_tete):
    """Oriente la tête et mesure la distance."""
    servo.set_angle(1, angle_tete)
    time.sleep(0.3)  # laisse le servo se placer
    dist = get_dist()
    servo.set_angle(1, TETE_CENTRE)
    return dist

def contourner():
    """
    Recule, balaye gauche et droite, puis tourne du côté le plus libre.
    """
    print("[MissionC] Obstacle détecté → recul + balayage")

    # Reculer pour avoir de la place
    servo.set_angle(0, ANGLE_CENTRE)
    Task4.set_throttle(SPEED_BACK)
    time.sleep(DUREE_RECUL)
    Task4.motorStop()
    time.sleep(0.2)

    # Mesurer les deux côtés
    dist_droite = mesurer_cote(TETE_DROITE)
    dist_gauche = mesurer_cote(TETE_GAUCHE)
    print(f"[MissionC] Gauche:{dist_gauche:.1f}cm  Droite:{dist_droite:.1f}cm")

    # Tourner du côté le plus libre
    if dist_gauche < dist_droite:
        print("[MissionC] → Virage gauche")
        servo.set_angle(0, ANGLE_DROITE)
        Task4.set_throttle(SPEED_BACK)
        time.sleep(DUREE_RECUL)
        Task4.motorStop()
        time.sleep(0.2)
        servo.set_angle(0, ANGLE_GAUCHE)
    else:
        print("[MissionC] → Virage droite")
        servo.set_angle(0, ANGLE_GAUCHE)
        Task4.set_throttle(SPEED_BACK)
        time.sleep(DUREE_RECUL)
        Task4.motorStop()
        time.sleep(0.2)
        servo.set_angle(0, ANGLE_DROITE)

    Task4.set_throttle(SPEED_FWD)
    time.sleep(DUREE_VIRAGE)
    servo.set_angle(0, ANGLE_CENTRE)  # remettre les roues droites

def run():
    servo.set_angle(1, TETE_CENTRE)
    time.sleep(0.5)
    print("[MissionC] Démarrage")

    while True:
        dist = get_dist()
        print(f"[MissionC] IR l:{left.value} m:{middle.value} r:{right.value} | dist:{dist:.1f}cm")

        if bord_detecte():
            print("[MissionC] Bord détecté → recul + virage")
            if left.value==1 :
                print("[MissionC] Bord détecté → recul + virage droite")
                servo.set_angle(0, ANGLE_CENTRE)
                Task4.set_throttle(SPEED_BACK)
                time.sleep(DUREE_RECUL)
                servo.set_angle(0, ANGLE_DROITE)
                Task4.set_throttle(SPEED_FWD)
                time.sleep(DUREE_VIRAGE+0.4)
                servo.set_angle(0, ANGLE_CENTRE)
            elif right.value==1 :
                print("[MissionC] Bord détecté → recul + virage gauche")
                servo.set_angle(0, ANGLE_CENTRE)
                Task4.set_throttle(SPEED_BACK)
                time.sleep(DUREE_RECUL)
                servo.set_angle(0, ANGLE_GAUCHE)
                Task4.set_throttle(SPEED_FWD)
                time.sleep(DUREE_VIRAGE+0.4)
                servo.set_angle(0, ANGLE_CENTRE)
            elif left.value==1 and right.value==1 :
                Task4.motorStop()

        if dist < OBSTACLE_DIST_CM:
            contourner()

        else:
            print("[MissionC] → Tout droit")
            servo.set_angle(0, ANGLE_CENTRE)
            Task4.set_throttle(SPEED_FWD)

        time.sleep(0.05)
