import threading
import time
# from api import models
from datetime import timedelta

class DoNextTask(threading.Thread):
    def __init__(self, sleep_period=1):
        self._stop_event = threading.Event()
        self.sleep_period = sleep_period
        
        threading.Thread.__init__(self, name="DoNextTask Thread")

    def set_task(self, delay=0, task=None, *args):
        self.task = task
        self.delay = delay
        self.args = args
    
    def get_task(self):
        return self.delay, self.task, self.args

    def run(self):
        count = 0
        while not self._stop_event.isSet():
            if count == self.delay:
                break
            count += 1
            self._stop_event.wait(self.sleep_period)
        
        if self.task and count == self.delay:
            self.task(*self.args)

    def kill(self, timeout=None):
        self._stop_event.set()
        threading.Thread.join(self, timeout)
        print(f"{self.getName()} died.")

class DoNextTaskSingleton:
    __instance__ = None
    @staticmethod
    def get_instace():
        if DoNextTaskSingleton.__instance__ is None:
            DoNextTaskSingleton()
        return DoNextTaskSingleton.__instance__
    
    def __init__(self):
        if DoNextTaskSingleton.__instance__ is not None:
            return
        else:
            DoNextTaskSingleton.__instance__ = DoNextTask()

instance = DoNextTaskSingleton()

def testjob():
    print("OK")

