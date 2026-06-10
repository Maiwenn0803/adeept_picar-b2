import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
# Créer une instance simple de la classe PCA9685.
pca = PCA9685(i2c, address=0x5f) #L'adresse par défaut est 0x40

pca.frequency = 50

# La plage d'impulsions est de 750 à 2250 par défaut. Cette plage donne typiquement 135 degrés de
# rotation, mais la valeur par défaut est d'utiliser 180 degrés. On peut spécifier la plage attendue si besoin :
# servo7 = servo.Servo(pca.channels[7], actuation_range=135)
def set_angle(ID, angle):
    servo_angle = servo.Servo(pca.channels[ID], min_pulse=500, max_pulse=2400, actuation_range=180)
    servo_angle.angle = angle


def test(channel):
    for i in range(180): # Le servo tourne de 0 à 180 degrés.
        set_angle(channel, i)
        time.sleep(0.01)
    time.sleep(0.5)
    for i in range(180): # Le servo tourne de 180 à 0 degrés.
        set_angle(channel, 180-i)
        time.sleep(0.01)
    time.sleep(0.5)

if __name__ == "__main__":
    channel = 0 # Le servo est connecté au canal 0.
    while True:
        test(channel)