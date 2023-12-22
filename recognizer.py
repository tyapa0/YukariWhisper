#!/usr/bin/env python3

from threading import Thread
from queue import Queue
from whisper_utils import WhisperModelWrapper

import speech_recognition as sr
import numpy as np
import time
import settings
import wsocket
import vad
import oscserver

#音声認識エンジン本体
class myrecognizer:
    model_wrapper: WhisperModelWrapper
    recognizers: sr.Recognizer
    audio_queue: Queue
    ini_file: settings
    ws: wsocket

    def __init__(self):
        # 設定ファイルをロード
        self.ini_file      = settings.inifile_settings('yukariwhisper.ini', 'UTF-8')
        self.recognizers   = sr.Recognizer()
        self.audio_queue   = Queue()

        # faster-Whisperのモデルロード
        if self.ini_file.using_recognizer != 'google':
            self.model_wrapper =  WhisperModelWrapper(
                                self.ini_file.whisper_model_size,
                                self.ini_file.whisper_device,
                                self.ini_file.compute_type
                                )

        #音声認識器のパラメータ設定
        self.recognizers.energy_threshold = self.ini_file.energy_threshold
        self.recognizers.dynamic_energy_threshold = self.ini_file.dynamic_energy_threshold
        self.recognizers.dynamic_energy_adjustment_damping = self.ini_file.dynamic_energy_adjustment_damping
        self.recognizers.dynamic_energy_ratio = self.ini_file.dynamic_energy_ratio
        self.recognizers.pause_threshold  = self.ini_file.pause_threshold
        self.recognizers.phrase_threshold  = self.ini_file.phrase_threshold
        self.recognizers.non_speaking_duration  = self.ini_file.non_speaking_duration

        # websocket通信の設定
        self.wsocket = wsocket.wsocket('ws://localhost:', self.ini_file.local_port, self.ini_file.yukari_connect_neo)
        # ノイズフィルタの設定
        self.vad     = vad.Vad(self.ini_file.vad_threshold)
        # voiceキーの取得用 OSC server
        self.osc     = oscserver.oscserver()
        
    def is_automatic_recognition(self):
        return self.ini_file.automatic_recognition

    def get_recognition_device(self):
        return self.ini_file.recognition_device

    #ミュート制御
    def mute_control(self, mystream):
        if self.osc.Mute and self.ini_file.vrc_osc_micmute:
            if mystream.is_stopped() == False:
                mystream.stop_stream()
                #print("stop_stream")
            while self.osc.Mute:
                time.sleep(0.001)
            if mystream.is_stopped() == True:
                mystream.start_stream()  
                #print("start_stream")

    #音声認識実行スレッド
    def recognize_worker(self):
        # this runs in a background thread
        while True:
            audio = self.audio_queue.get()  # retrieve the next audio processing job from the main thread
            if audio is None: break  # stop processing if the main thread is done

            # received audio data, now we'll recognize it using Google Speech Recognition
            try:
                #print(f"sample_rate: {audio.sample_rate}")
                #print(f"sample_width: {audio.sample_width}")

                #音声を文字列に変換する
                if self.ini_file.using_recognizer == 'google':
                    start_t2 = time.time() 
                    #googleで認識
                    strGoogleData = self.recognizers.recognize_google(audio, language='ja-JP')
                    if self.ini_file.debug_out_text:
                        print(f"google [{time.time()-start_t2}]" + strGoogleData)
                    # send text to websocket 
                    self.wsocket.send(strGoogleData)

                else:
                    start_t = time.time() 
                    #audioデーターのフォーマットをwhisper用の16k 16bitに変換する
                    frame_bytes = audio.get_raw_data(convert_rate=16000)
                    speech_array = np.frombuffer(frame_bytes, dtype=np.int16)
                    if self.vad.is_speech(speech_array):
                        #whisperで認識
                        segments = self.model_wrapper.transcribe(speech_array)
                        for segment in segments:
                            if segment.text in self.ini_file.ng_words:
                                continue
                            if self.ini_file.debug_out_text:
                                print(f"whisper[{time.time()-start_t}]" + segment.text)

                            # send text to websocket 
                            self.wsocket.send(segment.text)

            except sr.UnknownValueError:
                #print("Google Speech Recognition could not understand audio")
                pass
            except sr.RequestError as e:
                #print("Could not request results from Google Speech Recognition service; {0}".format(e))
                pass

            self.audio_queue.task_done()  # mark the audio processing job as completed in the queue

    #実行関数
    def start(self, index):
        # start a new thread to recognize audio, while this thread focuses on listening
        recognize_thread = Thread(target=self.recognize_worker)
        recognize_thread.daemon = True
        recognize_thread.start()
        print("音声認識開始:")

        # String transfer communication with YukariNet
        self.wsocket.open()

        #M ic mute sync with VRC
        phrase_time_limit = None
        if self.ini_file.vrc_osc_micmute:
            self.osc.start()
            phrase_time_limit = 1

        # speech_recognition start
        with sr.Microphone(index) as source:
            try:
                while True:  # repeatedly listen for phrases and put the resulting audio on the audio processing job queue
                    try:
                        self.audio_queue.put(self.recognizers.listen(source, phrase_time_limit))
                    except sr.WaitTimeoutError:
                        pass
                    self.mute_control(source.stream.pyaudio_stream)

            except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
                pass

        self.audio_queue.join()  # block until all current audio processing jobs are done
        self.audio_queue.put(None)  # tell the recognize_thread to stop
        recognize_thread.join()  # wait for the recognize_thread to actually stop
