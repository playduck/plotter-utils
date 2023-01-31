#!/usr/bin/env python3

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
success = False

def availabeBuffer():
    # while 1:
    reminaingBuffer = 0

    ser.write(bytes("\033.B;", "utf-8"))
    # time.sleep(0.5)
    raw = ser.read_until("\r", 5)
    print("RAW", raw)

    # print("BUFFER", ser.out_waiting, ser.in_waiting)

    try:
        if raw:
            reminaingBuffer, _ = raw.decode("utf-8").split("\r")
        else:
            reminaingBuffer = -1
    except:
        reminaingBuffer = -2

    reminaingBuffer = int(reminaingBuffer)
    print("Buffer remaining", reminaingBuffer)
    return reminaingBuffer


class Job(threading.Thread):

    def __init__(self, port, file, delay, line, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.set()
        self.__running = threading.Event()
        self.__running.set()

        self.port = port
        self.file = file
        self.delay = delay
        self.line = line
        print(self.line)

    def run(self):
        global ser
        global success

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
        ser = serial.Serial(
            self.port,
            9600,
            timeout=1.0,
            inter_byte_timeout=self.delay
        )
        time.sleep(0.2)
        ser.write(bytes("\033.P3;", "utf-8")) # Handshake

        i = self.line
        print("START", i)
        print("LEN", len(line_list))
        while i < len(line_list):
            if("SP" in line_list[i]):
                print("----")
                print(f"Selecting new pen ({line_list[i]}). Waiting for user confirmation")
                print("Type \"r\" to continue")
                print("----")
                self.pause()
                time.sleep(0.4)

            if(self.__running.isSet()):
                self.__flag.wait()

            delay = (len(line_list[i]) * self.delay)
            # print(f"{i}\t {delay}\t {line_list[i]}")

            ser.write(bytes(line_list[i], "utf-8"))
            time.sleep(delay)

            i = i + 1;

            if(i % 10 == 0):
                buffer = availabeBuffer()
                # while buffer != 1024:
                #     print("Waiting on Buffer")
                #     time.sleep(1)
                #     buffer = availabeBuffer()

        # ser.close()
        self.stop()
        success = True

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
    global success
    try:
        if not success:
            ser.write(bytes("\033.J;", "utf-8"))
            ser.write(bytes("\033.K;", "utf-8"))
            ser.write(bytes("\033.Z;", "utf-8"))
            print("--- ABORTING ---")
        ser.close()
    except: pass
    print("END")
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
                    default=0.01
                    )
parser.add_argument('-l', '--line',
                    action='store',
                    dest='line',
                    help='Line Start',
                    type=int,
                    default=0
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

a = Job(args.get("port"), args.get("file"), args.get("delay"), args.get("line"))
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
        elif("B" in prompt):
            availabeBuffer()

print("Job done - exiting")
sys.exit(1)
