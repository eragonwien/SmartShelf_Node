import random
import time
import sys


# set pin
def get_sonic_value(echo, trigger):
    return round(random.uniform(echo, trigger), 0)
    '''
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        # if no device is found. a random number is generated for testing
        return round(random.uniform(echo, trigger), 0)
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(trigger, GPIO.OUT)
        GPIO.output(trigger, 0)
        GPIO.setup(echo, GPIO.IN)
        time.sleep(0.1)
        # print("Start sonic measure...")
        GPIO.output(trigger, 1)
        time.sleep(0.00001)
        GPIO.output(trigger, 0)
        timer_start = time.time()
        while GPIO.input(echo) == 0 and (time.time() - timer_start) < 1:
            pass
        start = time.time()
        while GPIO.input(echo) == 1 and (time.time() - timer_start) < 1:
            pass
        stop = time.time()
        return (stop - start) * 17000
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        GPIO.cleanup()

    '''
