import time
from collections import OrderedDict


class TimeCounter:
    def __init__(self, time_window: int=None, duration: int=None):
        if time_window % duration != 0 or time_window <= 0 or duration <= 0 or time_window < duration:
            raise ValueError("time_window must be a multiple of duration, and both must be positive")
        self.time_window = time_window or 3 * 24 * 60 * 60
        self.duration = duration or 30
        self.counter = OrderedDict()

    def count(self):
        current_time = time.time()
        current_interval = int(current_time // self.duration)

        # 增加当前时间段的计数
        if current_interval not in self.counter:
            self.counter[current_interval] = 1
        else:
            self.counter[current_interval] += 1

        # 删除过期的时间段
        self.remove_expired_intervals()

    def remove_expired_intervals(self):
        current_time = time.time()
        current_interval = int(current_time // self.duration)
        expired_interval = current_interval - (self.time_window // self.duration)

        keys_to_delete = []
        for key in self.counter:
            if key <= expired_interval:
                keys_to_delete.append(key)
            else:
                break

        for key in keys_to_delete:
            del self.counter[key]

    def __repr__(self):
        return f"TimeCounter(time_window={self.time_window}, duration={self.duration}, counter={self.counter})"
