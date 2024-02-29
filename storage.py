import ast
import base64

from security import AESCipher

class Storage:
    def __init__(self, path, key):
        self.path = path
        self.aes = AESCipher(key)

    def read(self):
        with open(self.path, "rb") as file:
            data = base64.b64decode(self.aes.decrypt(file.read())).decode()
            data = ast.literal_eval(data)
            return data

    def write(self, data: str):
        with open(self.path, "wb") as file:
            data = self.aes.encrypt(base64.b64encode(str(data).encode()))
            file.write(data)