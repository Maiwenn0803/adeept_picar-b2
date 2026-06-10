import Task4
from Task5 import *
from Task6 import *

def auto_stop_distance():
    dist = checkdist()
    if dist < 300:
        print("stop")
        task4.drive_with_ramp(0, 1, 0.7)
