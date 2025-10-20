# worker.py - Worker para tareas asíncronas en Bot Comunidad
import threading

class Worker:
    def __init__(self):
        self.jobs = []
    def add_job(self, func, *args, **kwargs):
        self.jobs.append((func, args, kwargs))
    def run(self):
        while self.jobs:
            func, args, kwargs = self.jobs.pop(0)
            t = threading.Thread(target=func, args=args, kwargs=kwargs)
            t.start()
