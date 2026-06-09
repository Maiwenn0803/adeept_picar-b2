import time
import argparse
from gpiozero import InputDevice

line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)

def run():
    status_right = right.value
    status_middle = middle.value
    status_left = left.value
    print('left: %d   middle: %d   right: %d' %(status_right,status_middle,status_left))


if __name__ == '__main__':
    try:
      while 1:
        run()
        time.sleep(0.3)
    except KeyboardInterrupt:
        pass

#le programme affiche toute les 0.3 secondes une detection avec les capteurs 
#on voit les 3 capteur : droite milieu gauche, si le capteur ne detecte pas de ligne il met 0 par contre sinon il met 1
# on peut l'utiliser en imaginant une ligne de la taille des 3 capteurs, on lui dit que s'il ne voit plus de ligne sur l'un des trois il tourne pour se retrouver
#sur la ligne (pour suivre la ligne)
# la seconde option est de lui dire que s'il détecte une ligne il tourne pour ne pas dépasser de la ligne.
