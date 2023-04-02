from api.config import Config, config_file
from utils.data_types import RequestCounter, TimeQueue

# log settings

reverse_proxy_log_file = None
reverse_proxy_process = None
server_log_filename = None

# system info

startup_time = None

# request_statistics

config = Config(config_file)
request_log_counter_time_window = config.get("request_log_counter_time_window", 30 * 24 * 60 * 60)  # 30 days
request_log_counter_interval = config.get("request_log_counter_interval", 30 * 60)  # 30 minutes
request_log_counter = RequestCounter(
    time_window=request_log_counter_time_window,
    interval=request_log_counter_interval
)
ask_log_queue = TimeQueue(config.get("ask_log_time_window", 7 * 24 * 60 * 60))  # 7 days
