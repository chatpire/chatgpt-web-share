from api.conf import Config
from utils.stats import RequestCounter, TimeQueue

config = Config()

reverse_proxy_log_file = None
reverse_proxy_process = None
server_log_filename = None

startup_time = None

request_log_counter = RequestCounter(
    time_window=config.stats.request_counter_time_window,
    interval=config.stats.request_counts_interval
)
ask_log_queue = TimeQueue(config.stats.ask_log_time_window)  # 7 days

chatgpt_manager = None
