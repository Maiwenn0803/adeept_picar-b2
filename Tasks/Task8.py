import time
import smbus

class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus=smbus.SMBus(1)
        self.address = 0x48 # 0x48 is the default i2c address for ADS7830 Module.   
        
    def analogRead(self, chn): # ADS7830 has 8 ADC input pins, chn:0,1,2,3,4,5,6,7
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value

if __name__ == "__main__":
    adc = ADS7830()
    while True:
        adc_value = adc.analogRead(1)
        print(f"Light Tracking Value: {adc_value}")
        time.sleep(0.5)
# Le programme affiche la valeur de luminosite captee par les deux capteurs place a l'avant du robot
# La valeur est commune au deux capteurs qui augmente quand la lumiere viend de gauche et diminue quand elle vient de droite
# Il peut etre utilise afin de diriger le robot vers la plus grande source de lumiere
