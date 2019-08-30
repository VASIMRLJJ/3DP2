from flask import Flask, render_template, request
from printer import Printer
from uploader import Uploader
import os
import platform
import time
from led import LED
import glob
import threading

# 提取com口名称字符串
if platform.system() == 'Linux':
    COM = glob.glob(r'/dev/ttyUSB*') + glob.glob(r'/dev/ttyACM*')
    if len(COM) == 0:
        COM = '/dev/ttyUSB0'
    else:
        COM = COM[0]
else:  # 用作在Windows上面测试
    COM = 'COM6'

# 初始化全局变量
app = Flask(__name__)  # flask的app
p = Printer(COM)  # 打印机对象
u = Uploader(p)  # 平台数据上传器对象

# 配置数据字典
settings = {
    'ssid': '',  # wifi名称
    'psw': '',  # wifi密码
    'ip': '',  # 平台服务器ip
    'eid': '',  # 设备eid
    'pw': ''  # 设备密码
}


# 根路由，如果有'settings.txt'文件，渲染index，没有则渲染wizard
@app.route('/')
def enter():
    if os.path.isfile('settings.txt'):
        return render_template('index.html')
    else:
        return render_template('wizard.html')


# 写入配置文件，实测需要重启才能写入
@app.route('/index')
def index():
    with open('settings.txt', 'w') as f:
        f.write(str(settings))
    if platform.system() == 'Linux':
        os.system('reboot')
    else:
        return render_template('index.html')


# 渲染设置页面
@app.route('/setting')
def setting():
    return render_template('settings.html', **settings)


# 恢复出厂设置
@app.route('/reset')
def reset():
    os.remove('settings.txt')
    if platform.system() == 'Linux':
        os.system('reboot')
    else:
        exit()
    return 200


# 测试wifi连接
@app.route('/api/wifi_setting', methods=['GET', 'POST'])
def wifi():
    if request.method == 'POST':
        ssid = request.form['ssid']
        psw = request.form['psw']
        ret = wifi_connect(ssid, psw)  # 测试连接是否成功
        if ret:  # 连接成功则设置settings字典的wifi账号密码值
            settings['ssid'] = ssid
            settings['psw'] = psw
            return '连接成功'
        else:
            return '连接失败'


# @app.route('/api/printer_test', methods=['GET', 'POST'])
# def printer_test():
#     if request.method == 'POST':
#         baud_rate = request.form['baud_rate']
#         if platform.system() == 'Linux':
#             global COM
#             COM = glob.glob(r'/dev/ttyUSB*') + glob.glob(r'/dev/ttyACM*')
#             print(COM)
#             if len(COM) == 0:
#                 COM = '/dev/ttyUSB0'
#             else:
#                 COM = COM[0]
#             p.port = COM
#         ret = p.connect(int(baud_rate))
#         if not ret:
#             return '连接失败'
#         else:
#             settings['baud_rate'] = baud_rate
#             return '连接成功'


# 测试服务器连接
@app.route('/api/server_save', methods=['GET', 'POST'])
def server_test():
    if request.method == 'POST':
        ip = request.form['ip']
        eid = request.form['eid']
        pw = request.form['pw']
        ret = u.connect(ip, eid, pw)  # 测试服务器连接
        if not ret:
            return '连接失败'
        else:  # 连接成功则写入配置
            settings['ip'] = ip
            settings['eid'] = eid
            settings['pw'] = pw
            return '连接成功'


# 重启
@app.route('/reboot', methods=['GET', 'POST'])
def reboot_system():
    if platform.system() == 'Linux':
        os.system('reboot')
    else:
        exit()


# 连接wifi测试
def wifi_connect(ssid: str, psw: str):
    if platform.system() == 'Linux':
        r = os.popen('nmcli conn show').read()  # 查看已有连接
        if not 'wlan0' in r:  # 查看wifi是否已经连接
            r = os.popen('nmcli d wifi connect "' + ssid + '" password "' + psw + '" wlan0')  # 利用nm连接wifi
            timeout_t = time.time() + 10
            while timeout_t > time.time():  # 10s以内自动重连，连不上判断为失败
                if 'success' in r.read():
                    os.system('sh ./route.sh')  # 连接成功，则配置子网等
                    return True
            return False
    return True


# 启动flask的web服务器
def configure():
    if platform.system() == 'Linux':
        app.run(host='0.0.0.0', port=80)  # Linux的local
    else:
        app.run(host='127.0.0.1', port=80)  # Windows的localhost，测试用


if __name__ == '__main__':
    l = LED()  # 实例化led对象
    l.t = 1.5  # 闪灯间隔为1.5s
    t = threading.Thread(target=configure)
    t.start()  # 开启启动flask的web服务器的线程，不然主函数无法向下运行
    if os.path.isfile('settings.txt'):  # 有配置文件则读取配置文件
        with open('settings.txt', 'r') as f:
            settings = eval(f.read())
       
        while True:  # 连接wifi并自动重连
            ret = wifi_connect(settings['ssid'], settings['psw'])
            if ret:
                os.system('sh ./route.sh')  # 网络配置脚本
                break
        l.t = 0.8  # 闪灯变快以示完成
        while True:  # 连接打印机并自动重连，同时自动判定波特率
            ret = p.connect(115200)
            if ret:
                break
            ret = p.connect(250000)
            if ret:
                break
            time.sleep(5)
        l.t = 0.1  # 闪灯变快以示完成
        while True:  # 连接服务器并自动重连
            ret = u.connect(settings['ip'], settings['eid'], settings['pw'])
            if ret:
                break
            time.sleep(5)
        l.stop()  # 灯常亮以示全部完成


