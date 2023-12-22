from threading import Thread
import websocket

#String transfer communication with YukariNet
class wsocket:
    def __init__(self, host, port, connect_neo):
        websocket.enableTrace(False)
        self.hostname = host + port + '/'
        self.ws = websocket.WebSocketApp(self.hostname)
        self.yukari_connect_neo = connect_neo
       
    def websocket_worker(self):
        self.ws.run_forever()

    def open(self):
        ws_thread = Thread(target=self.websocket_worker)
        ws_thread.daemon = True
        ws_thread.start()

    def send(self, text):
        if self.yukari_connect_neo == False:
            text = '0:' + text
        self.ws.send(text)
