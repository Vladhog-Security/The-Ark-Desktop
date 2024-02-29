import datetime
import logging
import os
import subprocess
import traceback

from stem.control import Controller
import threading
import socket
from flask import Flask, request, jsonify
from security import DH_Endpoint, AESCipher
import secrets
import string

from storage import Storage
import utils

alphabet = string.ascii_letters + string.digits

app = Flask("The Ark")
app.secret_key = ''.join(secrets.choice(alphabet) for i in range(256))
clients = {}


@app.route("/handshake")
def index():
    stage = request.args.get('stage')
    data = request.json
    if stage == "1":
        p2_key = DH_Endpoint.generate_numbers()
        pk2_key = DH_Endpoint.generate_numbers()
        p1_key = data['key']
        a = DH_Endpoint(p1_key, p2_key, pk2_key)
        clients[data['id']] = a
        return jsonify({"key2": p2_key, "pk2": a.generate_partial_key()})
    elif stage == "2":
        dh = clients[data['id']]
        dh.generate_full_key(data['pk1'])
        return "", 200


@app.route("/get-message", methods=['POST'])
def get_message():
    try:
        data = request.json
        dh = clients[data['id']]
        service = data['service']
        message = data['message'].encode()
        # print(f"{data['id']}: {dh.decrypt_message(message)}")
        if server.ready:
            server.add_message(service, dh.decrypt_message(message))
            #print(server.on_message_listener)
            threading.Thread(target=server.on_message_listener, args=(None, True)).start()
            return "", 200
        else:
            return "", 400
    except Exception:
        logging.error(traceback.format_exc())


class Server:
    def __init__(self):
        # starting tor
        self.messages = None
        self.database = None
        self.key = None
        self.ready = False
        self.name = None
        self.on_message_listener = None
        self.logger = logging.getLogger("The_Ark.api.server")
        self.logger.setLevel(logging.INFO)
        self.logger.info("Starting tor...")
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen("./tor/tor/tor.exe -f ./tor/tor/torrc", shell=False, stdout=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        self.logger.info("Tor started")
        # print("yes")
        #threading.Thread(target=subprocess.Popen, args=("../tor/tor/tor.exe -f ../tor/tor/torrc",),
        #                kwargs={'shell': False, 'stdout': subprocess.DEVNULL, "creationflags": CREATE_NO_WINDOW}).start()
        self.logger.info("Tor started")

        # getting control over tor
        self.logger.info("Connecting to tor api...")
        self.controller = Controller.from_port(address="127.0.0.1", port=9051)
        self.controller.authenticate(password="12345")  # don't ask about the password.
        self.logger.info("Connected!")

    def start(self, name: str = None):
        self.database = Storage(utils.database_path, self.key)
        self.messages = Storage(utils.messages_path, self.key)

        # getting random open port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        self.port = s.getsockname()[1]
        s.close()
        # print(self.port)

        if not os.path.exists(utils.database_path):
            self.logger.info("First start processing... generating address...")
            a = self.controller.create_ephemeral_hidden_service(ports={80: f"127.0.0.1:{self.port}"},
                                                                await_publication=True)
            data = {
                "service": f"{a.private_key_type}:{a.private_key}",
                "name": name,
                "address": a.service_id,
                "contacts": {}
            }
            messages = {}
            self.name = name
            self.database.write(str(data))
            self.messages.write(str(messages))
            self.logger.info("Server ready and connected to network!")
        else:
            self.logger.info("Reading data...")
            data = self.database.read()
            self.name = data['name']
            #print(data)
            key_type, key_content = data['service'].split(":", 1)

            a = self.controller.create_ephemeral_hidden_service(ports={80: f"127.0.0.1:{self.port}"},
                                                                await_publication=True, key_type=key_type,
                                                                key_content=key_content)
            self.logger.info("Server ready and connected to network!")

        self.service_host = a.service_id
        #print(self.service_host)
        threading.Thread(target=app.run, kwargs={'port': self.port}).start()
        self.ready = True

    def get_contacts(self):
        #print(self.database.read())
        data = self.database.read()['contacts']
        #print(data)
        return data

    def add_contact(self, name: str, address: str):
        data = self.database.read()
        data['contacts'][name] = address
        self.database.write(data)

    def remove_contact(self, name: str):
        data = self.database.read()
        del data['contacts'][name]
        self.database.write(data)

    def get_messages(self, name: str):
        #print(name)
        address = self.database.read()['contacts'][name]
        try:
            data = self.messages.read()[address]
            #print(data)
            return data
        except KeyError:
            return []
        except FileNotFoundError:
            self.messages.write({})
            return []

    def add_message(self, address: str, text: str, selfsent: bool = False):
        if not selfsent:
            # converting address to name
            name = list(self.database.read()['contacts'].keys())[
                list(self.database.read()['contacts'].values()).index(address)]
            data = self.messages.read()
            try:
                data[address].append({"timestamp": str(datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")), "text": text, "author": name})
            except KeyError:
                data[address] = [{"timestamp": str(datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")), "text": text, "author": name}]
            self.messages.write(data)
        else:
            data = self.messages.read()
            try:
                data[address].append({"timestamp": str(datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")), "text": text, "author": ""})
            except KeyError:
                data[address] = [{"timestamp": str(datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")), "text": text, "author": ""}]
            self.messages.write(data)


server = Server()
