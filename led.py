import threading
import os
import time
import platform


class LED:
    def __init__(self):
        self.t = 0.5
        self.flash_t = threading.Thread(target=self.flash)
        self.flash_t.setDaemon(True)
        self.run = True
        self.flash_t.start()

    def stop(self):
        self.run = False
        time.sleep(1)
        if platform.system() == 'Linux':
            os.system('gpio write 30 1')

    def flash(self):
        while self.run:
            if platform.system() == 'Windows':
                continue
            os.system('gpio write 30 1')
            time.sleep(self.t)
            os.system('gpio write 30 0')
            time.sleep(self.t)
