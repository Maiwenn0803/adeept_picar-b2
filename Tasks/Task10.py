"""
Tâche 10 : Suivi de source lumineuse et obstacle
=================================================
But : Suivre une source lumineuse (torche téléphone),
      arrêt puis dégagement si obstacle.

Commandes :
  'M' → Démarrer le suivi
  'A' → Arrêt immédiat
  'Q' → Quitter le programme

Séquence obstacle (< 20 cm) :
  1. Arrêt moteur + feux de détresse
  2. Pause 1 seconde
  3. Recul ~30 cm à vitesse réduite + bip bip
  4. Arrêt 2 secondes
  5. Reprise du suivi
"""

import time
import threading

from gpiozero import TonalBuzzer

# ─────────────────────────────────────────────────
#  Imports des modules matériels (tâches précédentes)
# ─────────────────────────────────────────────────
import Task3_1 as servo         # Servomoteurs (PCA9685)
import Task4   as motor         # Moteur DC
from Task5     import checkdist # Capteur ultrasonique (renvoie en mm)
from Task8     import ADS7830   # Capteur de lumière (ADC I2C)
from Task2     import Adeept_SPI_LedPixel  # LEDs WS2812


# ══════════════════════════════════════════════════
#  CONSTANTES  (à calibrer sur le robot réel)
# ══════════════════════════════════════════════════

# --- Détection d'obstacle ---
OBSTACLE_THRESHOLD_MM = 200         # 20 cm en millimètres

# --- Vitesses moteur (0–100 %) ---
FORWARD_SPEED         = 30          # vitesse de suivi de lumière
REVERSE_SPEED         = 20          # vitesse de recul (réduite)
RAMP_DURATION         = 0.7        # durée d'une rampe d'accélération (s)

# --- Direction (servo canal 0) ---
STEER_CHANNEL         = 0           # canal PCA9685 du servo de direction
STEER_CENTER          = 90          # angle neutre (roues droites)
STEER_MAX_TURN        = 40          # amplitude de braquage max (±40°)

# --- Capteur de lumière ---
LIGHT_CENTER          = 128         # valeur neutre du capteur (à calibrer)

# --- Temporisations séquence obstacle ---
OBSTACLE_PAUSE        = 1.0        # pause avant recul (s)
REVERSE_TIME          = 2.0        # durée du recul pour ~30 cm (à calibrer)
POST_REVERSE_WAIT     = 2.0        # pause après recul (s)

# --- Buzzer ---
BUZZER_PIN            = 18
BEEP_NOTE             = "A5"       # note du bip
BEEP_ON               = 0.15       # durée d'un bip (s)
BEEP_OFF              = 0.15       # silence entre bips (s)

# --- Boucle principale ---
LOOP_PERIOD           = 0.05       # 50 ms entre chaque itération


# ══════════════════════════════════════════════════
#  INITIALISATION DU MATÉRIEL
# ══════════════════════════════════════════════════

adc    = ADS7830()                             # capteur de lumière
buzzer = TonalBuzzer(BUZZER_PIN)               # buzzer
led    = Adeept_SPI_LedPixel(14, 255)          # 14 LEDs WS2812


# ══════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════

# ─── Capteur de lumière ──────────────────────────

def read_light():
    """
    Lit la valeur brute du capteur de lumière (0–255).
    Valeur haute → lumière venant de la gauche.
    Valeur basse → lumière venant de la droite.
    """
    return adc.analogRead(1)


def compute_steering(light_value):
    """
    Convertit la lecture du capteur de lumière en angle de direction.

    Entrée  : light_value (0–255), centre ≈ LIGHT_CENTER
    Sortie  : angle servo entre (CENTER - MAX_TURN) et (CENTER + MAX_TURN)
    """
    # Écart par rapport au centre : négatif → droite, positif → gauche
    offset = light_value - LIGHT_CENTER

    # Normalisation dans [-1.0 , +1.0]
    normalized = max(-1.0, min(1.0, offset / LIGHT_CENTER))

    # Conversion en angle servo
    angle = STEER_CENTER + normalized * STEER_MAX_TURN
    return round(angle, 1)


# ─── Direction ───────────────────────────────────

def steer_to(angle):
    """Applique un angle de direction au servo."""
    servo.set_angle(STEER_CHANNEL, angle)


def steer_straight():
    """Remet les roues droites."""
    steer_to(STEER_CENTER)


# ─── Feux de détresse (LEDs WS2812) ─────────────

def hazard_lights_on():
    """Allume toutes les LEDs en orange (feux de détresse)."""
    led.set_all_led_color(255, 165, 0)


def hazard_lights_off():
    """Éteint toutes les LEDs WS2812."""
    led.set_all_led_color(0, 0, 0)


# ─── Buzzer (bip bip de recul) ───────────────────

def beep_loop(stop_event):
    """
    Émet des bips répétés jusqu'à ce que stop_event soit activé.
    Destiné à tourner dans un thread séparé.
    """
    while not stop_event.is_set():
        buzzer.play(BEEP_NOTE)
        time.sleep(BEEP_ON)
        buzzer.stop()
        time.sleep(BEEP_OFF)


# ══════════════════════════════════════════════════
#  SÉQUENCE OBSTACLE
# ══════════════════════════════════════════════════

def obstacle_sequence():
    """
    Gère la détection d'un obstacle en 4 étapes :
      1. Arrêt moteur + feux de détresse
      2. Pause 1 seconde
      3. Recul ~30 cm avec bip bip (en parallèle)
      4. Arrêt 2 secondes, extinction des feux
    """
    # ── Étape 1 : Arrêt + feux de détresse ──
    motor.motorStop()
    steer_straight()
    hazard_lights_on()
    print("\n[Obstacle] Détecté ! Arrêt + feux de détresse.")

    # ── Étape 2 : Pause 1 seconde ──
    time.sleep(OBSTACLE_PAUSE)

    # ── Étape 3 : Recul avec bip bip ──
    print("[Obstacle] Recul ~30 cm avec bip bip...")

    # Lancer les bips dans un thread séparé
    beep_stop  = threading.Event()
    beep_thread = threading.Thread(
        target=beep_loop, args=(beep_stop,), daemon=True
    )
    beep_thread.start()

    # Reculer : rampe montante → maintien → rampe descendante
    motor.drive_with_ramp(REVERSE_SPEED, -1, RAMP_DURATION)
    time.sleep(REVERSE_TIME)
    motor.drive_with_ramp(0, -1, RAMP_DURATION)

    # Arrêter les bips
    beep_stop.set()
    beep_thread.join()
    buzzer.stop()

    # ── Étape 4 : Arrêt complet + pause 2 secondes ──
    motor.motorStop()
    hazard_lights_off()
    print("[Obstacle] Pause 2 secondes avant reprise...")
    time.sleep(POST_REVERSE_WAIT)
    print("[Obstacle] Reprise du suivi.")


# ══════════════════════════════════════════════════
#  LECTURE CLAVIER (thread séparé, non bloquant)
# ══════════════════════════════════════════════════

def input_reader(command_holder, running_event):
    """Lit les entrées clavier en boucle et stocke la dernière commande."""
    while running_event.is_set():
        try:
            cmd = input().strip().upper()
            command_holder["value"] = cmd
        except EOFError:
            break


# ══════════════════════════════════════════════════
#  NETTOYAGE
# ══════════════════════════════════════════════════

def cleanup():
    """Arrête proprement tout le matériel."""
    motor.motorStop()
    motor.destroy()
    buzzer.stop()
    hazard_lights_off()
    led.led_close()
    steer_straight()
    print("[Main] Nettoyage terminé.")


# ══════════════════════════════════════════════════
#  BOUCLE PRINCIPALE
# ══════════════════════════════════════════════════

def main():
    """
    Machine à états principale :
      IDLE     → en attente de la commande 'M'
      TRACKING → suivi de lumière actif, surveillance obstacle
    """
    # ─── États ───
    STATE_IDLE     = "IDLE"
    STATE_TRACKING = "TRACKING"

    state     = STATE_IDLE
    is_moving = False           # True quand le moteur avance déjà

    # ─── Bannière ───
    print("=" * 50)
    print("  TÂCHE 10 : Suivi de lumière + Obstacle")
    print("=" * 50)
    print("  'M' → Démarrer le suivi")
    print("  'A' → Arrêt immédiat")
    print("  'Q' → Quitter le programme")
    print("=" * 50)

    # ─── Thread clavier ───
    command = {"value": None}
    running = threading.Event()
    running.set()

    kb_thread = threading.Thread(
        target=input_reader, args=(command, running), daemon=True
    )
    kb_thread.start()

    # ─── Boucle ───
    try:
        while running.is_set():

            # ── Lire et consommer la commande ──
            cmd = command["value"]
            command["value"] = None

            # ── Commande : Quitter ──
            if cmd == "Q":
                print("\n[Main] Arrêt du programme.")
                break

            # ── Commande : Arrêt immédiat ──
            if cmd == "A":
                if state == STATE_TRACKING:
                    motor.motorStop()
                    hazard_lights_off()
                    steer_straight()
                    is_moving = False
                    print("\n[Main] Arrêt manuel.")
                state = STATE_IDLE

            # ── Commande : Démarrage ──
            if cmd == "M" and state == STATE_IDLE:
                print("[Main] Démarrage du suivi de lumière.")
                state = STATE_TRACKING
                is_moving = False       # la prochaine itération lancera le moteur

            # ── État TRACKING ──
            if state == STATE_TRACKING:

                # 1) Vérifier la présence d'un obstacle
                distance_mm = checkdist()

                if distance_mm < OBSTACLE_THRESHOLD_MM:
                    is_moving = False
                    obstacle_sequence()
                    # Après la séquence, on reste en TRACKING ;
                    # le moteur redémarrera à la prochaine itération.
                    continue

                # 2) Lire la lumière et ajuster la direction
                light_val   = read_light()
                steer_angle = compute_steering(light_val)
                steer_to(steer_angle)

                # 3) Démarrer le moteur si ce n'est pas déjà fait
                if not is_moving:
                    motor.drive_with_ramp(FORWARD_SPEED, 1, RAMP_DURATION)
                    is_moving = True

                # 4) Affichage de suivi (sur une seule ligne)
                print(
                    f"\r[Tracking] Lumière={light_val:3d}  "
                    f"Dir={steer_angle:5.1f}°  "
                    f"Dist={distance_mm:6.0f}mm   ",
                    end="", flush=True
                )

            time.sleep(LOOP_PERIOD)

    except KeyboardInterrupt:
        print("\n[Main] Interruption Ctrl-C.")

    finally:
        running.clear()
        cleanup()


# ══════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    main()
