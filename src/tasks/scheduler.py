# scheduler.py - Programador de tareas para Bot Comunidad
import time
import threading

class Scheduler:
    def __init__(self):
        self.tasks = []
    def add_task(self, func, run_at):
        self.tasks.append((func, run_at))
    def run(self):
        while True:
            now = time.time()
            for func, run_at in list(self.tasks):
                if now >= run_at:
                    func()
                    self.tasks.remove((func, run_at))
            time.sleep(1)
