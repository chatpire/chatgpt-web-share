from .config import Config
from .credentials import Credentials

config = Config()
credentials = Credentials()

config.load()
credentials.load()
