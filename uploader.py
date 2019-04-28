import socket
import json
import requests
from printer import Printer
import threading
import time


class Uploader:
    def __init__(self, p: Printer):
        self.ip = ''
        self.eid = ''
        self.pw = ''
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
        self.sock.sendall(('AUT'+json.dumps(login)+'\n').encode('ascii'))
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
                    'X': '00.00',
                    'Y': '00.00',
                    'Z': '00.00',
                    'E': '00.00'
                },
                'T': self.p.e
            }
        }
        return data

    def sender(self):
        while self.run:
            if self.is_started:
                self.lock.acquire()
                self.sock.send(('STA'+json.dumps(self.get_data())+'\n').encode('ascii'))
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
                data22 = {'EID': self.eid, 'RI': data2['I']}
                self.sock.send((json.dumps(data22)+'\n').encode('ascii'))
                rec2 = self.sock.recv(1024).decode('ascii').replace('\r\n', '')
                print(rec2)
                try:
                    data222 = json.loads(rec2)
                except json.JSONDecodeError:
                    print('naj2')
                    return
                if 'EID' in data222.keys() and 'IDE' in data222.keys():
                    print(data222)
                    if data222['IDE'] != 'OK':
                        return
                    data33 = p.sendCommand(data2['I'])
                    data333 = {'EID': self.eid, 'I': data2['I'], 'IS': data33}
                    print(data333)
                    self.sock.send((json.dumps(data333)+'\n').encode('ascii'))


if __name__ == '__main__':
    p = Printer('COM5')
    u = Uploader(p)
    while True:
        pass
