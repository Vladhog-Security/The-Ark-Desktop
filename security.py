import base64
import binascii
import hashlib
import random
from Cryptodome import Random
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
import numpy as np

class WrongPassword(Exception):
    pass

# should not be used, experimental only for key exchange
class DH_Endpoint(object):
    """DH encryption"""

    def __init__(self, public_key1=None, public_key2=None, private_key=None):
        self.public_key1 = public_key1
        self.public_key2 = public_key2
        self.private_key = private_key
        self.full_key = None
        self.aes = None

    def generate_partial_key(self):
        partial_key = pow(self.public_key1, self.private_key, self.public_key2)
        return partial_key

    def generate_full_key(self, partial_key_r):
        full_key = pow(partial_key_r, self.private_key, self.public_key2)
        self.full_key = full_key
        self.aes = AESCipher(str(self.full_key))
        #print(self.aes.key)
        return full_key

    def encrypt_message(self, message: bytes):
        return self.aes.encrypt(message)

    def decrypt_message(self, encrypted_message: bytes):
        return self.aes.decrypt(encrypted_message)

    def add_full_key(self, full_key):
        self.full_key = full_key

    @staticmethod
    def generate_numbers():
        num = ""
        a = random.randint(2, 9)
        num = str(num) + str(a)
        for i in range(2048):
            a = random.randint(1, 9)
            num = str(num) + str(a)
        return int(num)

class AESCipher(object):
    def __init__(self, key: str):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw: bytes) -> bytes:
        raw = pad(raw, self.bs)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc: bytes) -> bytes:
        try:
            enc = base64.b64decode(enc)
            iv = enc[:AES.block_size]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(enc[AES.block_size:]), self.bs)
        except Exception:
            raise WrongPassword(f"wrong key: {self.key}")