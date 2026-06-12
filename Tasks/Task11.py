import Task4
import Task3 as servo
from Task9 import *
from gpiozero import InputDevice
import sys
import select
import time

def _safe_input_device(pin):
    try:
        return InputDevice(pin=pin)
    except Exception:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)

        class _PinProxy:
            def __init__(self, p): self._pin = p
            @property
            def value(self): return GPIO.input(self._pin)

        return _PinProxy(pin)

left   = _safe_input_device(22)
middle = _safe_input_device(27)
right  = _safe_input_device(17)
print("[Task11] Capteurs initialisés")

last_angle = 100

def follow_line():
    """
    Suit la ligne.Retourne True si on continue, False si on doit s'arrêter
    (arrêt manuel ou perte de ligne).
    """
    global last_angle
    # 1. Vérification de l'arrêt (manuel ou distance)
    if auto_stop_distance():
        print("\n[Task11] OBSTACLE DÉTECTÉ !")
        Task4.motorStop()
        return False
        
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        if char.lower() == 'a':
            print("\n[Task11] ARRÊT MANUEL !")
            Task4.motorStop()
            return False

    target = 0.25
    second=0
    l = left.value
    m = middle.value
    r = right.value
    
    # Debug optionnel (décommenter si besoin)
    # print(f'[Task11] left:{l}  middle:{m}  right:{r}')

    if l == 1 and m == 1 and r == 1:
        print("[Task11] → Tout droit")
        last_angle = 100
        servo.set_angle(0, last_angle)
        target = 0.4
        second=0

    elif l == 0 and m == 1 and r == 1:
        print("[Task11] → Correction droite (légère)")
        last_angle = 80
        servo.set_angle(0, last_angle)
        target = 0.35
        second=0

    elif l == 1 and m == 1 and r == 0:
        print("[Task11] → Correction gauche (légère)")
        last_angle = 120
        servo.set_angle(0, last_angle)
        target = 0.35
        second=0

    elif l == 0 and m == 0 and r == 1:
        print("[Task11] → Correction droite (forte)")
        last_angle = 60
        servo.set_angle(0, last_angle)
        target = 0.35
        second=0

    elif l == 1 and m == 0 and r == 0:
        print("[Task11] → Correction gauche (forte)")
        last_angle = 140
        servo.set_angle(0, last_angle)
        target = 0.35
        second=0
    else:
        print("[Task11] → Perte de ligne, recul de secours...")
        # Braquer dans le sens opposé au dernier angle connu pour revenir vers la ligne
        recul_angle = 200 - last_angle
        servo.set_angle(0, recul_angle)
        
        # Vitesse un peu réduite pour éviter de dépasser la ligne en reculant
        Task4.drive_generic(30, -1)
        
        # On force un recul minimum pour s'éloigner de la zone de perte
        time.sleep(0.4)
        
        start_recul = time.time()
        found = False
        # On continue de reculer jusqu'à 2s max ou jusqu'à retrouver la ligne
        while time.time() - start_recul < 1.6:
            if left.value == 1 or middle.value == 1 or right.value == 1:
                # Confirmation pour filtrer les faux positifs (bruit capteur)
                time.sleep(0.05)
                if left.value == 1 or middle.value == 1 or right.value == 1:
                    print("[Task11] → Ligne retrouvée avec certitude !")
                    found = True
                    break
            time.sleep(0.05)
            
        Task4.motorStop()
        if not found:
            print("[Task11] → Pas de ligne retrouvée après le recul : Arrêt.")
            # On remet les roues droites avant de s'arrêter
            servo.set_angle(0, 100)
            return False
        
        # On a retrouvé la ligne, on repart doucement
        target = 0.20
    
    Task4.set_throttle(target)
    # On n'applique le throttle que si on n'a pas arrêté le moteur
    return True
