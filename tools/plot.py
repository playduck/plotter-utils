import sys
import select
import serial
import time
import keyboard
import argparse
import threading
import datetime

VERSION = "v1.0.0"

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
        print("opening file", self.file)
        line_list = list()
        with open(self.file,"r") as f:
            line_list = [l.strip() for l in list(f.readlines())]

        print("opening serial port", self.port)
        ser = serial.Serial(self.port, 9600, timeout=0.5)

        i = 0;
        while(i < len(line_list)):
            ser.write(bytes(line_list[i], "utf-8"))

            if(i % 50 == 0):
                time_remaining = int(round(((len(line_list) - i) * self.delay), 0))
                tm = datetime.datetime.fromtimestamp(time_remaining)
                progress = round(i / len(line_list) * 100, 2)
                print(f"{i}/{len(line_list)} {tm.strftime('%M:%S')} {progress}%")

            i = i + 1;
            time.sleep(self.delay)
            if(self.__running.isSet()):
                self.__flag.wait()

        ser.close()
        self.stop()

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        self.__running.clear()

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
                    default=0.2
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

time.sleep(0.2)

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
