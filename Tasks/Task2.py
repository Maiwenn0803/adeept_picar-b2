import spidev
import threading
import numpy
from numpy import sin, cos, pi
import time


class Adeept_SPI_LedPixel(threading.Thread):
    """
    #Classe principale pour contrôler le bandeau de LEDs WS2812 via le bus SPI.
    #Hérite de threading.Thread pour faire tourner les animations en arrière-plan.
    """

    def __init__(self, count=14, bright=255, sequence='GRB', bus=0, device=0, *args, **kwargs):
        """
        Initialisation du contrôleur de LEDs.
        count: Nombre de LEDs dans le bandeau (défaut : 14)
        bright: Luminosité globale de 0 à 255 (défaut : 255 = max)
        sequence: Ordre des canaux couleur selon le modèle de LED (ex: 'GRB', 'RGB')
        bus: Numéro du bus SPI (défaut : 0 = SPI0 sur Raspberry Pi)
        device: Numéro du device SPI (chip select, défaut : 0)
        """
        self.set_led_type(sequence)          # Configure l'ordre des canaux RGB
        self.set_led_count(count)            # Definition du nombre de LED
        self.set_led_brightness(bright)      # Luminosité initiale
        self.led_begin(bus, device)          # Ouvre la connexion SPI

        # Mode d'animation actif ('none', 'police', 'breath')
        self.lightMode = 'none'

        # Couleur cible pour l'effet de respiration (breath)
        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10               # Nombre de paliers pour l'effet de fondu

        self.set_all_led_color(0, 0, 0)     # Éteint toutes les LEDs au démarrage

        # Initialisation du thread parent
        super(Adeept_SPI_LedPixel, self).__init__(*args, **kwargs)

        # Événement de synchronisation : bloque le thread quand aucune animation n'est active
        self.__flag = threading.Event()
        self.__flag.clear()  # Le thread démarre en état "pause"

# ---Initialisation et gestion du bus SPI---

    def led_begin(self, bus=0, device=0):
        """
        Ouvre la connexion SPI avec le device spécifié.
        En cas d'échec (OSError), affiche des instructions de configuration.
        """
        self.bus = bus
        self.device = device
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0           # Mode SPI 0 : CPOL=0, CPHA=0 (requis pour WS2812)
            self.led_init_state = 1     # Connexion réussie
        except OSError:
            print("Please check the configuration in /boot/firmware/config.txt.")
            if self.bus == 0:
                print("You can turn on the 'SPI' in 'Interface Options' by using 'sudo raspi-config'.")
                print("Or make sure that 'dtparam=spi=on' is not commented, then reboot the Raspberry Pi.")
            else:
                print("Please add 'dtoverlay=spi{}-2cs' at the bottom of /boot/firmware/config.txt.".format(self.bus, self.bus))
            self.led_init_state = 0     # Échec de connexion

    def check_spi_state(self):
        """Retourne 1 si le SPI est opérationnel, 0 sinon."""
        return self.led_init_state

    def spi_gpio_info(self):
        """Affiche les numéros de broches GPIO correspondant au bus SPI sélectionné (utile pour le câblage)."""
        if self.bus == 0:
            print("SPI0-MOSI: GPIO10(WS2812-PIN)  SPI0-MISO: GPIO9  SPI0-SCLK: GPIO11  ...")
        # (... autres bus similaires omis pour clarté ...)

    def led_close(self):
        """Éteint toutes les LEDs et ferme proprement la connexion SPI."""
        self.set_all_led_rgb([0, 0, 0])
        self.spi.close()

# ---Configuration des LEDs---

    def set_led_count(self, count):
        """
        Définit le nombre de LEDs et initialise les tableaux de couleurs.
        Chaque LED est représentée par 3 valeurs (R, G, B) dans un tableau plat.
        """
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count           # Couleurs avec luminosité appliquée
        self.led_original_color = [0, 0, 0] * self.led_count  # Couleurs originales (avant ajustement luminosité)

    def set_led_type(self, rgb_type):
        """
        Configure les décalages (offsets) R, G, B selon l'ordre des canaux du modèle de LED.
        Certaines LEDs WS2812 utilisent l'ordre GRB au lieu de RGB.
        Les valeurs encodées en hexadécimal définissent la position de chaque canal.
        """
        try:
            led_type = ['RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR']
            led_type_offset = [0x06, 0x09, 0x12, 0x21, 0x18, 0x24]  # Encodage des positions sur 2 bits chacun
            index = led_type.index(rgb_type)
            # Extraction des positions R, G, B depuis l'octet encodé (bits 5-4, 3-2, 1-0)
            self.led_red_offset   = (led_type_offset[index] >> 4) & 0x03
            self.led_green_offset = (led_type_offset[index] >> 2) & 0x03
            self.led_blue_offset  = (led_type_offset[index] >> 0) & 0x03
            return index
        except ValueError:
            # Type inconnu → ordre GRB par défaut
            self.led_red_offset   = 1
            self.led_green_offset = 0
            self.led_blue_offset  = 2
            return -1

    def set_led_brightness(self, brightness):
        """
        Applique une luminosité globale (0–255) à toutes les LEDs.
        Recalcule les valeurs de couleur en tenant compte du facteur de luminosité.
        """
        self.led_brightness = brightness
        for i in range(self.led_count):
            self.set_led_rgb_data(i, self.led_original_color)

# ---Méthodes de réglage des couleurs (sans/avec envoi immédiat)---

    def set_ledpixel(self, index, r, g, b):
        """
        Méthode centrale : stocke la couleur d'une LED avec ajustement de luminosité.
        - Sauvegarde la couleur originale (pour recalcul si la luminosité change)
        - Calcule la valeur réelle envoyée aux LEDs en tenant compte de led_brightness
        - Place les valeurs dans le bon ordre selon le type de LED (GRB, RGB, etc.)
        """
        p = [0, 0, 0]
        # Mise à l'échelle selon la luminosité globale
        p[self.led_red_offset]   = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset]  = round(b * self.led_brightness / 255)

        # Sauvegarde de la couleur d'origine (sans mise à l'échelle)
        self.led_original_color[index * 3 + self.led_red_offset]   = r
        self.led_original_color[index * 3 + self.led_green_offset] = g
        self.led_original_color[index * 3 + self.led_blue_offset]  = b

        # Stockage de la couleur ajustée dans le tableau d'envoi
        for i in range(3):
            self.led_color[index * 3 + i] = p[i]

    def set_led_color_data(self, index, r, g, b):
        """Modifie la couleur d'une LED (sans envoi SPI)."""
        self.set_ledpixel(index, r, g, b)

    def set_led_rgb_data(self, index, color):
        """Modifie la couleur d'une LED depuis une liste [R, G, B] (sans envoi SPI)."""
        self.set_ledpixel(index, color[0], color[1], color[2])

    def set_led_color(self, index, r, g, b):
        """Modifie la couleur d'une LED ET envoie immédiatement via SPI (show)."""
        self.set_ledpixel(index, r, g, b)
        self.show()

    def set_led_rgb(self, index, color):
        """Modifie la couleur d'une LED (liste [R,G,B]) ET envoie immédiatement."""
        self.set_led_rgb_data(index, color)
        self.show()

    def set_all_led_color_data(self, r, g, b):
        """Applique une couleur à toutes les LEDs (sans envoi SPI)."""
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)

    def set_all_led_rgb_data(self, color):
        """Applique une couleur [R,G,B] à toutes les LEDs (sans envoi SPI)."""
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)

    def set_all_led_color(self, r, g, b):
        """Applique une couleur à toutes les LEDs ET envoie via SPI."""
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)
        self.show()

    def set_all_led_rgb(self, color):
        """Applique une couleur [R,G,B] à toutes les LEDs ET envoie via SPI."""
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)
        self.show()

# ---Encodage et envoi SPI (protocole WS2812)---

    def write_ws2812_numpy8(self):
        """
        Encode les couleurs RGB en signal SPI compatible WS2812 (résolution 8 bits par couleur).
        
        Principe : chaque bit de couleur est converti en 1 octet SPI :
          - Bit '1' → 0b11111000 (0x78 | 0x80) : impulsion haute longue (T1H ≈ 0.625µs)
          - Bit '0' → 0b10000000 (0x80)        : impulsion haute courte (T0H ≈ 0.25µs)
        
        Fréquence SPI :
          - Bus 0 : 6.4 MHz (période = 1.25µs, conforme WS2812)
          - Autres bus : 8 MHz
        """
        d = numpy.array(self.led_color).ravel()             # Tableau 1D de toutes les valeurs RGB
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)     # 8 octets SPI par valeur RGB

        # Pour chaque bit (du MSB au LSB), calcul de l'octet SPI correspondant
        for ibit in range(8):
            tx[7 - ibit::8] = ((d >> ibit) & 1) * 0x78 + 0x80

        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))  # 6.4 MHz pour SPI0
            else:
                self.spi.xfer(tx.tolist(), int(8 / 1.0e-6))   # 8 MHz pour les autres bus

    def write_ws2812_numpy4(self):
        """
        Version alternative d'encodage SPI (résolution 4 bits par couleur, 2 bits encodés par octet).
        Moins précis mais plus rapide — chaque octet SPI encode 2 bits de couleur.
        """
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 4, dtype=numpy.uint8)
        for ibit in range(4):
            tx[3 - ibit::4] = ((d >> (2 * ibit + 1)) & 1) * 0x60 + ((d >> (2 * ibit + 0)) & 1) * 0x06 + 0x88
        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(4 / 1.25e-6))
            else:
                self.spi.xfer(tx.tolist(), int(4 / 1.0e-6))

    def show(self, mode=1):
        """
        Envoie les données de couleur aux LEDs via SPI.
        :param mode: 1 = encodage 8 bits (défaut, plus précis), autre = encodage 4 bits
        """
        if mode == 1:
            write_ws2812 = self.write_ws2812_numpy8
        else:
            write_ws2812 = self.write_ws2812_numpy4
        write_ws2812()

# ---Conversion couleur---


    def wheel(self, pos):
        """
        Calcule une couleur RGB sur une roue chromatique de 256 positions.
        Utilisé pour créer des effets arc-en-ciel (0–255 → rouge→vert→bleu→rouge).
        """
        if pos < 85:
            return [(255 - pos * 3), (pos * 3), 0]
        elif pos < 170:
            pos -= 85
            return [0, (255 - pos * 3), (pos * 3)]
        else:
            pos -= 170
            return [(pos * 3), 0, (255 - pos * 3)]

    def hsv2rgb(self, h, s, v):
        """
        Convertit une couleur HSV (Teinte, Saturation, Valeur) en RGB.
        :param h: Teinte (0–360 degrés)
        :param s: Saturation (0–100 %)
        :param v: Valeur/Luminosité (0–100 %)
        :return: Liste [R, G, B] (valeurs 0–255)
        """
        h = h % 360
        rgb_max = round(v * 2.55)                          # Conversion valeur → 0-255
        rgb_min = round(rgb_max * (100 - s) / 100)         # Composante minimale selon la saturation
        i = round(h / 60)                                  # Secteur de la roue chromatique (0–5)
        diff = round(h % 60)                               # Décalage dans le secteur
        rgb_adj = round((rgb_max - rgb_min) * diff / 60)   # Ajustement de transition entre secteurs

        # Calcul des composantes R, G, B selon le secteur
        if i == 0:   r, g, b = rgb_max, rgb_min + rgb_adj, rgb_min
        elif i == 1: r, g, b = rgb_max - rgb_adj, rgb_max, rgb_min
        elif i == 2: r, g, b = rgb_min, rgb_max, rgb_min + rgb_adj
        elif i == 3: r, g, b = rgb_min, rgb_max - rgb_adj, rgb_max
        elif i == 4: r, g, b = rgb_min + rgb_adj, rgb_min, rgb_max
        else:        r, g, b = rgb_max, rgb_min, rgb_max - rgb_adj
        return [r, g, b]

# ---Contrôle des animations (mode police, respiration)---

    def police(self):
        """Active l'effet 'police' (clignotement bleu/rouge alternés) et démarre le thread."""
        self.lightMode = 'police'
        self.resume()

    def breath(self, R_input, G_input, B_input):
        """
        Active l'effet de respiration (fondu progressif d'une couleur).
        :param R_input, G_input, B_input: Couleur cible de l'effet
        """
        self.lightMode = 'breath'
        self.colorBreathR = R_input
        self.colorBreathG = G_input
        self.colorBreathB = B_input
        self.resume()

    def resume(self):
        """Débloque le thread d'animation (set() déverrouille l'Event)."""
        self.__flag.set()

    def breathProcessing(self):
        """
        Boucle d'animation de l'effet 'breath' :
        - Phase montante : augmente progressivement l'intensité de la couleur cible
        - Phase descendante : réduit progressivement l'intensité
        Utilise breathSteps paliers avec 30ms de délai entre chaque.
        """
        while self.lightMode == 'breath':
            # Phase montante (intensité 0 → max)
            for i in range(0, self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(
                    self.colorBreathR * i / self.breathSteps,
                    self.colorBreathG * i / self.breathSteps,
                    self.colorBreathB * i / self.breathSteps
                )
                time.sleep(0.03)
            # Phase descendante (intensité max → 0)
            for i in range(0, self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(
                    self.colorBreathR - (self.colorBreathR * i / self.breathSteps),
                    self.colorBreathG - (self.colorBreathG * i / self.breathSteps),
                    self.colorBreathB - (self.colorBreathB * i / self.breathSteps)
                )
                time.sleep(0.03)

    def policeProcessing(self):
        """
        Boucle d'animation de l'effet 'police' :
        - 3 clignotements bleus rapides (50ms on / 50ms off)
        - Pause de 100ms
        - 3 clignotements rouges rapides
        - Pause de 100ms
        """
        while self.lightMode == 'police':
            for i in range(0, 3):
                self.set_all_led_color_data(0, 0, 255)  # Bleu
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0, 0, 0)    # Éteint
                self.show()
                time.sleep(0.05)
            if self.lightMode != 'police':
                break
            time.sleep(0.1)
            for i in range(0, 3):
                self.set_all_led_color_data(255, 0, 0)  # Rouge
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0, 0, 0)    # Éteint
                self.show()
                time.sleep(0.05)
            time.sleep(0.1)

    def lightChange(self):
        """
        Aiguillage vers la bonne animation selon lightMode.
        Si 'none', met le thread en pause (pause()).
        """
        if self.lightMode == 'none':
            self.pause()
        elif self.lightMode == 'police':
            self.policeProcessing()
        elif self.lightMode == 'breath':
            self.breathProcessing()

    def run(self):
        """
        Méthode principale du thread (appelée par thread.start()).
        Attend indéfiniment que le flag soit levé, puis exécute l'animation active.
        """
        while 1:
            self.__flag.wait()   # Bloque jusqu'à ce que resume() soit appelé
            self.lightChange()

# ---Interface utilisateur simplifiée---

    def setLED(self, numero_led, couleur, intensite=255):
        """
        Interface simplifiée pour allumer une LED par numéro et couleur.
        :param numero_led: Index de la LED (0 à 13)
        :param couleur: 'R' (rouge), 'G' (vert), 'B' (bleu), 'N' (éteindre)
        :param intensite: Luminosité de 0 à 255 (défaut : 255)
        """
        # Validation de l'index de la LED
        if numero_led < 0 or numero_led > 13:
            print("Numéro de LED invalide (0 à 13)")
            return

        # Clamp de l'intensité dans la plage valide [0, 255]
        intensite = max(0, min(255, intensite))

        # Correspondance couleur → valeurs RGB
        if couleur == 'R':
            r, g, b = intensite, 0, 0
        elif couleur == 'G':
            r, g, b = 0, intensite, 0
        elif couleur == 'B':
            r, g, b = 0, 0, intensite
        elif couleur == 'N':
            r, g, b = 0, 0, 0       # Éteindre la LED
        else:
            print("Couleur invalide. Utilisez R, G, B ou N.")
            return

        self.set_led_color(numero_led, r, g, b)
        self.show()
        print(f"LED {numero_led} → couleur {couleur}, intensité {intensite}")

# ===Point d'entrée principal (exécution directe du script)===

if __name__ == "__main__":
    import time
    import os

    # Vérification de la version de spidev et des devices SPI disponibles
    print("spidev version is ", spidev.__version__)
    print("spidev device as show:")
    os.system("ls /dev/spi*")  # Liste les interfaces SPI disponibles sur le système

    # Création du contrôleur avec 14 LEDs à luminosité maximale
    led = Adeept_SPI_LedPixel(14, 255)

    if led.check_spi_state() == 0:
        print("Erreur : SPI non disponible.")
    else:
        print("=== Contrôle manuel des LEDs WS2812 ===")
        print("Format : <numéro> <couleur> <intensité>")
        print("  numéro   : 0 à 13")
        print("  couleur  : R, G, B, N (éteindre)")
        print("  intensité: 0 à 255 (optionnel, 255 par défaut)")
        print("  Exemple  : NumeroLED Couleur Intensite ou NumLED Couleur")
        print("  Tapez 'q' pour quitter")
        print()

        # Boucle principale de saisie des commandes utilisateur
        while True:
            commande = input("Commande : ").strip()

            # Quitter proprement
            if commande.lower() == 'q':
                led.led_close()
                print("Au revoir !")
                break

            parts = commande.split()

            if len(parts) == 2:
                # Format : <numéro> <couleur>
                try:
                    numero  = int(parts[0])
                    couleur = parts[1].upper()
                    led.setLED(numero, couleur)
                except ValueError:
                    print("Format invalide. Exemple : NumLED Couleur")

            elif len(parts) == 3:
                # Format : <numéro> <couleur> <intensité>
                try:
                    numero    = int(parts[0])
                    couleur   = parts[1].upper()
                    intensite = int(parts[2])
                    led.setLED(numero, couleur, intensite)
                except ValueError:
                    print("Format invalide. Exemple : NumLED Couleur Intensite")

            else:
                print("Format invalide. Exemple : NumLED Couleur Intensite ou NumLED Couleur")
