import logging
import os

datafolder = os.getenv("appdata") + "/the_ark/"
database_path = datafolder + "data"
messages_path = datafolder + "messages"

try:
    os.mkdir(datafolder)
except FileExistsError:
    pass

logging.basicConfig(filename=datafolder + "log.log", filemode='a',
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)