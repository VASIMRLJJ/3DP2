import socket
import json
import requests
from printer import Printer
import threading
import time


class Uploader:
    def __init__(self, p: Printer):
        self.ip = ''  # 服务器的ip
        self.eid = ''  # 设备id
        self.pw = ''  # 设备密码
        self.is_started = False  # 是否开始传输数据标志量
        self.lock = threading.Lock()  # 互斥锁，用于设置临界区，使得控制数据和状态数据的发送不冲突
        self.p = p  # 打印机对象

        self.sock = None  # socket连接对象
        self.sender_t = threading.Thread(target=self.sender)  # 发送线程
        self.sender_t.setDaemon(True)  # 设为守护
        self.receiver_t = threading.Thread(target=self.receiver)  # 接收线程
        self.receiver_t.setDaemon(True)  # 设为守护

        self.run = False  # 线程开关

        self.dip = ''  # 设备的ip

    def __del__(self):  # 删除对象时停住线程并关闭socket连接
        if self.sock:
            self.sock.close()
        self.run = False

    def connect(self, ip: str, eid: str, pw: str):
        if self.sock:  # 如果有连接则关闭连接
            self.run = False
            self.sock.close()
        self.ip = ip  # 服务器ip
        self.eid = eid  # 设备id
        self.pw = pw  # 设备密码
        try:  # 连接socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, 8093))
        except Exception:
            return False
        ret = self.on_connect()  # 发给服务器进行验证
        return ret

    def on_connect(self):  # 验证设备账号密码
        login = {
            'EID': self.eid,
            'PW': self.pw
        }  # 设备认证数据DATA0
        self.sock.sendall(('AUT'+json.dumps(login)+'END'+'\n').encode('ascii'))  # 发送认证数据
        rec = self.sock.recv(1024).decode('ascii')  # 接收平台返回数据
        rec.replace('\r\n', '')  # 清除换行符(java平台所致)
        print(rec)  # 输出以便调试
        if rec == 'OK':  # 认证通过则开启线程
            self.loop_start()
            return True
        else:  # 否则关闭连接
            self.sock.close()
            return False

    def loop_start(self):  # 开启线程
        try:  # 获取设备ip
            dip = requests.get('https://ifconfig.co/ip', timeout=10).text.replace('\n', '')
            self.dip = dip
        except:  # 获取不到则按0000处理
            self.dip = '0.0.0.0'
        self.run = True  # 开启发送接收线程
        self.receiver_t.start()
        self.sender_t.start()

    def get_data(self):  # 获取打印机数据
        data = {
            'ST': {
                'EID': self.eid,
                'IP': self.dip
            },
            'DY': {
                'S': {
                    'T1': self.p.t1,
                    'T2': self.p.t2,
                    'T3': self.p.t3
                },
                'P': {
                    'X': self.p.x,
                    'Y': self.p.y,
                    'Z': self.p.z,
                    'E': self.p.e
                },
                'T': '00.00'
            }
        }  # 按照状态数据DATA1格式取打印机实时数据作为字典返回
        return data

    def sender(self):  # 发送数据线程
        while self.run:
            if self.is_started:  # 如果开始发送则发送数据
                self.lock.acquire()  # 临界区开始
                self.sock.send(('STA'+json.dumps(self.get_data())+'END'+'\n').encode('ascii'))  # 发送状态数据
                print(('STA'+json.dumps(self.get_data())+'END'+'\n').encode('ascii'))
                self.lock.release()  # 临界区结束
                time.sleep(1)  # 间隔为1s
            else:  # 没有开始发送则发送心跳包
                self.lock.acquire()
                self.sock.send(b'{}\n')
                self.lock.release()
                time.sleep(5)  # 间隔为5s

    def receiver(self):
        while self.run:
            rec = self.sock.recv(1024).decode('ascii').replace('\r\n', '')  # socket接收数据（阻塞）
            if rec == 'STA':  # 服务器开始发送状态数据信号
                self.is_started = True
            if rec == 'STOP':  # 服务器停止发送状态数据信号
                self.is_started = False
            else:  # 向打印机发送控制数据
                self.lock.acquire()
                self.sendcmd(rec)
                self.lock.release()

    def sendcmd(self, rec):  # 向打印机发送控制数据
        try:  # 解析json包
            data2 = json.loads(rec)
        except json.JSONDecodeError:
            print('naj')  # 解析失败输出naj(not a json)，一般是java平台问题
            return
        if 'EID' in data2.keys() and 'I' in data2.keys():  # 解析指令并发送给打印机
            if data2['EID'] == self.eid:  # 判定eid是否正确
                data33 = self.p.sendCommand(data2['I'])  # 发送命令给打印机
                data333 = {'EID': self.eid, 'I': data2['I'], 'IS': data33}  # 执行状态数据
                print(data333)  # 输出便于调试
                self.sock.send((json.dumps(data333)+'\n').encode('ascii'))  # 向平台返回执行状态


# 用作单元测试
if __name__ == '__main__':
    p = Printer('COM5')
    u = Uploader(p)
    while True:
        pass
