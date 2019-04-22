from flask import Flask, render_template, request
from printer import Printer
from uploader import Uploader
import os
import pywifi


COM = 'COM5'

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
    global u, p
    del p
    del u
    p = Printer(COM)
    u = Uploader(p)
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
        profile = pywifi.Profile()
        profile.ssid = settings['ssid']
        profile.auth = pywifi.const.AUTH_ALG_OPEN
        profile.akm.append(pywifi.const.AKM_TYPE_WPA2PSK)
        profile.cipher = pywifi.const.CIPHER_TYPE_CCMP
        profile.key = settings['psw']

        wifi = pywifi.PyWiFi()
        iface = wifi.interfaces()[0]
        profile = iface.add_network_profile(profile)
        iface.connect(profile)

        p.connect(int(settings['baud_rate']))
        u.connect(settings['ip'], settings['eid'], settings['pw'])
        u.loop_start()
    app.run(host='127.0.0.1', port=8080)
