import time
from gpiozero import LED
from gpiozero import PWMOutputDevice as PWM
# ─── Numéros de broches GPIO pour les LEDs RGB gauche et droite ───────────────
# Chaque LED RGB est composée de 3 canaux : Rouge (R), Vert (G), Bleu (B)
Left_R  = 0 # Canal Rouge  de la LED RGB gauche
Left_G  = 19 # Canal Vert   de la LED RGB gauche
Left_B  = 13 # Canal Bleu   de la LED RGB gauche

Right_R = 1 # Canal Rouge  de la LED RGB droite
Right_G = 5 # Canal Vert   de la LED RGB droite
Right_B = 6 # Canal Bleu   de la LED RGB droite
def switchSetup():
    """
    Initialise tous les périphériques de sortie GPIO.
    Doit être appelée une seule fois au démarrage avant toute utilisation
    des fonctions switch() ou set_all_switch_off().
    """
    global led1,led2,led3, L_R, L_G, L_B, R_R, R_G, R_B
     # LEDs simples (tout-ou-rien) sur les broches 9, 25 et 11
    # Correspondent aux ports 1, 2 et 3 dans switch()
    led1 = LED(9)
    led2 = LED(25)
    led3 = LED(11)
    # LEDs RGB gauche — pilotées en PWM à 2000 Hz
    # initial_value=1.0 → duty cycle à 100% = LED éteinte (logique inverse, cathode commune)
    L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
    L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
    L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)
    R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
    R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
    R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)

def switch(port, status):
    if port == 1:# LED simple n°1 (GPIO 9)
        if status == 1:
            led1.on()
        elif status == 0:
            led1.off()
    elif port == 2:# LED simple n°2 (GPIO 25)
        if status == 1:
            led2.on()
        elif status == 0:
            led2.off()
    elif port == 3:# LED simple n°3 (GPIO 11)
        if status == 1:
            led3.on()
        elif status == 0:
            led3.off()
    elif port == 4:# Canal Rouge  — LED RGB gauche
        if status == 1:
            L_R.value = 0.0# Duty 0%  → tension basse → LED allumée
        elif status == 0:
            L_R.value =1.0# Duty 100% → tension haute → LED éteinte
    elif port == 5:# Canal Vert   — LED RGB gauche
        if status == 1:
            L_G.value = 0.0
        elif status == 0:
            L_G.value =1.0
    elif port == 6:# Canal Bleu   — LED RGB gauche
        if status == 1 :
            L_B.value = 0.0
        elif status == 0 :
            L_B.value =1.0
    elif port == 7:# Canal Rouge  — LED RGB droite
        if status == 1:
            R_R.value = 0.0
        elif status == 0:
            R_R.value =1.0
    elif port == 8:# Canal Vert   — LED RGB droite
        if status == 1 :
            R_G.value = 0.0
        elif status == 0:
            R_G.value =1.0
    elif port == 9:# Canal Bleu   — LED RGB droite
        if status == 1 :
            R_B.value = 0.0
        elif status == 0:
            R_B.value =1.0
    else:
        print('Wrong Command: Example--switch(3, 1)->to switch on port3')
def set_all_switch_off():
    for port in range(1, 10):
        switch(port, 0)
#Point d'entrée principal
if __name__ == "__main__":
    switchSetup() # Initialisation des GPIO avant toute commande
    while True:
        try:
            code = int(input("Entrez un code de commande : "))
        except ValueError:
            print("Veuillez entrer un nombre entier.")
            continue
        time.sleep(1)# Petit délai pour éviter les rebonds de commande rapide
        if 11 <= code <= 19:
             # Codes 11–19 → allumer le port correspondant (11=port1, ..., 19=port9)
            port = code - 10  # 11→1, 12→2, ..., 19→9
            switch(port, 1)
            print(f"LED {port} allumée.")
        elif 21 <= code <= 29:
            # Codes 21–29 → éteindre le port correspondant (21=port1, ..., 29=port9)
            port = code - 20  # 21→1, 22→2, ..., 29→9
            switch(port, 0)
            print(f"LED {port} éteinte.")
        else:
            print("Code inconnu. Utilisez un nombre entre 11 et 29")
