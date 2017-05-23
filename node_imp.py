import socket
import os.path
import json
import threading
import time
import random
import select
import sys
import os
import zipfile
# --------------------DATA----------------------------------------------------------------------------------------------
VERSION = '1.3.2'
UPDATES_PATH = ''
UPDATES_FILENAME = 'updates.zip'


def is_file_exist(file_path):
    return os.path.isfile(file_path)


def is_json(obj) -> bool:
    try:
        json.loads(obj)
        return True
    except ValueError:
        return False


# this function return an object from file
def get_obj_from_file(file_path: str):
    file = None
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            file = json.loads(file.read())
    return file


# this function overwrite a file with a new object
def set_obj_in_file(obj, file_path: str):
    with open(file_path, 'w') as file:
        file.write(json.dumps(obj, indent=1))


def create_new_pins(pin_file: str):
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
    set_obj_in_file(pin_list, pin_file)


def create_data_from_pin_file(pin_file: str, datafile: str):
    if not is_file_exist(datafile):
        pin_list = get_obj_from_file(pin_file)
        sensor_list = []
        for pin_dual in pin_list:
            sensor = {"in": pin_dual[0], "out": pin_dual[1], "item_width": 0, "shelf_width": 0}
            sensor_list.append(sensor)
        node = sensor_list
        set_obj_in_file(node, datafile)


def create_connection_data(connection_file, host, port, a_port, buffersize, max_client, timeout, reconnect,
                           alive_interval):
    connection_data = {'host': host, 'port': port, 'a_port': a_port, 'buffersize': buffersize, 'max_client': max_client,
                       'timeout': timeout, 'reconnect': reconnect, 'alive_interval': alive_interval}
    set_obj_in_file(connection_data, connection_file)


def extract_zip(file_path: str, zip_name: str):
    with zipfile.ZipFile(zip_name, 'r') as target_zip:
        target_zip.extractall(file_path)
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


# this func receives single files as tcp message
def tcp_file_receive(file_path: str, host: str, port, buffersize, timeout, max_client):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind((host, port))
    tcp.settimeout(timeout)
    tcp.listen(max_client)
    with open(file_path, 'wb') as received_file:
        try:
            while True:
                connection, address = tcp.accept()
                data = connection.recv(buffersize)
                while data:
                    received_file.write(data)
                    data = connection.recv(buffersize)
            tcp.close()
        except socket.timeout:
            tcp.close()
        except socket.error:
            tcp.close()


# this func receive multiple TCP message
def tcp_select_receive(host, port, buffersize, timeout, max_client):
    results = []
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setblocking(0)
    tcp.bind((host, port))
    tcp.listen(max_client)
    server_input = [tcp]
    running = 1
    while running:
        input_ready, output_ready, except_ready = select.select(server_input, [], [], timeout)
        if not (input_ready or output_ready or except_ready):
            tcp.close()
            break
        for s in input_ready:
            if s == tcp:
                # handle the server socket
                client, address = tcp.accept()
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
        result = calculate_stock_from_distance(sonic_value, int(self.sensor["item_width"]),
                                               int(self.sensor["shelf_width"]))
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


def replace_sensor(sensor_index: int, new_sensor: dict, data_file: str):
    sensor_list = get_obj_from_file(data_file)
    sensor = sensor_list[sensor_index]
    for key, item in sensor.items():
        if key in new_sensor:
            sensor[key] = new_sensor[key]
    set_obj_in_file(sensor_list, data_file)

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
            tcp_send(self.target, connection_data["a_port"], connection_data["host"],
                     connection_data["timeout"], connection_data["reconnect"])
        elif self.command == "STOCK?":
            sensor_list = get_obj_from_file(self.data_file)
            results = ["Timeout" for i in range(len(sensor_list))]
            for i in range(len(sensor_list)):
                SonicThread(i, results, self.data_file)
            start = time.time()
            wait_time = 2  # waits 2 seconds
            while time.time() < (start + wait_time):
                pass
            # sends results
            message = json.dumps([connection_data["host"], results])
            tcp_send(self.target, connection_data["port"], message, connection_data["timeout"],
                     connection_data["reconnect"])
        # get node info
        elif self.command == "DATA?":
            tcp_send(self.target, connection_data["port"], "DATAY" + connection_data["host"],
                     connection_data["timeout"], connection_data["reconnect"])
        # get sensor info
        elif self.command[:6] == "SENSOR" and self.command[6:] == connection_data["host"]:
            answer = []
            sensor_list = get_obj_from_file(self.data_file)
            for sensor in sensor_list:
                item = {"item_width": sensor["item_width"], "shelf_width": sensor["shelf_width"]}
                answer.append(item)
            tcp_send(self.target, connection_data["port"], json.dumps(answer), connection_data["timeout"],
                     connection_data["reconnect"])
        # shutdown
        elif self.command[:6] == "SHUTD?" and self.command[6:] == connection_data["host"]:
            tcp_send(self.target, connection_data["port"], "SHUTDY" + connection_data["host"],
                     connection_data["timeout"], connection_data["reconnect"])
            print("Shutting down...")
            os.system("sudo shutdown now")
        # update and reboot
        elif self.command == "UPDATE":
            print("Updates Notification received")
            tcp_send(self.target, connection_data["port"], connection_data["host"],
                     connection_data["timeout"], connection_data["reconnect"])
            print("Confirmation sent")
            time.sleep(5)
            tcp_file_receive(UPDATES_FILENAME, connection_data["host"], connection_data["port"],
                             connection_data["buffersize"], connection_data["timeout"], connection_data["max_client"])
            extract_zip(UPDATES_PATH, UPDATES_FILENAME)
            print("Updates received")
            print("Updating...")
            os.system('sudo cp updates/* .')
            print("Shutting down...")
            os.system("sudo shutdown -r now")
        # test
        elif self.command == "TEST":
            tcp_send(self.target, connection_data["port"], json.dumps([connection_data["host"], VERSION]),
                     connection_data["timeout"], connection_data["reconnect"])
        # handles JSON Message
        elif is_json(self.command):
            package = json.loads(self.command)
            if package[0] == "CHANGE":
                (node_id, sensor_index) = package[1]
                if node_id == connection_data["host"]:
                    replace_sensor(int(sensor_index), package[2], self.data_file)
                    tcp_send(self.target, connection_data["port"], "OK" + connection_data["host"],
                             connection_data["timeout"], connection_data["reconnect"])


# this func receives multiple UDP message then fowards it to processor
def udp_select_receive(connection_file, data_file):
    connection_data = get_obj_from_file(connection_file)
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setblocking(0)
    server2.setblocking(0)
    server.bind(('', connection_data["port"]))
    server2.bind(('', connection_data["a_port"]))
    server_input = [server, server2]
    while True:
        input_ready, output_ready, except_ready = select.select(server_input, [], [])
        if not (input_ready or output_ready or except_ready):
            server.close()
            break
        for s in input_ready:
            if s == server or s == server2:
                data, address = s.recvfrom(connection_data["buffersize"])
                print("Source :", address[0], " Message :", data.decode())
                NodeProcessor(data.decode(), address[0], connection_file, data_file)
