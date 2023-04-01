from api.chatgpt import ChatGPTManager
from collections import deque

from api.config import config
from utils.time_counter import TimeCounter
from utils.time_queue import TimeQueue

chatgpt_manager = ChatGPTManager()

reverse_proxy_log_file = None

reverse_proxy_process = None

server_log_filename = None

# request_statistics

request_log_counter = TimeCounter(
    time_window=config.get("request_log_counter_time_window", 30 * 24 * 60 * 60),  # 30 days
    duration=config.get("request_log_counter_duration", 10 * 60)  # 10 minutes
)
ask_log_queue = TimeQueue(config.get("statistic_log_time_window", 7 * 24 * 60 * 60))  # 7 days
