import logging
import logging.config
import os
from datetime import datetime
import traceback
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


def with_traceback(e: Exception):
    if Config().common.print_traceback:
        tb = traceback.extract_tb(e.__traceback__)
        last_frames = tb[-10:]
        formatted_traceback = ["traceback:"]
        for frame in last_frames:
            frame_info = f"{frame.filename}:{frame.lineno} in {frame.name}"
            formatted_traceback.append(frame_info)
        formatted_traceback = "\n".join(formatted_traceback)
        return f"<{e.__class__.__name__}> {str(e)}\n{formatted_traceback}"
    else:
        return str(e)
