import logging
import logging.config
import os
from datetime import datetime

import yaml

from api.conf import Config
import api.globals as g


def get_log_config():
    with open('logging_config.yaml', 'r') as f:
        log_config = yaml.safe_load(f.read())
    log_config['handlers']['file_handler']['filename'] = g.server_log_filename
    log_config['handlers']['console_handler']['level'] = Config().log.console_log_level
    return log_config


def setup_logger():
    log_dir = os.path.join(Config().data.data_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    g.server_log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d_%H-%M-%S')}.log")
    log_config = get_log_config()
    logging.config.dictConfig(log_config)


def get_logger(name):
    return logging.getLogger(f"cws.{name}")
