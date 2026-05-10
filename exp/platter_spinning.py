from gpiozero import DigitalInputDevice
from signal import pause
import time

sensor = DigitalInputDevice(17, pull_up=True)

count = 0
start_time = time.time()

def pulse():
    global count
    count += 1

sensor.when_activated = pulse

while True:
    time.sleep(5)
    elapsed = time.time() - start_time
    rpm = (count / elapsed) * 60
    print(f"Estimated RPM: {rpm}")
    count = 0
    start_time = time.time()