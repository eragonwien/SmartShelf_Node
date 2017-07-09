import random
import time
import sys


# set pin
def get_sonic_value(echo, trigger):
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        # if no device is found. a random number is generated for testing
        return round(random.uniform(echo, trigger), 0)
    try:
        timer_start = time.time()
        timeout = False
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(trigger, GPIO.OUT)
        GPIO.setup(echo, GPIO.IN)
        GPIO.output(trigger, 0)
        time.sleep(0.1)
        # print("Start sonic measure...")
        GPIO.output(trigger, 1)
        time.sleep(0.00001)
        GPIO.output(trigger, 0)

        while GPIO.input(echo) == 0:
            if time.time() - timer_start > 0.5:
                timeout = True
                break
            pass
        start = time.time()
        if not timeout:
            while GPIO.input(echo) == 1:
                pass
        stop = time.time()
        GPIO.cleanup()
        if timeout:
            return -2
        return (stop - start) * 17000
    except ValueError:
        print('Throws GPIO Error')
        GPIO.cleanup()
        return -1
