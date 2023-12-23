from threading import Thread
import argparse
#import math

import pyaudio
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

#OSC入力でマイクのミュート状態を取得する
class oscserver:
    def __init__(self):
        self.Mute = False

    def print_volume_handler(self, unused_addr, args, Mute):
        self.Mute = Mute

    def worker(self):
        dispatcher = Dispatcher()
        dispatcher.map("/avatar/parameters/MuteSelf", self.print_volume_handler, "Volume")
        server = osc_server.ThreadingOSCUDPServer( ("127.0.0.1", 9001), dispatcher)
        server.serve_forever()

    def start(self):
        osc_thread = Thread(target=self.worker)
        osc_thread.daemon = True
        osc_thread.start()
