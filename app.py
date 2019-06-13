from flask import Flask, render_template, request
from printer import Printer
from uploader import Uploader
import os
import platform
import time
from led import LED
import glob

if platform.system() == 'Linux':
    COM = glob.glob(r'/dev/ttyUSB*')
    COM.append(glob.glob(r'/dev/ttyACM*'))
    if len(COM) == 0:
        COM = '/dev/ttyUSB0'
    else:
        COM = COM[0][0]
else:
    COM = 'COM6'

app = Flask(__name__)
p = Printer(COM)
u = Uploader(p)

settings = {
    'ssid': '',
    'psw': '',
    'ip': '',
    'eid': '',
    'pw': '',
    'baud_rate': ''
}


@app.route('/')
def enter():
    if os.path.isfile('settings.txt'):
        return render_template('index.html')
    else:
        return render_template('wizard.html')


@app.route('/index')
def index():
    with open('settings.txt', 'w') as f:
        f.write(str(settings))
    if platform.system() == 'Linux':
        os.system('reboot')
    else:
        return render_template('index.html')


@app.route('/setting')
def setting():
    return render_template('settings.html', **settings)


@app.route('/reset')
def reset():
    os.remove('settings.txt')
    if platform.system() == 'Linux':
        os.system('reboot')
    else:
        exit()
    return 200


@app.route('/api/wifi_setting', methods=['GET', 'POST'])
def wifi():
    if request.method == 'POST':
        ssid = request.form['ssid']
        psw = request.form['psw']
        ret = wifi_connect(ssid, psw)
        if ret:
            settings['ssid'] = ssid
            settings['psw'] = psw
            return '连接成功'
        else:
            return '连接失败'


@app.route('/api/printer_test', methods=['GET', 'POST'])
def printer_test():
    if request.method == 'POST':
        baud_rate = request.form['baud_rate']
        if platform.system() == 'Linux':
            global COM
            COM = glob.glob(r'/dev/ttyUSB*')
            COM.append(glob.glob(r'/dev/ttyACM*'))
            print(COM)
            if len(COM) == 0:
                COM = '/dev/ttyUSB0'
            else:
                COM = COM[0][0]
            p.port = COM
        ret = p.connect(int(baud_rate))
        if not ret:
            return '连接失败'
        else:
            settings['baud_rate'] = baud_rate
            return '连接成功'


@app.route('/api/server_test', methods=['GET', 'POST'])
def server_test():
    if request.method == 'POST':
        ip = request.form['ip']
        eid = request.form['eid']
        pw = request.form['pw']
        ret = u.connect(ip, eid, pw)
        if not ret:
            return '连接失败'
        else:
            settings['ip'] = ip
            settings['eid'] = eid
            settings['pw'] = pw
            return '连接成功'


def wifi_connect(ssid: str, psw: str):
    if platform.system() == 'Linux':
        r = os.popen('nmcli conn show').read()
        if not 'wlan0' in r:
            r = os.popen('nmcli d wifi connect "' + ssid + '" password "' + psw + '" wlan0')
            timeout_t = time.time() + 10
            while timeout_t > time.time():
                if 'success' in r.read():
                    return True
            return False
    return True


if __name__ == '__main__':
    if os.path.isfile('settings.txt'):
        with open('settings.txt', 'r') as f:
            settings = eval(f.read())
        l = LED()
        while True:
            ret = wifi_connect(settings['ssid'], settings['psw'])
            if ret:
                break
        l.t = 0.2
        while True:
            ret1 = p.connect(int(settings['baud_rate']))
            ret2 = u.connect(settings['ip'], settings['eid'], settings['pw'])
            if ret1 and ret2:
                break
            time.sleep(10)
        l.stop()
    if platform.system() == 'Linux':
        app.run(host='0.0.0.0', port=80)
    else:
        app.run(host='127.0.0.1', port=80)

