
import sys
import node_imp
import time

while not node_imp.has_internet() : time.sleep(1)
HOST = node_imp.get_host_ip()
REGISTER_PORT = 51212
ALIVE_PORT = 51213
STOCK_PORT = 51214
CONFIG_PORT = 51215
BUFFERSIZE = 2048
MAX_CLIENT = 10
DATA_PATH = "data.txt"
CONNECTION_PATH = "connection.txt"
PIN_PATH = "pin.txt"
SONIC_PATH = "sonic.txt"
RECONNECTION_TIMES = 3
TIMEOUT = 3
ALIVE_INTERVALL = 10
print("NODE Nr.",HOST)
threads_list = []

node_imp.create_connection_data(CONNECTION_PATH, HOST, REGISTER_PORT, BUFFERSIZE, MAX_CLIENT, TIMEOUT, RECONNECTION_TIMES, ALIVE_INTERVALL)
if not node_imp.is_file_exist(PIN_PATH):
    print("No Data file found. Create new one with pin maker")
    node_imp.create_new_pins(PIN_PATH)
node_imp.get_data_from_center(CONNECTION_PATH,DATA_PATH, PIN_PATH)
node_imp.create_default_sonic_file(SONIC_PATH, PIN_PATH)
# run Sonic at start
pin_list = node_imp.get_obj_from_file(PIN_PATH)
#udp receiver
alice_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, ALIVE_PORT)
threads_list.append(alice_receiver)
stock_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, STOCK_PORT)
threads_list.append(stock_receiver)
update_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, CONFIG_PORT)
threads_list.append(update_receiver)

while True:
    try: time.sleep(10)
    except :
        for thread in threads_list:
            thread.set_terminate()
        print("Closing App...")
        time.sleep(5)
        break
