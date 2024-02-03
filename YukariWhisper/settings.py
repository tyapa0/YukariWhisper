import configparser
import unicodedata
import sys
import torch

class inifile_settings:

    inifile: configparser.ConfigParser
    yukari_connect_neo = False
    local_port = 5000
    automatic_recognition = False
    recognition_device = 0
    whisper_model_size = "large-v3"
    whisper_device = "cuda"
    compute_type = "int8_float16"
    using_recognizer = "whispr"
    debug_out_text = False
    gpu_device_index = 0

    pause_threshold = 0.8
    energy_threshold = 300
    energy_threshold_Low = 100
    dynamic_energy_threshold = True
    dynamic_energy_adjustment_damping = 0.15
    dynamic_energy_ratio = 1.5
    phrase_threshold = 0.3
    non_speaking_duration = 0.5
    vad_threshold = 0.1
    vrc_osc_micmute = False
    vrc_osc_adsress = "127.0.0.1"
    vrc_osc_port = 9001

    ng_words = ''

    #各セクションの解析
    def __init__(self, ini_filename, chr_code):
        self.inifile = configparser.ConfigParser()
        self.inifile.read(ini_filename, chr_code)

        self.parse_common()
        self.parse_recognizer()
        self.parse_ngwords(chr_code)

    #whisper compute_typeの設定
    #Compute_Capability:7以上 int8_float16(default), 6:float16, 5以下動作不能
    def set_whisper_device(self):
        Compute_Capability = int(torch.cuda.get_device_capability(self.gpu_device_index)[0])
        if(7 > Compute_Capability):
            compute_type = "float16"

    #COMMONセクションの解析
    def parse_common(self):
        ini_common = self.inifile['COMMON']
    
        if ini_common.get('text_type') == '1':
            self.yukari_connect_neo = True
        self.local_port = ini_common.get('local_port')

        #ゆかりねっとコネクターNEOから動的ポート番号を渡されたら反映
        if(len(sys.argv) > 1 and str.isnumeric(sys.argv[1])):
            self.local_port = sys.argv[1]

        if self.yukari_connect_neo:
            print(f"ゆかコネNEOを起動し、CommunicationPortのWebSocketの値を確認してください:[{self.local_port}]")
        else:
            print(f"ゆかりねっとを起動し、認識結果待ち受けポートを:[{self.local_port}]にしてください")
    
        if ini_common.get('automatic_recognition') != 'n':
            self.automatic_recognition = True
            self.recognition_device = ini_common.getint('automatic_recognition')

        self.whisper_model_size = ini_common.get('whisper_model_size')

        if ini_common.get('debug_out_text') != 'n':
            self.debug_out_text = True

        self.using_recognizer = ini_common.get('using_recognizer')

        if ini_common.get('vrc_osc_micmute') != 'n':
            self.vrc_osc_micmute = True

        self.vrc_osc_adsress = ini_common.get('vrc_osc_adsress')
        self.vrc_osc_port = ini_common.getint('vrc_osc_port')
        self.gpu_device_index = ini_common.getint('gpu_device_index')
        self.set_whisper_device()

    #RECOGNIZERセクションの解析
    def parse_recognizer(self):
        ini_recognizer = self.inifile['RECOGNIZER']
        self.pause_threshold = ini_recognizer.getfloat('pause_threshold')
        self.energy_threshold = ini_recognizer.getint('energy_threshold')
        if ini_recognizer.get('dynamic_energy_threshold') != 'y':
            self.dynamic_energy_threshold = False
        self.dynamic_energy_adjustment_damping = ini_recognizer.getfloat('dynamic_energy_adjustment_damping')
        self.dynamic_energy_ratio = ini_recognizer.getfloat('dynamic_energy_ratio')
        self.phrase_threshold = ini_recognizer.getfloat('phrase_threshold')
        self.non_speaking_duration = ini_recognizer.getfloat('non_speaking_duration')
        self.vad_threshold = ini_recognizer.getfloat('vad_threshold')
        self.energy_threshold_Low = ini_recognizer.getfloat('energy_threshold_Low')

    #NGWORDSセクションの解析
    def parse_ngwords(self, chr_code):
        ini_ngwords = self.inifile['NGWORDS']
        filename = ini_ngwords.get('ng_words_filename')
        with open('../'+filename, mode='r', encoding=chr_code) as f:
            self.ng_words = [unicodedata.normalize('NFC',word.strip()) for word in f if word != '\n']
        self.ng_words
