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
VERSION = '1.2.3b'


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
            sensor = {"in": pin_dual[0], "out": pin_dual[1], "item_width":0, "shelf_width": 0}
            sensor_list.append(sensor)
        node = sensor_list
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
    port = 80
    host = "www.google.com"
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


def calculate_stock_from_distance(distance: int, item_width: int, shelf_width: int):
    try:
        if item_width <= 0:
            return 0
        return round((shelf_width - distance) / item_width)
    except ArithmeticError:
        return None


# this thread calculates sonic value from sensor
class SonicThread(threading.Thread):
    def __init__(self, sensor_index: int, results: list, data_file: str):
        threading.Thread.__init__(self)
        self.sensor_index = int(sensor_index)
        self.results = results
        self.data_file = data_file
        sensor_list = get_obj_from_file(data_file)
        self.sensor = sensor_list[sensor_index]
        self.sensor_in = self.sensor["in"]
        self.sensor_out = self.sensor["out"]
        self.daemon = 1
        self.terminated = 0
        self.start()

    def run(self):
        sonic_value = get_sonic_value(int(self.sensor_in), int(self.sensor_out))
        result = calculate_stock_from_distance(sonic_value, int(self.sensor["item_width"]), int(self.sensor["shelf_width"]))
        if result:
            self.results[self.sensor_index] = result
        else:
            self.results[self.sensor_index] = "Arithmetic Error"


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
        sensor = {"in": pin_dual[0], "out": pin_dual[1], "item_width": 0, "shelf_width": 0}
        sensor_list.append(sensor)
    node = sensor_list
    return node

def replace_sensor(sensor_index:int, new_sensor:dict, data_file:str):
    sensor_list = get_obj_from_file(data_file)
    sensor = sensor_list[sensor_index]
    for key, item in sensor.items():
        if key in new_sensor:
            sensor[key] = new_sensor[key]
    set_obj_in_file(sensor_list,data_file)

# --------------------------THREAD---------------------------------------------------------------------------------------


class NodeProcessor(threading.Thread):
    def __init__(self, command, target, connection_file, data_file):
        threading.Thread.__init__(self)
        self.command = command
        self.target = target
        self.connection_file = connection_file
        self.data_file = data_file
        self.daemon = 1
        self.start()

    def run(self):
        connection_data = get_obj_from_file(self.connection_file)
        if self.command == "ALIVE?":
            tcp_send(self.target, connection_data["port"], "ALIVEY" + connection_data["host"],
                     connection_data["timeout"], connection_data["reconnect"])
        elif self.command == "STOCK?":
            sensor_list = get_obj_from_file(self.data_file)
            results = [0 for i in range(len(sensor_list))]
            sensor_pool = [ "timeout" for i in range(len(sensor_list))]
            for i in range(len(sensor_list)):
                sensor_pool.append(SonicThread(i, results, self.data_file))
            start = time.time()
            wait_time = 2 # waits 2 seconds
            while time.time() < (start + wait_time): pass
            # sends results
            message = json.dumps([connection_data["host"], results])
            tcp_send(self.target, connection_data["port"], message, connection_data["timeout"], connection_data["reconnect"])

        elif self.command == "DATA?":
            tcp_send(self.target, connection_data["port"], "DATAY" + connection_data["host"],
                     connection_data["timeout"], connection_data["reconnect"])
        elif self.command[:6] == "SENSOR":
            if self.command[6:] == connection_data["host"]:
                answer = []
                sensor_list = get_obj_from_file(self.data_file)
                for sensor in sensor_list:
                    item = {"item_width":sensor["item_width"] , "shelf_width":sensor["shelf_width"]}
                    answer.append(item)
                tcp_send(self.target, connection_data["port"], json.dumps(answer), connection_data["timeout"], connection_data["reconnect"])
        # handles JSON Message
        elif is_json(self.command):
            package = json.loads(self.command)
            if package[0] == "CHANGE":
                (node_id, sensor_index) = package[1]
                if node_id == connection_data["host"]:
                    replace_sensor(int(sensor_index),package[2],self.data_file)
                    tcp_send(self.target, connection_data["port"],"OK"+connection_data["host"],connection_data["timeout"], connection_data["reconnect"])


# this func receives multiple UDP message then fowards it to processor
def udp_select_receive(connection_file, data_file):
    connection_data = get_obj_from_file(connection_file)
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('', connection_data["port"]))
    server_input = [server]
    while True:
        inputready, outputready, exceptready = select.select(server_input, [], [])
        if not (inputready or outputready or exceptready):
            server.close()
            break
        for s in inputready:
            if s == server:
                data, addr = s.recvfrom(connection_data["buffersize"])
                print("Source :", addr[0], " Messsage :", data.decode())
                NodeProcessor(data.decode(), addr[0], connection_file, data_file)
