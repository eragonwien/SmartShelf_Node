import socket
import os.path
import json
import threading
import time
import random
import math
import select
import sys
import os

# --------------------DATA----------------------------------------------------------------------------------------------
VERSION = '1.2.3a'


def is_file_exist(filepath):
    return os.path.isfile(filepath)


def is_json(obj) -> bool:
    try:
        json.loads(obj)
        return True
    except ValueError:
        return False


# this function return an object from file
def get_obj_from_file(filepath: str):
    file = None
    if os.path.isfile(filepath):
        with open(filepath, 'r') as file:
            file = json.loads(file.read())
    return file


# this function overwrite a file with a new object
def set_obj_in_file(obj, filepath: str):
    with open(filepath, 'w') as file:
        file.write(json.dumps(obj, indent=1))


def create_new_pins(pinfile: str):
    print("PIN MAKER")
    pin_list = []
    while True:
        print("Type close to cancel creating pin")
        command = input("New Pin ? yes / no ")
        if command == "no":
            break
        elif command == "close":
            sys.exit()
        elif command == "yes":
            pin_in = input("PIN IN ? ")
            pin_out = input("PIN OUT ? ")
            pin_set = [pin_in, pin_out]
            pin_list.append(pin_set)
        else:
            print("Input has to be either yes or no ")
    set_obj_in_file(pin_list, pinfile)


def create_data_from_pinfile(pinfile: str, datafile: str, node_id: str):
    if not is_file_exist(datafile):
        pin_list = get_obj_from_file(pinfile)
        sensor_list = []
        for pin_dual in pin_list:
            sensor = {"in": pin_dual[0], "out": pin_dual[1], "status": "offline", "item_width": 0, "shelf_width": 0}
            sensor_list.append(sensor)
        node = {"id": node_id, "sensors": sensor_list, "status": "online"}
    else:
        node = get_obj_from_file(datafile)
        node["id"] = node_id
    set_obj_in_file(node, datafile)


def create_connection_data(connection_file, host, port, buffersize, max_client, timeout, reconnect,
                           alive_intervall):
    connection_data = {'host': host, 'port': port, 'buffersize': buffersize, 'max_client': max_client,
                       'timeout': timeout, 'reconnect': reconnect, 'alive_intervall': alive_intervall}
    set_obj_in_file(connection_data, connection_file)


def create_default_sonic_file(stockfile: str, pinfile: str):
    pin_list = get_obj_from_file(pinfile)
    stock_list = []
    for i in range(len(pin_list)):
        stock_list.append(0)
    set_obj_in_file(stock_list, stockfile)


# --------------------TCP-----------------------------------------------------------------------------------------------


# this func send a message over TCP
def tcp_send(host, port, message: str, timeout, reconnect) -> bool:
    for i in range(reconnect):
        sock = socket.socket()
        try:

            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.send(message.encode())
            sock.close()
            return True
        except socket.timeout:
            sock.close()
            return False


# this func receive multiple TCP message
def tcp_select_receive(host, port, buffersize, timeout, max_client):
    results = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(max_client)
    server_input = [server]
    running = 1
    while running:
        inputready, outputready, exceptready = select.select(server_input, [], [], timeout)
        if not (inputready or outputready or exceptready):
            server.close()
            break
        for s in inputready:
            if s == server:
                # handle the server socket
                client, address = server.accept()
                server_input.append(client)
            else:
                # handle all other sockets
                data = s.recv(buffersize)
                if data:
                    message = data.decode()
                    results.append(message)
                else:
                    s.close()
                    server_input.remove(s)
    return results


# check internet connection
def has_internet() -> bool:
    port = 53
    host = '8.8.8.8'
    timeout = 3
    try:
        sock = socket.socket()
        sock.settimeout(timeout)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return True
    except socket.timeout:
        return False


# --------------------UDP-----------------------------------------------------------------------------------------------
def broadcast_message(port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(message.encode(), ("<broadcast>", port))
    sock.close()
    return True


# --------------------SONIC---------------------------------------------------------------------------------------------
def get_sonic_value(trigger: int, echo: int) -> int:
    return round(random.uniform(echo, trigger), 0)


# this thread calculates sonic value from sensor
class SonicThread(threading.Thread):
    def __init__(self, sensor_index: int, results: list, pin_file: str):
        threading.Thread.__init__(self)
        self.sensor_index = int(sensor_index)
        self.results = results
        self.pin_file = pin_file
        pin_data = get_obj_from_file(pin_file)
        [self.sensor_in, self.sensor_out] = pin_data[self.sensor_index]
        self.daemon = 1
        self.terminated = 0
        self.start()

    def run(self):
        sonic_value = get_sonic_value(int(self.sensor_in), int(self.sensor_out))
        self.results[self.sensor_index] = sonic_value


def save_sonic_data(pin_file: str, sonic_file: str):
    pin_list = get_obj_from_file(pin_file)
    results = [0 for i in range(len(pin_list))]
    for i in range(len(pin_list)):
        SonicThread(i, results, pin_file)
    while len(results) < len(pin_list): pass
    set_obj_in_file(results, sonic_file)


def get_list_of_stocks(data_file: str) -> list:
    results = []
    node = get_obj_from_file(data_file)
    sensor_list = node["sensors"]
    for i in range(len(sensor_list)):
        sensor = sensor_list[i]
        sonic_value = get_sonic_value(int(sensor["in"]), int(sensor["out"]))
        amount = 0
        if int(sensor["item_width"]) > 0:
            amount = math.floor((int(sensor["shelf_width"]) - sonic_value) / int(sensor["item_width"]))
        results.append(amount)
    return results


# --------------------ETC-----------------------------------------------------------------------------------------------
def get_host_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    host = s.getsockname()[0]
    s.close()
    return host


# --------------------NODE SPECIFIC-------------------------------------------------------------------------------------

# this func create new node with default infomation
def create_new_default_node(id: str, pin_list: list, datapath: str) -> dict:
    sensor_list = []
    for pin_dual in pin_list:
        sensor = {"in": pin_dual[0], "out": pin_dual[1], "status": "offline", "item_width": 0, "shelf_width": 0}
        sensor_list.append(sensor)
    node = {"id": id, "sensors": sensor_list, "status": "online"}
    return node


def get_data_from_center(connect_file, data_file, pin_file):
    # broad cast ip over network
    connect_data = get_obj_from_file(connect_file)
    my_host = connect_data["host"]
    port = connect_data["port"]
    buffersize = connect_data["buffersize"]
    timeout = connect_data["timeout"]
    max_client = connect_data["max_client"]
    message = [my_host, get_obj_from_file(pin_file)]
    # broadcast and receive until there is a respond
    answer_list = []
    while not answer_list:
        broadcast_message(port, json.dumps(message, indent=1))
        # wait for confirmation per tcp
        # add the first valid one in data
        answer_list = tcp_select_receive(my_host, port, buffersize, timeout, max_client)
    # filter the answer,
    valid_registry = filter_registry(my_host, answer_list)
    # save the first valid one
    package = json.loads(valid_registry)
    for i in range(len(package)):
        if i == 0:
            set_obj_in_file(package[0], data_file)
            # if i == 1 : set_obj_in_file(package[1],connect_file)

    data = get_obj_from_file(data_file)
    print(data)
    return True


def register_self_to_network(connect_file, data_file):
    # broad cast ip over network
    connect_data = get_obj_from_file(connect_file)
    my_host = connect_data["host"]
    port = connect_data["port"]
    message = [my_host, get_obj_from_file(data_file)]
    broadcast_message(port, json.dumps(message, indent=1))
    return True


def filter_registry(node_id: str, registry_list: list) -> list:
    # get the least ok one
    valid_registry = []
    priority_registry = []
    for registry in registry_list:
        if is_json(registry):
            package = json.loads(registry)
            if isinstance(package, list) and isinstance(package[0], dict):
                if not valid_registry:
                    valid_registry = registry
                node = package[0]
                if node["id"] == node_id and node["sensors"]:
                    valid_registry = registry
                    # registry with priority
                    if "priority" in node:
                        priority_registry = registry
    if priority_registry:
        return priority_registry
    return valid_registry


# --------------------------THREAD---------------------------------------------------------------------------------------
class NodeUpdater(threading.Thread):
    def __init__(self, connect_file, data_file):
        threading.Thread.__init__(self)
        self.connect_file = connect_file
        self.data_file = data_file
        self.terminated = False
        self.daemon = True
        self.start()

    def run(self):
        while not self.terminated:
            get_data_from_center(self.connect_file, self.data_file)
            connection_data = get_obj_from_file(self.connect_file)
            intervall = connection_data["alive_intervall"]
            time.sleep(intervall)

    def set_terminated(self):
        self.terminated = True


class UDPProzessor(threading.Thread):
    def __init__(self, message, connect_file, data_file, pin_file, sonic_file, port):
        threading.Thread.__init__(self)
        self.connect_file = connect_file
        self.data_file = data_file
        self.pin_file = pin_file
        self.sonic_file = sonic_file
        self.message = message
        connection_data = get_obj_from_file(connect_file)
        self.host = connection_data["host"]
        self.port = port
        self.buffersize = connection_data["buffersize"]
        self.timeout = connection_data["timeout"]
        self.reconnect = connection_data["reconnect"]
        self.terminated = False
        self.daemon = True
        self.start()

    def run(self):
        print("Receive :", str(self.port), " : ", self.message)
        if self.message[:5] == "ALIVE":
            target_host = self.message[5:]
            tcp_send(target_host, self.port, self.host, self.timeout, self.reconnect)
        elif self.message[:5] == "DATAS":
            target_host = self.message[5:]
            package = [self.host, get_obj_from_file(self.data_file)]
            tcp_send(target_host, self.port, json.dumps(package), self.timeout, self.reconnect)
        elif self.message[:5] == "STOCK":
            target_host = self.message[5:]
            # get a list of measured value
            sonic_list = [self.host]
            save_sonic_data(self.pin_file, self.sonic_file)
            sonic_list += get_list_of_stocks(self.data_file)
            package = json.dumps(sonic_list, indent=1)
            tcp_send(target_host, self.port, package, self.timeout, self.reconnect)
            print("STOCK SENT")
        elif self.message[:5] == "RBOOT":
            target_host = self.message[5:]
            results = [self.host]
            package = json.dumps(results)
            tcp_send(target_host, self.port, package, self.timeout, self.reconnect)
            time.sleep(3)
            os.system("sudo chmod +x script.sh")
            os.system("sh script.sh")
        elif self.message[:5] == "SHUTD":
            os.system('sudo shutdown -h now')
        elif self.message[:5] == "TESTS":
            target_host = self.message[5:]
            # set test result here
            results = [self.host, VERSION]
            package = json.dumps(results)
            tcp_send(target_host, self.port, package, self.timeout, self.reconnect)
            print("STOCK SENT")
        else:
            if is_json(self.message):
                package = json.loads(self.message)
                if package[0] == self.host and package[1]:
                    node = get_obj_from_file(self.data_file)
                    node["sensors"] = package[1]
                    set_obj_in_file(node, self.data_file)


# this thread receives all incoming udp messages from a given port
# it checks the incoming message and init a respond
class UDPReceiver(threading.Thread):
    def __init__(self, connect_file, data_file, pin_file, sonic_file, port):
        threading.Thread.__init__(self)
        self.connect_file = connect_file
        self.data_file = data_file
        self.pin_file = pin_file
        self.sonic_file = sonic_file
        connection_data = get_obj_from_file(connect_file)
        self.host = connection_data["host"]
        self.port = port
        self.buffersize = connection_data["buffersize"]
        self.terminated = False
        self.daemon = True
        self.start()

    def run(self):
        while not self.terminated:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            s.bind(('', self.port))
            try:
                message = s.recvfrom(self.buffersize)
                UDPProzessor(message[0].decode(), self.connect_file, self.data_file, self.pin_file, self.sonic_file,
                             self.port)
            except socket.error:
                s.close()

    def set_terminate(self):
        self.terminated = True
