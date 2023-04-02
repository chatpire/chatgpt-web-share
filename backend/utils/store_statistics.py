from collections import OrderedDict, deque

import api.globals as g
import json
import os

from utils.logger import get_logger

logger = get_logger(__name__)


def dump():
    path = g.config.get("statistics_store_path", ".")
    path = os.path.join(path, "statistics.json")
    data = {
        "request_log_counter_interval": g.request_log_counter_interval,
        "request_log_counter": g.request_log_counter.counter,
        "ask_log_queue": g.ask_log_queue.queue
    }
    with open(path, "w") as f:
        json.dump(data, f)
    logger.info(f"Requests statistics dumped to {path}.")


def load():
    path = g.config.get("statistics_store_path", ".")
    path = os.path.join(path, "statistics.json")
    try:
        with open(path, "r") as f:
            data = json.load(f)

            if g.config.get("request_log_counter_interval") != data["request_log_counter_interval"]:
                logger.warning("request_log_counter_interval is different from the saved one, counter cleared.")
                return
            else:
                g.request_log_counter_interval = data["request_log_counter_interval"]
                g.request_log_counter.interval = data["request_log_counter_interval"]

            for k, v in data["request_log_counter"].items():
                g.request_log_counter.counter[k] = v
            g.ask_log_queue.queue = deque(data["ask_log_queue"])

            logger.info("Requests statistics loaded.")
    except FileNotFoundError:
        logger.info("File statistics.json not found, skip loading statistics.")
    except json.decoder.JSONDecodeError:
        logger.warning("Failed to load statistics.json, skip loading statistics.")