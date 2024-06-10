#!/usr/bin/env python3

from threading import Thread
from queue import Queue
from whisper_utils import WhisperModelWrapper
from audio_utils import AudioDeviceWrapper
import matplotlib as matp
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

import speech_recognition as sr
import numpy as np
import time
import settings
import wsocket
import vad
import oscserver
import unicodedata

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
SAMPLE_RATE = 16000

#音声認識エンジン本体
class myrecognizer:
    model_wrapper: WhisperModelWrapper
    recognizers: sr.Recognizer
    audio_queue: Queue
    ini_file: settings
    ws: wsocket
    audio_data_list :list
    downsample :int
    silence_counter :int
    speach_counter :int
    audio_device: AudioDeviceWrapper
    recognition_timeout :int
    line : matp.lines.Line2D
    plotdata : np.ndarray

    def __init__(self):
        # 設定ファイルをロード
        print("初期化中...")
        self.ini_file      = settings.inifile_settings('../yukariwhisper.ini', 'UTF-8')
        self.recognizers   = sr.Recognizer()
        self.alive = True
        self.audio_data_list = []
        self.silence_counter = 0
        self.speach_counter = 0
        self.audio_queue   = Queue()

        self.downsample = 10
        self.sample_rate = SAMPLE_RATE

        # faster-Whisperのモデルロード
        if self.ini_file.using_recognizer != 'google':
            self.model_wrapper =  WhisperModelWrapper(
                                self.ini_file.whisper_model_size,
                                self.ini_file.whisper_device,
                                self.ini_file.compute_type,
                                self.ini_file.gpu_device_index,
                                self.ini_file.beam_size,
                                self.ini_file.vad_enable2,
                                self.ini_file.vad_threshold2
                                )

        #マイク入力
        self.audio_device = AudioDeviceWrapper()
        self.recognition_timeout = self.ini_file.recognition_timeout

        # websocket通信の設定
        self.wsocket = wsocket.wsocket('ws://localhost:', self.ini_file.local_port, self.ini_file.yukari_connect_neo)
        # ノイズフィルタの設定
        self.vad     = vad.Vad(self.ini_file.vad_threshold)
        # voiceキーの取得用 OSC server
        self.osc     = oscserver.oscserver()

    #マイク入力の列挙
    def get_devicxe_list(self):
        self.audio_device.get_device_list()

    #32msec by 512chunk
    def audio_callback(self, indata, frames, time, status):
        is_speech = self.vad.is_speech(indata)
        #Mute
        if self.osc.Mute and self.ini_file.vrc_osc_micmute:
            is_speech = False

        if is_speech:
            self.speach_counter += 1
            self.silence_counter = 0
            self.audio_data_list.append(indata.flatten())
            self.line.set_color("m")
        else:
            self.silence_counter += 1
            self.audio_data_list.append(indata.flatten())
            self.line.set_color("gray")

            #0.5secの無音を検知してキューに入れる
            #250=25sec whisperの最大許容秒数
            if self.silence_counter > self.ini_file.pause_threshold or len(self.audio_data_list) > 250:
                #1sec以上話したデータが無いと採用しないようにする
                if self.speach_counter > self.ini_file.phrase_threshold :
                    concatenate_audio_data = np.concatenate(self.audio_data_list)
                    self.audio_queue.put(concatenate_audio_data)
                    self.speach_counter = 0
                    #print("debug:audio_queue.put")

                self.audio_data_list.clear()
                self.silence_counter = 0

        # indata.shape=(n_samples, n_channels)
        data = indata[::self.downsample, 0]
        shift = len(data)
        self.plotdata = np.roll(self.plotdata, -shift, axis=0)
        self.plotdata[-shift:] = data

    def update_plot(self, frame):
        """This is called by matplotlib for each plot update.
        """
        self.line.set_ydata(self.plotdata)
        return self.line,

    def is_automatic_recognition(self):
        return self.ini_file.automatic_recognition
    def get_recognition_device(self):
        return self.ini_file.recognition_device

    # ng_wordsが含まれているか判定
    def check_ng_words(self, text):
        for check_in_text in self.ini_file.ng_words:
            if check_in_text in text:
                #print("NGW:" + text)
                return True
        return False

    #音声認識実行スレッド
    def recognize_worker(self):
        # this runs in a background thread
        while self.alive:
            audio_data = self.audio_queue.get()  # retrieve the next audio processing job from the main thread
            if audio_data is None: break  # stop processing if the main thread is done

            # received audio data, now we'll recognize it using Google Speech Recognition
            try:
                #print(f"sample_rate: {audio.sample_rate}")
                #print(f"sample_width: {audio.sample_width}")

                #音声を文字列に変換する
                if self.ini_file.using_recognizer == 'google':
                    start_t2 = time.time() 
                    #googleで認識
                    audio_bytes = (audio_data * 32767).astype(np.int16).tobytes() # Convert numpy array to bytes
                    audio = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)
                    strGoogleData = self.recognizers.recognize_google(audio, language='ja-JP')
                    if self.ini_file.debug_out_text:
                        print(f"google [{(time.time()-start_t2):.4f}]({len(segment.text)})" + strGoogleData)
                    # send text to websocket 
                    self.wsocket.send(strGoogleData)

                else:
                    start_t = time.time() 
                    #whisperで認識
                    segments = self.model_wrapper.transcribe(audio_data)
                    for segment in segments:
                        # 時間が指定秒以上かかる場合は結果を破棄して次の音声認識結果に移行する
                        if round((time.time()-start_t), 1) >= self.recognition_timeout:
                            print("音声認識がタイムアウトしました。")
                            continue
                        # uniocode Normalization
                        normalized_text = unicodedata.normalize('NFC', segment.text)
                        if self.check_ng_words(normalized_text):
                            continue
                        if self.ini_file.debug_out_text:
                            print(f"whisper[{(time.time()-start_t):.4f}]({len(segment.text)})" + normalized_text)
                         # send text to websocket 
                        self.wsocket.send(normalized_text)

            except sr.UnknownValueError:
                #print("Google Speech Recognition could not understand audio")
                pass
            except sr.RequestError as e:
                #print("Could not request results from Google Speech Recognition service; {0}".format(e))
                pass
            except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
                break

    #実行関数
    def start(self, index):

        #マイク入力の初期化
        stream = self.audio_device.create_audio_stream(index, self.audio_callback, SAMPLE_RATE*0.1)
    
        #plots_set 
        length = int(1000 * self.sample_rate / (1000 * self.downsample))
        self.plotdata = np.zeros((length))
        fig, ax = plt.subplots()
        self.line, = ax.plot(self.plotdata)
        ax.set_ylim([-1.0, 1.0])
        ax.set_xlim([0, length])
        ax.yaxis.grid(True)
        fig.tight_layout()
    
        # start a new thread to recognize audio, while this thread focuses on listening
        recognize_thread = Thread(target=self.recognize_worker)
        recognize_thread.daemon = True
        recognize_thread.start()
        print("音声認識開始:")

        # String transfer communication with YukariNet
        self.wsocket.open()

        #Mic mute sync with VRC
        phrase_time_limit = None
        if self.ini_file.vrc_osc_micmute:
            self.osc.start(self.ini_file.vrc_osc_adsress, self.ini_file.vrc_osc_port)
            phrase_time_limit = 1

        # speech_recognition start
        #print("debug:recognize_start")
        ani = FuncAnimation(fig, self.update_plot, interval=30, blit=True, cache_frame_data=False)
        with stream:
            try:
                if self.ini_file.plot_data:
                    plt.show()
                else:
                    recognize_thread.join()
            except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
                pass

        #print("debug:recognize_end")

        self.audio_queue.join()  # block until all current audio processing jobs are done
        self.audio_queue.put(None)  # tell the recognize_thread to stop
        self.alive = False # thread end
        recognize_thread.join()  # wait for the recognize_thread to actually stop
