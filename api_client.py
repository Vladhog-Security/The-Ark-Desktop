import logging
import traceback

from requests_tor import RequestsTor
from stem import Signal
from stem.control import Controller

from security import DH_Endpoint
import secrets
import string
from storage import Storage
import utils
alphabet = string.ascii_letters + string.digits

class Client:
    def __init__(self, address, key):
        self.service = Storage(utils.database_path, key).read()['address']
        self.address = address
        self.connect_url = "http://" + address + ".onion"
        self.dh = DH_Endpoint()
        self.session = RequestsTor(tor_ports=(9050,), tor_cport=9051)
        self.client_id = ''.join(secrets.choice(alphabet) for i in range(16))
        self.logger = logging.getLogger("The_Ark.api.client")
        self.logger.info("Client created")

    def connect(self):
        try:
            self.logger.info(f"Starting connection proccess for {self.address}")
            p1_key = self.dh.generate_numbers()
            pk1_key = self.dh.generate_numbers()
            data = self.session.get(self.connect_url + "/handshake", json={"key": p1_key, "id": self.client_id}, params={'stage': "1"}).json()
            #print(data)
            p2_key = int(data['key2'])
            self.dh = DH_Endpoint(p1_key, p2_key, pk1_key)
            key = self.dh.generate_full_key(data['pk2'])
            #print(key)
            self.session.get(self.connect_url + "/handshake", json={'pk1': self.dh.generate_partial_key(), "id": self.client_id}, params={'stage': "2"})
            self.logger.info("Connected!")
        except Exception:
            self.logger.error(traceback.format_exc())

    def send_message(self, text):
        try:
            self.logger.info("Sending message...")
            message = self.dh.encrypt_message(text.encode()).decode()
            self.session.post(self.connect_url + "/get-message", json={'message': message, "id": self.client_id, "service": self.service})
            self.logger.info("Message sent!")
        except Exception:
            self.logger.error(traceback.format_exc())

