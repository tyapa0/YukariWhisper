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

    def worker(self, adress, port):
        try:
            dispatcher = Dispatcher()
            dispatcher.map("/avatar/parameters/MuteSelf", self.print_volume_handler, "Volume")
            server = osc_server.ThreadingOSCUDPServer( (adress, port), dispatcher)
            server.serve_forever()
        except:
            print('VRC用のOSCポートが見つけられません vrc_osc_micmute=yにするか vrc_osc_portを確認してください')

    def start(self, adress, port):
        osc_thread = Thread(target=self.worker,args=(adress,port))
        osc_thread.daemon = True
        osc_thread.start()
