
import sys
import node_imp
import time
import multiprocessing
import os

while not node_imp.has_internet():
    time.sleep(1)
HOST = node_imp.get_host_ip()
PORT = 51212
A_PORT = 51213
BUFFERSIZE = 2048
MAX_CLIENT = 10
DATA_PATH = 'data.txt'
CONNECTION_PATH = 'connection.txt'
PIN_PATH = 'pin.txt'
SONIC_PATH = 'sonic.txt'
RECONNECTION_TIMES = 3
TIMEOUT = 3
ALIVE_INTERVAL = 10

if __name__ == '__main__':
    print('NODE Nr.', HOST)

    # CHECK CORE COMPONENTS
    # look for pin settings in directory
    if not node_imp.is_file_exist(PIN_PATH):
        print('No Data file found. System exits')
        sys.exit()

    # INITIALIZE COMPONENTS
    # look for database
    if not node_imp.is_file_exist(DATA_PATH):
        node_imp.create_data_from_pin_file(PIN_PATH, DATA_PATH)

    # create connection data
    node_imp.create_connection_data(
        CONNECTION_PATH, HOST, PORT, A_PORT, BUFFERSIZE, MAX_CLIENT, TIMEOUT, RECONNECTION_TIMES, ALIVE_INTERVAL)

    # look for info file
    node_imp.create_data_from_pin_file(PIN_PATH, DATA_PATH)

    # create value file
    node_imp.create_value_file_from_pin_file(PIN_PATH, SONIC_PATH)

    # BACKGROUND PROCESS
    working_queue = multiprocessing.SimpleQueue()
    background_process = node_imp.BackgroundProcess(
        CONNECTION_PATH, DATA_PATH, SONIC_PATH, working_queue, multiprocessing.Lock())
    background_process.start()

    # SONIC PROCESS
    sonic = node_imp.SonicThread(working_queue)
    sonic.start()

    # RECEIVES MESSAGE
    node_imp.udp_select_receive(CONNECTION_PATH, working_queue)
    # SYNC END
    sonic.kill_sonic()
    background_process.join()
    sonic.join()
    os.system('sudo reboot now')
