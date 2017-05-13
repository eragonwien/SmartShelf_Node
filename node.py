
import sys
import node_imp
import time

while not node_imp.has_internet() : time.sleep(1)
HOST = node_imp.get_host_ip()
REGISTER_PORT = 51212
ALIVE_PORT = 51213
STOCK_PORT = 51214
CONFIG_PORT = 51215
UPDATE_PORT = 51216
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

# create connection data
node_imp.create_connection_data(CONNECTION_PATH, HOST, REGISTER_PORT, BUFFERSIZE, MAX_CLIENT, TIMEOUT, RECONNECTION_TIMES, ALIVE_INTERVALL)
'''
# turn on updater
#update_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, UPDATE_PORT)
#threads_list.append(update_receiver)
# look for pin settings in directory
if not node_imp.is_file_exist(PIN_PATH):
    print("No Data file found. System exits")
    sys.exit()
    #node_imp.create_new_pins(PIN_PATH)

# look for database
node_imp.create_data_from_pinfile(PIN_PATH, DATA_PATH, node_id=HOST)

# register itself to the network
#node_imp.register_self_to_network(CONNECTION_PATH,DATA_PATH)
# create default file containing stock value
#node_imp.create_default_sonic_file(SONIC_PATH, PIN_PATH)
# run Sonic at start
#pin_list = node_imp.get_obj_from_file(PIN_PATH)
#udp receiver
alice_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, ALIVE_PORT)
threads_list.append(alice_receiver)
stock_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, STOCK_PORT)
#threads_list.append(stock_receiver)
#config_receiver = node_imp.UDPReceiver(CONNECTION_PATH, DATA_PATH, PIN_PATH, SONIC_PATH, CONFIG_PORT)
#threads_list.append(config_receiver)
'''
# look for database
node_imp.create_data_from_pinfile(PIN_PATH, DATA_PATH, node_id=HOST)

node_imp.udp_select_receive(CONNECTION_PATH, DATA_PATH)
while True:
    try: time.sleep(10)
    except :
        for thread in threads_list:
            thread.set_terminate()
        print("Closing App...")
        time.sleep(5)
        break

