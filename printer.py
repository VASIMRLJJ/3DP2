from serial import Serial, SerialException, SerialTimeoutException
from time import time, sleep
import re
import threading


class Printer:
    def __init__(self, port: str):
        self.port = port
        self.baud_rate = 115200
        self.name = 'unknown'
        self.serial = None
        self.timeout = 5
        self.read_timeout = 1

        self.run = False

        self.updater_t = threading.Thread(target=self.read_data)
        self.updater_t.setDaemon(True)

        self._command_received = True
        self.t_received = True
        self.p_received = True

        self.t1 = '0.00'
        self.t2 = '0.00'
        self.t3 = '0.00'

        self.x = '0.00'
        self.y = '0.00'
        self.z = '0.00'
        self.e = '0.00'

    def __del__(self):
        if self.serial is not None:
            self.serial.close()
        self.run = False

    def connect(self, baud_rate=None):
        if self.serial:
            self.run = False
            self.serial.close()
        if baud_rate is not None:
            self.baud_rate = baud_rate
        try:
            self.serial = Serial(self.port, self.baud_rate, timeout=self.timeout, writeTimeout=self.timeout)
        except SerialException as e:
            print(str(e))
            return False
        sleep(10)  # CURA:Ensure that we are not talking to the boot loader. 1.5 seconds seems to be the magic number
        successful_responses = 0

        self.serial.write(b"\n")  # CURA:Ensure we clear out previous responses
        self.serial.write(b"M105\n")

        timeout_t = time() + self.timeout

        while timeout_t > time():
            line = self.serial.readline()
            print(line)
            if b"ok T:" in line:
                successful_responses += 1
                self.serial.write(b"M105\n")
                if successful_responses >= 3:
                    self.run = True
                    self.updater_t.start()
                    self.sendCommand('M105')
                    self.sendCommand('M114')
                    return True

        self.serial.close()
        self.serial = None
        return False

    #  Send a command to printer.
    def sendCommand(self, command: str):
        if self.serial is None or not self._command_received:
            return 'fail'
        command = command.encode()
        if not command.endswith(b"\n"):
            command += b"\n"

        timeout_t = time() + self.timeout
        self.serial.write(command)
        self._command_received = False

        while timeout_t > time():
            if self._command_received:
                return 'success'
        self._command_received = True
        return 'fail'

    def read_data(self):
        while self.run:
            try:
                line = self.serial.readline()
            except:
                continue

            if line.startswith(b"ok T"):
                line1 = line.decode()
                if 'B:' in line1:
                    res = re.findall("B: ?([\d\.]+)", line1)
                    self.t3 = res[0][0]
                    if 'T:' in line1:
                        res = re.findall("T: ?([\d\.]+)", line1)
                        self.t1 = res[0][0]
                    else:
                        res = re.findall("T0: ?([\d\.]+)", line1)
                        self.t1 = res[0][0]
                self.sendCommand('M105')

            if line.startswith(b"ok C:"):
                line1 = line.decode()
                res = re.findall("X: ?([\d\.]+)", line1)
                self.x = res[0][0]
                res = re.findall("Y: ?([\d\.]+)", line1)
                self.y = res[0][0]
                res = re.findall("Z: ?([\d\.]+)", line1)
                self.z = res[0][0]
                res = re.findall("E: ?([\d\.]+)", line1)
                self.e = res[0][0]
                self.sendCommand('M114')

            if b"ok" in line:
                self._command_received = True


if __name__ == '__main__':
    p = Printer('COM5')
    ret = False
    while not ret:
        print('connecting\n'+str(ret))
        ret = p.connect(250000)
        if ret:
            break
        sleep(5)
    while True:
        print(p.t1)
        print(p.t3)
        sleep(1)
