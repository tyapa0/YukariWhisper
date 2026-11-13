#!/usr/bin/env python3

from threading import Thread
from queue import Queue
from whisper_utils import WhisperModelWrapper
from haas_utils import HaasModelWrapper, is_haas_model_name
from google_utils import GoogleSpeechRecognizer, GoogleUnknownValueError, GoogleRequestError
from audio_utils import AudioDeviceWrapper

import numpy as np
import time
import settings
import wsocket
import vad
import oscserver
import unicodedata

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import onnxruntime
if hasattr(onnxruntime, "disable_telemetry_events"):
    onnxruntime.disable_telemetry_events()
SAMPLE_RATE = 16000

#音声認識エンジン本体
#波形ウインドウの描画は plotlib.WaveformPlot 
#認識エンジンは3種とも _transcribe_to_texts() の中で文字列の列に揃える:
#   google (using_recognizer) -> GoogleSpeechRecognizer (google_utils.py)
#   Haas-ja-v1.0 系の名前     -> HaasModelWrapper (ONNX, haas_utils.py)
#   それ以外                  -> WhisperModelWrapper (faster-whisper/CTranslate2)

class myrecognizer:
    audio_queue: Queue
    ini_file: settings
    ws: wsocket
    audio_data_list :list
    downsample :int
    silence_counter :int
    speach_counter :int
    audio_device: AudioDeviceWrapper
    recognition_timeout :int
    plot: "WaveformPlot"

    def __init__(self):
        # 設定ファイルをロード
        print("初期化中...")
        self.ini_file      = settings.inifile_settings('../yukariwhisper.ini', 'UTF-8')
        self.alive = True
        self.audio_data_list = []
        self.silence_counter = 0
        self.speach_counter = 0
        self.audio_queue   = Queue()
        self.ampfilter = 1.0

        # 波形表示用ダウンサンプル (表示専用)
        # 20 = 1px あたり約 1 点
        self.downsample = 20
        self.sample_rate = SAMPLE_RATE
        self.plot = None

        # 音声認識モデルのロード (google選択時はモデルを使わない)
        self.engine_name = 'whisper'
        self.model_wrapper = None
        self.google_recognizer = None
        if self.ini_file.using_recognizer == 'google':
            self.engine_name = 'google'
            self.google_recognizer = GoogleSpeechRecognizer(language='ja-JP')
        elif is_haas_model_name(self.ini_file.whisper_model_size):
            self.engine_name = 'haas'
            self.model_wrapper = HaasModelWrapper(
                                self.ini_file.whisper_model_size,
                                self.ini_file.haas_format,
                                self.ini_file.haas_threads,
                                self.ini_file.haas_repo
                                )
        else:
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
        #amp
        if self.ampfilter > 1.0:
            indata = indata * self.ampfilter

        is_speech = self.vad.is_speech(indata)

        #Mute
        if self.osc.Mute and self.ini_file.vrc_osc_micmute:
            is_speech = False

        if is_speech:
            self.speach_counter += 1
            self.silence_counter = 0
            self.audio_data_list.append(indata.flatten())
        else:
            self.silence_counter += 1
            self.audio_data_list.append(indata.flatten())

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

        # 波形表示は plotlib 側で行う
        if self.plot is not None:
            self.plot.set_speech(is_speech)
            self.plot.push(indata)

    def slider_amp_update(self, slider_val):
        self.ampfilter = slider_val

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

    # 1発話分の音声を文字列の列に変換する。
    #   google        -> GoogleSpeechRecognizer.transcribe() (文字列を1つ返す)
    #   whisper / haas-> model_wrapper.transcribe() (.text の列を返す)
    def _transcribe_to_texts(self, audio_data):
        if self.engine_name == 'google':
            return [self.google_recognizer.transcribe(audio_data, SAMPLE_RATE)]
        return [segment.text for segment in self.model_wrapper.transcribe(audio_data)]

    # 認識結果1件分の後処理 (タイムアウト判定・正規化・NGワード・デバッグ出力・送信)
    def _dispatch_text(self, text, start_t):
        # 時間が指定秒以上かかる場合は結果を破棄して次の音声認識結果に移行する
        if round((time.time()-start_t), 1) >= self.recognition_timeout:
            print("音声認識がタイムアウトしました。")
            return
        # unicode Normalization
        normalized_text = unicodedata.normalize('NFC', text)
        if self.check_ng_words(normalized_text):
            return
        if self.ini_file.debug_out_text:
            print(f"{self.engine_name}[{(time.time()-start_t):.4f}]({len(text)})" + normalized_text)
        # send text to websocket
        self.wsocket.send(normalized_text)

    #音声認識実行スレッド
    def recognize_worker(self):
        # this runs in a background thread
        while True:
            audio_data = self.audio_queue.get()  # retrieve the next audio processing job from the main thread
            try:
                # stop processing if the main thread is done
                # (終了時はキューに残った音声を処理せず、そのまま捨てる)
                if audio_data is None or not self.alive:
                    break

                try:
                    start_t = time.time()
                    for text in self._transcribe_to_texts(audio_data):
                        self._dispatch_text(text, start_t)

                except GoogleUnknownValueError:
                    # googleで聞き取れなかった場合 (旧 speech_recognition.UnknownValueError)
                    pass
                except GoogleRequestError:
                    # googleへ接続できなかった場合 (旧 speech_recognition.RequestError)
                    pass
            finally:
                self.audio_queue.task_done()

    #実行関数
    def start(self, index):

        #波形ウインドウの用意 (描画まわりは plotlib)
        #コールバックが来る前に用意しておくため、マイク入力より先
        if self.ini_file.plot_data:
            from plotlib import WaveformPlot
            self.plot = WaveformPlot(self.sample_rate, self.downsample, self.slider_amp_update)

        #マイク入力の初期化
        stream = self.audio_device.create_audio_stream(index, self.audio_callback, SAMPLE_RATE*0.1)

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

        # ウインドウ表示
        #print("debug:recognize_start")
        if self.plot is not None:
            self.plot.start_animation()
        with stream:
                if self.plot is not None:
                    self.plot.show()
                else:
                    recognize_thread.join()

        #print("debug:recognize_end")

        # 終了処理: 認識スレッドを止める。キューに残った音声は処理せず破棄する
        self.alive = False # thread end
        self.audio_queue.put(None)  # tell the recognize_thread to stop
        recognize_thread.join()  # wait for the recognize_thread to actually stop
