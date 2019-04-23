from flask import Flask, render_template, request
from printer import Printer
from uploader import Uploader
import os
import platform
import time
from led import LED


COM = '/dev/ttyUSB0'

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
    u.loop_start()
    return render_template('index.html')


@app.route('/wizard')
def wizard():
    os.remove('settings.txt')
    global u, p
    u.run = False
    p.run = False
    return render_template('wizard.html')


@app.route('/api/wifi_setting', methods=['GET', 'POST'])
def wifi():
    if request.method == 'POST':
        settings['ssid'] = request.form['ssid']
        settings['psw'] = request.form['psw']
        return 'success'


@app.route('/api/printer_test', methods=['GET', 'POST'])
def printer_test():
    if request.method == 'POST':
        baud_rate = request.form['baud_rate']
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


if __name__ == '__main__':
    if os.path.isfile('settings.txt'):
        with open('settings.txt', 'r') as f:
            settings = eval(f.read())
        l = LED()
        if platform.system() == 'Linux':
            r = os.popen('nmcli conn show').read()
            if not 'wlan0' in r:
                r = os.popen('nmcli d wifi connect "'+settings['ssid']+'" password "'+settings['psw']+'" wlan0')
                while not 'success' in r.read():
                    time.sleep(1)
        l.t = 0.2
        while True:
            ret1 = p.connect(int(settings['baud_rate']))
            ret2 = u.connect(settings['ip'], settings['eid'], settings['pw'])
            if ret1 and ret2:
                break
            time.sleep(5)
        u.loop_start()
        l.stop()
    app.run(host='0.0.0.0', port=80)
