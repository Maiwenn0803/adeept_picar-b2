import time
import argparse
import  Task4
import Task3 as servo
from gpiozero import InputDevice

line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)

def follow_line():
    """
    avance en suivant une ligne
    """
    global current_throttle
    target = 0.25
    l = left.value  # 1 = noir, 0 = blanc
    m = middle.value
    r = right.value
    print(f'left:{l}  middle:{m}  right:{r}')
    # ── Décision de direction ──────────────────────────────────────────────────
    if m == 1 and l == 1 and r == 1:
        # Centré sur la ligne
        print("reste droit")

    elif l == 1 and m == 1 and r == 0:
        # Ligne légèrement à gauche → corriger vers la gauche
        servo.set_angle(0,110)

    elif l == 0 and m == 1 and r == 1:
        # Ligne légèrement à droite → corriger vers la droite
        servo.set_angle(0,120)
    current_throttle = target
    Task4.set_throttle(target)
    print(f"[Low Speed] Direction=avant, Throttle={target:.2f}")
