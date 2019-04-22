from serial import Serial, SerialException
from time import time, sleep
import re


class Printer:
    def __init__(self, port: str):
        self.port = port
        self.baud_rate = 115200
        self.name = 'unknown'
        self.serial = None
        self.timeout = 3
        self.read_timeout = 1

        self.t1 = '0.00'
        self.t2 = '0.00'
        self.t3 = '0.00'
        self.e = '0.00'

    def __del__(self):
        if self.serial is not None:
            self.serial.close()

    def connect(self, baud_rate=None):
        if baud_rate is not None:
            self.baud_rate = baud_rate
        try:
            self.serial = Serial(self.port, self.baud_rate, timeout=self.timeout, writeTimeout=self.timeout)
        except SerialException as e:
            print(str(e))
            return False
        sleep(3)  # CURA:Ensure that we are not talking to the boot loader. 1.5 seconds seems to be the magic number
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
                    return True

        self.serial.close()
        self.serial = None
        return False

    def read_data(self):
        if self.serial is None:
            return False

        try:
            self.serial.write(b'M105\nM114\n')
        except SerialException:
            return False

        timeout_t = time() + self.read_timeout
        results = [None, None, None]

        while timeout_t > time():
            line = self.serial.readline()
            print(line)
            # Temperature message. 'T:' for extruder and 'B:' for bed
            if b"ok T:" in line or line.startswith(b"T:") or b"ok B:" in line or line.startswith(b"B:"):
                extruder_temperature_matches = re.findall(b"T(\d*): ?([\d\.]+) ?\/?([\d\.]+)?", line)
                results[0] = extruder_temperature_matches
                bed_temperature_matches = re.findall(b"B: ?([\d\.]+) ?\/?([\d\.]+)?", line)
                results[1] = bed_temperature_matches

            if b'X:' in line or line.startswith(b'X:'):
                extruder_position = re.findall(b"X: ?([\d\.]+)Y: ?([\d\.]+)Z: ?([\d\.]+)E: ?([\d\.]+)", line)
                results[2] = extruder_position

        return self.data_packer(results)

    def data_packer(self, results):
        print(results)
        if results[0] is None or results[1] is None or results[2] is None:
            return False
        t1 = results[0][0][1]
        t2 = b'NaN'
        t3 = results[1][0][0]
        x = results[2][0]
        y = results[2][1]
        z = results[2][2]
        e = results[2][3]
        result = {
            'S': {
                'T1': t1.decode(encoding='ascii'),
                'T2': t2.decode(encoding='ascii'),
                'T3': t3.decode(encoding='ascii')
            },
            'P': {
                'X': x.decode(encoding='ascii'),
                'Y': y.decode(encoding='ascii'),
                'Z': z.decode(encoding='ascii'),
                'E': e.decode(encoding='ascii')
            },
            'T': '00.00'
        }
        return result


if __name__ == '__main__':
    p = Printer('COM5', 250000)
    ret = False
    while not ret:
        print('connecting\n'+str(ret))
        ret = p.connect()
        if ret:
            break
        sleep(5)
    while True:
        print(p.read_data())
        sleep(1)
