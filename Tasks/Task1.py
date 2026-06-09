import time
from gpiozero import LED
from gpiozero import PWMOutputDevice as PWM
Left_R  = 0
Left_G  = 19
Left_B  = 13
Right_R = 1
Right_G = 5
Right_B = 6
def switchSetup():
    global led1,led2,led3, L_R, L_G, L_B, R_R, R_G, R_B
    led1 = LED(9)
    led2 = LED(25)
    led3 = LED(11)
    L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
    L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
    L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)
    R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
    R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
    R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)

def switch(port, status):
    if port == 1:
        if status == 1:
            led1.on()
        elif status == 0:
            led1.off()
    elif port == 2:
        if status == 1:
            led2.on()
        elif status == 0:
            led2.off()
    elif port == 3:
        if status == 1:
            led3.on()
        elif status == 0:
            led3.off()
    elif port == 4:
        if status == 1:
            L_R.value = 0.0
        elif status == 0:
            L_R.value =1.0
    elif port == 5:
        if status == 1:
            L_G.value = 0.0
        elif status == 0:
            L_G.value =1.0
    elif port == 6:
        if status == 1 :
            L_B.value = 0.0
        elif status == 0 :
            L_B.value =1.0
    elif port == 7:
        if status == 1:
            R_R.value = 0.0
        elif status == 0:
            R_R.value =1.0
    elif port == 8:
        if status == 1 :
            R_G.value = 0.0
        elif status == 0:
            R_G.value =1.0
    elif port == 9:
        if status == 1 :
            R_B.value = 0.0
        elif status == 0:
            R_B.value =1.0
    else:
        print('Wrong Command: Example--switch(3, 1)->to switch on port3')
def set_all_switch_off():
    for port in range(1, 10):
        switch(port, 0)

if __name__ == "__main__":
    switchSetup()
    while True:
        try:
            code = int(input("Entrez un code de commande : "))
        except ValueError:
            print("Veuillez entrer un nombre entier.")
            continue
        time.sleep(1)
        if 11 <= code <= 19:
            port = code - 10  # 11→1, 12→2, ..., 19→9
            switch(port, 1)
            print(f"LED {port} allumée.")
        elif 21 <= code <= 29:
            port = code - 20  # 21→1, 22→2, ..., 29→9
            switch(port, 0)
            print(f"LED {port} éteinte.")
        else:
            print("Code inconnu. Utilisez un nombre entre 11 et 29")
