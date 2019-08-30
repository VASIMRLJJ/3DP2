import threading
import os
import time
import platform
# 本文件的正常运行需要系统编译安装wiringpi(树莓派)
# 香橙派0版本：https://github.com/xpertsavenue/WiringOP-Zero
# 其他pi依据芯片而定


class LED:
    def __init__(self):
        self.t = 1.0  # 间隔时间
        self.flash_t = threading.Thread(target=self.flash)  # 闪灯线程
        self.flash_t.setDaemon(True)  # 设置为守护线程
        self.run = True  # 线程开关
        self.flash_t.start()  # 启动闪灯线程

    def stop(self):
        self.run = False  # 停止线程
        time.sleep(1)
        if platform.system() == 'Linux':
            os.system('gpio write 30 1')  # 将灯变为常亮

    def flash(self):  # 闪灯
        while self.run:
            if platform.system() == 'Windows':  # 用于在pc上面测试
                continue
            # 以下四行同单片机流水灯
            os.system('gpio write 30 1')
            time.sleep(self.t)
            os.system('gpio write 30 0')
            time.sleep(self.t)
