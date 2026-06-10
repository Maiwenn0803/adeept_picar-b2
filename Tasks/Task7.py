import threading
import time
from task1 import *
from task2 import *
from task3 import *
from task4 import *
from Task5 import *
from task6 import *
from task9 import *

running = True

def thread_task1_leds():
    """Gère l'animation des LEDs de la Task 1 en arrière-plan"""
    try:
        while running:
            for port in range(1, 10):
                if not running: break
                # switch(port, 1)
                time.sleep(0.1)
                # switch(port, 0)
                time.sleep(0.1)
    except Exception as e:
        print(f"Erreur Task 1: {e}")

def thread_task2_pixel():
    """Gère l'animation SPI LedPixel de la Task 2 en arrière-plan"""
    try:
        while running:
            # leds.set_all_led_color(255, 0, 0)
            time.sleep(1)
            if not running: break
            # leds.set_all_led_color(0, 255, 0)
            time.sleep(1)
    except Exception as e:
        print(f"Erreur Task 2: {e}")

def thread_task5_distance():
    """Gère la lecture seule du capteur à ultrasons Task 5 en arrière-plan"""
    try:
        while running:
            dist = checkdist()
            time.sleep(0.1) # Fréquence de rafraîchissement de la mesure
    except Exception as e:
        print(f"\nErreur Task 5: {e}")


def thread_task9_auto_stop():
    """
    THREAD DE SÉCURITÉ (Task 9) - Version optimisée anti-spam
    """
    print("[Sécurité] Thread d'arrêt automatique activé.")
    
    # On garde en mémoire si la sécurité a déjà arrêté le moteur
    securite_declenchee = False 
    
    try:
        while running:
            # Remplacer temporairement l'appel direct si auto_stop_distance() print trop.
            # Idéalement, adapte ce bloc selon la logique de ta 'task9.py' :
            
            # Exemple de logique à adapter si tu peux modifier task9 :
            # Ici on imagine que auto_stop_distance() renvoie True si elle a dû couper le moteur
            
            dist = checkdist() # Utilise directement le capteur pour valider la distance
            
            # Seuil critique (ex: 200 mm), à adapter selon tes besoins
            if dist < 200.0: 
                if not securite_declenchee:
                    # On n'agit et ne print QUE la première fois !
                    print("\n[ALERTE SÉCURITÉ] Obstacle détecté ! Arrêt d'urgence.")
                    motorStop()          # Arrêt immédiat direct sans rampe bruyante
                    securite_declenchee = True
            else:
                # L'obstacle a disparu, on réactive la vigilance
                securite_declenchee = False
            
            # On vérifie toutes les 100ms (largement suffisant et plus doux pour le CPU)
            time.sleep(0.1) 
            
    except Exception as e:
        print(f"\nErreur critique dans le thread de sécurité Task 9: {e}")

def manual_control_loop_test():
    """
    4. Commande manuelle interactive pour le test.
    """
    global running
    print("\n" + "="*50)
    print("      INTERFACE DE COMMANDE MANUELLE DU MOTEUR DC")
    print("="*50)
    print(f"Statut matériel réel : {'CONNECTÉ' if HARDWARE_AVAILABLE else 'SIMULATION'}")
    
    # --- LANCEMENT DU THREAD DE SÉCURITÉ AVANT D'ENTRER DANS LA BOUCLE INTERACTIVE ---
    t9 = threading.Thread(target=thread_task9_auto_stop, name="Task9_AutoStop", daemon=True)
    t9.start()
    
    while running:
        print(f"\nPuissance actuelle : {current_throttle*100.0:.1f}% (Throttle: {current_throttle:.2f})")
        print("1 : Marche avant à faible vitesse (25% - direct)")
        print("2 : Marche arrière à faible vitesse (25% - direct)")
        print("3 : Arrêt immédiat (sans rampe)")
        print("4 : Test de rampe standard (0 à 100% en 1.0s, maintient 2s, puis retour à 0)")
        print("5 : Commande générique (Vitesse, Sens, Pente de rampe)")
        print("6 : Commande avec durée (Vitesse, Sens, Durée de rampe)")
        print("q : Arrêt et quitter")

        choice = input("\ Votre choix : ").strip().lower()
        
        if choice == '1':
            drive_low_speed(1)
        elif choice == '2':
            drive_low_speed(-1)
        elif choice == '3':
            motorStop()
        elif choice == '4':
            print("\n--- Début du test de rampe standard ---")
            drive_with_ramp(100, 1, 1.0)
            print("Maintien à 100% pendant 2 secondes...")
            time.sleep(2)
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
            print("\nArrêt global demandé...")
            running = False
            destroy()
            break
        else:
            print("Choix invalide. Veuillez réessayer.")

def main():
    threads = []

    # Création des autres tâches de fond (LEDs, Servo, etc.)
    t1 = threading.Thread(target=thread_task1_leds, name="Task1_LED", daemon=True)
    t2 = threading.Thread(target=thread_task2_pixel, name="Task2_Pixel", daemon=True)
    t5 = threading.Thread(target=thread_task5_distance, name="Task5_Dist", daemon=True)

    threads.extend([t1, t2, t5])

    print("Démarrage des tâches secondaires...")
    for t in threads:
        t.start()

    # Configuration initiale unique pour le servo (Task 3)
    set_angle(0, 100)  

    # Lancement de la boucle de contrôle (qui va elle-même créer le thread de sécurité t9)
    manual_control_loop_test()

    time.sleep(0.5) 
    print("Programme terminé proprement.")

if __name__ == "__main__":
    main()
