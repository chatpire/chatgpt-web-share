import json
import os
from collections import deque

import api.globals as g
from api.conf import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def dump_stats(print_log=True):
    path = os.path.join(Config().data.data_dir, "statistics.json")
    data = {
        "request_log_counter_interval": Config().stats.request_counts_interval,
        "request_log_counter": g.request_log_counter.counter,
        "ask_log_queue": list(g.ask_log_queue.queue)
    }
    with open(path, "w") as f:
        json.dump(data, f)
    if print_log:
        logger.info(f"Requests statistics dumped to {path}.")


def load_stats():
    path = os.path.join(Config().data.data_dir, "statistics.json")
    logger.debug(f"loading statistics from {path}")
    try:
        with open(path, "r") as f:
            data = json.load(f)

            if Config().stats.request_counts_interval != data["request_log_counter_interval"]:
                logger.warning("request_log_counter_interval is different from the saved one, counter cleared.")
                return

            for k, v in data["request_log_counter"].items():
                g.request_log_counter.counter[int(k)] = v
            g.request_log_counter.remove_expired_intervals()
            g.ask_log_queue.queue = deque(data["ask_log_queue"])

            logger.info("Requests statistics loaded.")
    except FileNotFoundError:
        logger.info("File statistics.json not found, skip loading statistics.")
    except json.decoder.JSONDecodeError:
        logger.warning("Failed to load statistics.json, skip loading statistics.")
