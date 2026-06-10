"""
Tâche 4 : Moteur DC
Piloter le moteur DC de déplacement du Robot Picar-B.
"""

import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor

# Définition des broches pour les 4 moteurs (identique à exemple.py)
MOTOR_M1_IN1 = 15      # Pôle positif M1
MOTOR_M1_IN2 = 14      # Pôle négatif M1
MOTOR_M2_IN1 = 12      # Pôle positif M2
MOTOR_M2_IN2 = 13      # Pôle négatif M2
MOTOR_M3_IN1 = 11      # Pôle positif M3
MOTOR_M3_IN2 = 10      # Pôle négatif M3
MOTOR_M4_IN1 = 8       # Pôle positif M4
MOTOR_M4_IN2 = 9       # Pôle négatif M4

# Variable globale pour suivre la puissance actuelle (entre -1.0 et 1.0)
current_throttle = 0.0
HARDWARE_AVAILABLE = False

# Initialisation du matériel ou simulation
try:
    i2c = busio.I2C(SCL, SDA)
    # Utilisation de l'adresse 0x5f comme indiqué dans exemple.py
    pwm_motor = PCA9685(i2c, address=0x5f)
    # exemple.py utilise 50 Hz.
    pwm_motor.frequency = 50

    motor1 = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1], pwm_motor.channels[MOTOR_M1_IN2])
    motor1.decay_mode = motor.SLOW_DECAY
    motor2 = motor.DCMotor(pwm_motor.channels[MOTOR_M2_IN1], pwm_motor.channels[MOTOR_M2_IN2])
    motor2.decay_mode = motor.SLOW_DECAY
    motor3 = motor.DCMotor(pwm_motor.channels[MOTOR_M3_IN1], pwm_motor.channels[MOTOR_M3_IN2])
    motor3.decay_mode = motor.SLOW_DECAY
    motor4 = motor.DCMotor(pwm_motor.channels[MOTOR_M4_IN1], pwm_motor.channels[MOTOR_M4_IN2])
    motor4.decay_mode = motor.SLOW_DECAY
    
    HARDWARE_AVAILABLE = True
    print("[Hardware] Moteurs DC initialisés sur PCA9685 à l'adresse 0x5f (50Hz).")
except Exception as e:
    print(f"[Hardware] ATTENTION: Impossible d'initialiser le matériel réel ({e}).")
    print("[Hardware] Mode SIMULATION activé.")
    
    # Mock pour simuler les moteurs hors ligne
    class MockMotor:
        def __init__(self, name):
            self.name = name
            self._throttle = 0.0
            
        @property
        def throttle(self):
            return self._throttle
            
        @throttle.setter
        def throttle(self, value):
            self._throttle = value
            # Affiche la valeur de simulation en console
            print(f"[Sim] {self.name} throttle = {value:.3f}")

    motor1 = MockMotor("Motor 1")
    motor2 = MockMotor("Motor 2")
    motor3 = MockMotor("Motor 3")
    motor4 = MockMotor("Motor 4")


def set_throttle(val):
    """
    Applique la valeur de throttle (-1.0 à 1.0) sur les 4 moteurs.
    """
    val = max(-1.0, min(1.0, val))
    motor1.throttle = val
    motor2.throttle = val
    motor3.throttle = val
    motor4.throttle = val


def set_throttle_with_ramp(target_throttle, duration):
    """
    Fait varier progressivement le throttle de sa valeur actuelle vers target_throttle
    sur la durée indiquée (en secondes).
    """
    global current_throttle
    target_throttle = max(-1.0, min(1.0, target_throttle))
    
    if duration <= 0 or current_throttle == target_throttle:
        current_throttle = target_throttle
        set_throttle(current_throttle)
        return

    # Pas d'échantillonnage de 20ms pour la rampe
    step_time = 0.02
    steps = int(duration / step_time)
    
    if steps <= 0:
        steps = 1
        
    start_throttle = current_throttle
    throttle_diff = target_throttle - start_throttle
    
    for i in range(1, steps + 1):
        progress = i / steps
        current_throttle = start_throttle + (throttle_diff * progress)
        set_throttle(current_throttle)
        time.sleep(step_time)
        
    # S'assurer de la valeur finale exacte
    current_throttle = target_throttle
    set_throttle(current_throttle)


def drive_low_speed(direction):
    """
    1. Fonction simple de pilotage à faible vitesse (~25% du max)
    avec marche avant, marche arrière, arrêt.
    
    direction : 1 (avant), -1 (arrière), 0 (arrêt)
    Note : Cette fonction applique la vitesse directement (sans rampe).
    """
    global current_throttle
    if direction == 1:
        target = 0.25
    elif direction == -1:
        target = -0.25
    else:
        target = 0.0
        
    current_throttle = target
    set_throttle(target)
    print(f"[Low Speed] Direction={direction}, Throttle={target:.2f}")


def drive_with_ramp(target_speed, direction, ramp_duration=1.0):
    """
    2. Fonction de pilotage avec rampe de montée en vitesse.
    
    target_speed : vitesse cible entre 0 et 100 (%)
    direction : 1 (avant), -1 (arrière), 0 (arrêt)
    ramp_duration : durée de la rampe de transition en secondes.
    """
    speed_fraction = max(0.0, min(100.0, target_speed)) / 100.0
    if direction == -1:
        target_throttle = -speed_fraction
    elif direction == 1:
        target_throttle = speed_fraction
    else:
        target_throttle = 0.0
        
    print(f"[Ramp Drive] Transition de {current_throttle*100.0:.1f}% à {target_throttle*100.0:.1f}% en {ramp_duration:.2f}s...")
    set_throttle_with_ramp(target_throttle, ramp_duration)
    print(f"[Ramp Drive] Vitesse cible atteinte (Throttle = {current_throttle:.2f})")


def drive_generic(speed, direction, ramp_slope=100.0):
    """
    3. Fonction à 3 paramètres : vitesse, sens, pente de la rampe.
    
    speed : vitesse cible entre 0 et 100 (%)
    direction : 1 (avant), -1 (arrière), 0 (arrêt)
    ramp_slope : pente de la rampe en % par seconde (ex: 100 %/s correspond
                 à 0->100% en 1s). Si la pente est <= 0, l'application est directe.
    """
    speed_fraction = max(0.0, min(100.0, speed)) / 100.0
    if direction == -1:
        target_throttle = -speed_fraction
    elif direction == 1:
        target_throttle = speed_fraction
    else:
        target_throttle = 0.0
        
    if ramp_slope <= 0:
        duration = 0.0
    else:
        # Calcul de la différence en pourcentage de vitesse relative (valeur absolue)
        current_speed_pct = current_throttle * 100.0
        target_speed_pct = target_throttle * 100.0
        diff_pct = abs(target_speed_pct - current_speed_pct)
        # Calcul de la durée correspondante
        duration = diff_pct / ramp_slope
        
    print(f"[Generic Drive] Vitesse={speed}%, Sens={direction}, Pente={ramp_slope}%/s -> Durée calculée={duration:.2f}s")
    set_throttle_with_ramp(target_throttle, duration)


def motorStop():
    """Arrête immédiatement tous les moteurs."""
    global current_throttle
    current_throttle = 0.0
    set_throttle(0.0)
    print("[Motor] Arrêt d'urgence appliqué.")


def destroy():
    """Arrête proprement le robot et libère le contrôleur PWM."""
    motorStop()
    if HARDWARE_AVAILABLE:
        try:
            pwm_motor.deinit()
            print("[Motor] PCA9685 désinitialisé.")
        except Exception as e:
            print(f"[Motor] Erreur lors de la désinitialisation : {e}")


def get_float_input(prompt, default=0.0):
    try:
        val = input(prompt)
        if not val.strip():
            return default
        return float(val)
    except ValueError:
        print("Entrée invalide. Utilisation de la valeur par défaut.")
        return default


def get_int_input(prompt, default=0):
    try:
        val = input(prompt)
        if not val.strip():
            return default
        return int(val)
    except ValueError:
        print("Entrée invalide. Utilisation de la valeur par défaut.")
        return default


def manual_control_loop():
    """
    4. Commande manuelle interactive pour le test.
    """
    print("\n" + "="*50)
    print("      INTERFACE DE COMMANDE MANUELLE DU MOTEUR DC")
    print("="*50)
    print(f"Statut matériel réel : {'CONNECTÉ' if HARDWARE_AVAILABLE else 'SIMULATION'}")
    
    while True:
        print(f"\nPuissance actuelle : {current_throttle*100.0:.1f}% (Throttle: {current_throttle:.2f})")
        print("1 : Marche avant à faible vitesse (25% - direct)")
        print("2 : Marche arrière à faible vitesse (25% - direct)")
        print("3 : Arrêt immédiat (sans rampe)")
        print("4 : Test de rampe standard (0 à 100% en 1.0s, maintient 2s, puis retour à 0)")
        print("5 : Commande générique (Vitesse, Sens, Pente de rampe)")
        print("6 : Commande avec durée (Vitesse, Sens, Durée de rampe)")
        print("q : Arrêt et quitter")
        
        choice = input("\nVotre choix : ").strip().lower()
        
        if choice == '1':
            drive_low_speed(1)
        elif choice == '2':
            drive_low_speed(-1)
        elif choice == '3':
            motorStop()
        elif choice == '4':
            print("\n--- Début du test de rampe standard ---")
            # Rampe avant vers 100% en 1s
            drive_with_ramp(100, 1, 1.0)
            print("Maintien à 100% pendant 2 secondes...")
            time.sleep(2)
            # Rampe arrière/arrêt vers 0% en 1s
            drive_with_ramp(0, 1, 1.0)
            print("--- Fin du test de rampe standard ---\n")
        elif choice == '5':
            speed = get_float_input("Vitesse cible (0-100%) : ", 50.0)
            sens = get_int_input("Direction (1=Avant, -1=Arrière, 0=Arrêt) : ", 1)
            pente = get_float_input("Pente de la rampe (% par seconde, ex: 100) : ", 100.0)
            drive_generic(speed, sens, pente)
        elif choice == '6':
            speed = get_float_input("Vitesse cible (0-100%) : ", 50.0)
            sens = get_int_input("Direction (1=Avant, -1=Arrière, 0=Arrêt) : ", 1)
            duree = get_float_input("Durée de la rampe (secondes) : ", 1.0)
            drive_with_ramp(speed, sens, duree)
        elif choice == 'q':
            print("Arrêt du programme de test.")
            destroy()
            break
        else:
            print("Choix invalide. Veuillez réessayer.")


if __name__ == '__main__':
    try:
        manual_control_loop()
    except KeyboardInterrupt:
        print("\nInterruption détectée. Arrêt d'urgence...")
        destroy()
