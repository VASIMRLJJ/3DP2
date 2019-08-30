import socket
import json
import requests
from printer import Printer
import threading
import time


class Uploader:
    def __init__(self, p: Printer):
        self.ip = ''  # 设备的ip
        self.eid = ''  # 设备id
        self.pw = ''  # 设备密码
        self.is_started = False
        self.lock = threading.Lock()
        self.p = p

        self.sock = None
        self.sender_t = threading.Thread(target=self.sender)
        self.sender_t.setDaemon(True)
        self.receiver_t = threading.Thread(target=self.receiver)
        self.receiver_t.setDaemon(True)

        self.run = False

        self.dip = ''

    def __del__(self):
        if self.sock:
            self.sock.close()
        self.run = False

    def connect(self, ip: str, eid: str, pw: str):
        if self.sock:
            self.run = False
            self.sock.close()
        self.ip = ip
        self.eid = eid
        self.pw = pw
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, 8093))
        except Exception:
            return False
        ret = self.on_connect()
        return ret

    def on_connect(self):
        login = {
            'EID': self.eid,
            'PW': self.pw
        }
        self.sock.sendall(('AUT'+json.dumps(login)+'END'+'\n').encode('ascii'))
        rec = self.sock.recv(1024).decode('ascii')
        rec.replace('\r\n', '')
        print(rec)
        if rec == 'OK':
            self.loop_start()
            return True
        else:
            self.sock.close()
            return False

    def loop_start(self):
        try:
            dip = requests.get('https://ifconfig.co/ip', timeout=10).text.replace('\n', '')
            self.dip = dip
        except:
            self.dip = '0.0.0.0'
        self.run = True
        self.receiver_t.start()
        self.sender_t.start()

    def get_data(self):
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
        }
        return data

    def sender(self):
        while self.run:
            if self.is_started:
                self.lock.acquire()
                self.sock.send(('STA'+json.dumps(self.get_data())+'END'+'\n').encode('ascii'))
                print(('STA'+json.dumps(self.get_data())+'END'+'\n').encode('ascii'))
                self.lock.release()
                time.sleep(1)
            else:
                self.lock.acquire()
                self.sock.send(b'{}\n')
                self.lock.release()
                time.sleep(5)

    def receiver(self):
        while self.run:
            rec = self.sock.recv(1024).decode('ascii').replace('\r\n', '')
            if rec == 'STA':
                self.is_started = True
            if rec == 'STOP':
                self.is_started = False
            else:
                self.lock.acquire()
                self.sendcmd(rec)
                self.lock.release()

    def sendcmd(self, rec):
        try:
            data2 = json.loads(rec)
        except json.JSONDecodeError:
            print('naj')
            return
        if 'EID' in data2.keys() and 'I' in data2.keys():
            if data2['EID'] == self.eid:
                data33 = self.p.sendCommand(data2['I'])
                data333 = {'EID': self.eid, 'I': data2['I'], 'IS': data33}
                print(data333)
                self.sock.send((json.dumps(data333)+'\n').encode('ascii'))


if __name__ == '__main__':
    p = Printer('COM5')
    u = Uploader(p)
    while True:
        pass
