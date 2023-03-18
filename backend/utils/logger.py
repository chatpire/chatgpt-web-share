# 创建一个用于输出信息的logger，同时输出到控制台和logs/时间.log文件
import logging
import logging.config
import os
from datetime import datetime

import yaml

from api.config import config


def get_log_config():
    with open('logging_config.yaml', 'r') as f:
        log_config = yaml.safe_load(f.read())

    log_dir = config.get("log_dir", "logs")
    os.makedirs(log_dir, exist_ok=True)
    filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d_%H-%M-%S')}.log")
    log_config['handlers']['file_handler']['filename'] = filename
    log_config['handlers']['console_handler']['level'] = config.get("console_log_level", "INFO")
    return log_config


def setup_logger():
    log_config = get_log_config()
    logging.config.dictConfig(log_config)


def get_logger(name):
    return logging.getLogger(f"cws.{name}")

