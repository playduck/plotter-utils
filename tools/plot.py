import sys
import math
import select
import serial
import time
import atexit
import keyboard
import argparse
import threading
import datetime

VERSION = "v1.0.0"
ser = None

def availabeBuffer():
    while 1:
        reminaingBuffer = 0
        ser.flushInput()
        ser.flushInput()

        ser.write(bytes("\033.B\r\n", "utf-8"))
        time.sleep(0.5)
        raw = ser.read_until("\r", 5)
        print(raw)

        try:
            if raw:
                reminaingBuffer, _ = raw.decode("utf-8").split("\r")
            else:
                reminaingBuffer = -1
        except:
            reminaingBuffer = -2


        print("REM", reminaingBuffer)
    return int(reminaingBuffer)

class Job(threading.Thread):

    def __init__(self, port, file, delay, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.set()
        self.__running = threading.Event()
        self.__running.set()

        self.port = port
        self.file = file
        self.delay = delay

    def run(self):
        global ser

        print("opening file", self.file)
        lines = ""
        with open(self.file,"r") as f:
            lines = f.read()
        command_list = lines.split(";")

        line_list = list()
        for i in range(len(command_list)):
            line_list.append(command_list[i] + ";")
        line_list = [f.strip() for f in line_list]

        print("opening serial port", self.port)
        ser = serial.Serial(self.port, 9600, timeout=0.5)

        i = 0
        print("LEN", len(line_list))
        while i < len(line_list):
            print(i, line_list[i])
            ser.write(bytes(line_list[i], "utf-8"))
            time.sleep(len(line_list[i]) * 0.01)

            i = i + 1;

            if(self.__running.isSet()):
                self.__flag.wait()


        ser.close()
        self.stop()

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def stop(self):
        print("stopping")
        self.__flag.set()
        self.__running.clear()

def exitHandler():
    global ser
    try:
        ser.write(bytes("\033.J\r\n", "utf-8"))
        ser.write(bytes("\033.K\r\n", "utf-8"))
        ser.write(bytes("\033.Z\r\n", "utf-8"))
        ser.close()
    except: pass
    print("Aborting")
    return 0

atexit.register(exitHandler)

parser = argparse.ArgumentParser(description="Roland DXY-1150 Plotter utility")
parser.add_argument('-p', '--port',
                    action='store',
                    dest='port',
                    help='Serialport',
                    type=str
                    )
parser.add_argument('-f', '--file',
                    action='store',
                    dest='file',
                    help='HPGL File',
                    type=str
                    )
parser.add_argument('-d', '--delay',
                    action='store',
                    dest='delay',
                    help='Command delay',
                    type=float,
                    default=0.05
                    )
parser.add_argument('-v', '--version',
                    action='store_true',
                    dest='version',
                    help='displays version'
                    )

args = vars(parser.parse_args())

if(args.get("version", None) is True):
    print(VERSION)
    sys.exit(0)
if(args.get("file", None) is None):
    print("input file cannot be undefined.")
    sys.exit(0)
if(args.get("port", None) is None):
    print("port cannot be undefined. Add using --port flag")
    sys.exit(0)

a = Job(args.get("port"), args.get("file"), args.get("delay"))
a.start()

time.sleep(0.5)

# b = threading.Thread(target=availabeBuffer)
# b.run()

print("\ntype \'p\' to pause and \'r\' to resume\n")
while a.is_alive():
    # read inputt, 1 second timeout
    i, o, e = select.select( [sys.stdin], [], [], 1 )
    if i:
        # if no timeout occured
        prompt = sys.stdin.readline().strip().upper()
        if("P" in prompt):
            print("pausing")
            a.pause()
        elif("R" in prompt):
            print("resuming")
            a.resume()


print("Job done - exiting")
sys.exit(1)
