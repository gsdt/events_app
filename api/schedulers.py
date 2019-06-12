import threading

class Scheduler(threading.Thread):
    def __init__(self, sleep_period=1):
        self.stop_event = threading.Event()
        self.sleep_period = sleep_period