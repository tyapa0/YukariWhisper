import configparser
import unicodedata


class inifile_settings:

    inifile: configparser.ConfigParser
    yukari_connect_neo = False
    local_port = 5000
    automatic_recognition = False
    recognition_device = 0
    whisper_model_size = "large-v3"
    whisper_device = "cuda"
    compute_type = "int8_bfloat16"
    using_recognizer = "whispr"
    debug_out_text = False

    pause_threshold = 0.8
    energy_threshold = 300
    dynamic_energy_threshold = True
    dynamic_energy_adjustment_damping = 0.15
    dynamic_energy_ratio = 1.5
    phrase_threshold = 0.3
    non_speaking_duration = 0.5
    vad_threshold = 0.1
    vrc_osc_micmute = False

    ng_words = ''

    #各セクションの解析
    def __init__(self, ini_filename, chr_code):
        self.inifile = configparser.ConfigParser()
        self.inifile.read(ini_filename, chr_code)

        self.parse_common()
        self.parse_recognizer()
        self.parse_ngwords(chr_code)

    #COMMONセクションの解析
    def parse_common(self):
        ini_common = self.inifile['COMMON']
    
        if ini_common.get('text_type') == '1':
            self.yukari_connect_neo = True
        self.local_port = ini_common.get('local_port')

        if self.yukari_connect_neo:
            print(f"ゆかコネNEOを起動しCommunicationPortのWebSocketの値を確認してください:[{self.local_port}]")
        else:
            print(f"ゆかりねっとを起動し認識結果待ち受けポートを:[{self.local_port}]にしてください")
    
        if ini_common.get('automatic_recognition') != 'n':
            self.automatic_recognition = True
            self.recognition_device = ini_common.getint('automatic_recognition')

        self.whisper_model_size = ini_common.get('whisper_model_size')

        if ini_common.get('debug_out_text') != 'n':
            self.debug_out_text = True

        w_device = ini_common.get('whisper_device')
        if w_device == 'cpu_8':
            self.whisper_device = 'cpu'
            self.compute_type = 'int8'
        elif w_device == 'cpu_32':
            self.whisper_device = 'cpu'
            self.compute_type = 'float32'
        elif w_device == 'cuda_16':
            self.compute_type = 'float16'
        elif w_device == 'cuda_8_1':
            self.compute_type = 'int8_float16'

        self.using_recognizer = ini_common.get('using_recognizer')

        if ini_common.get('vrc_osc_micmute') != 'n':
            self.vrc_osc_micmute = True

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

    #NGWORDSセクションの解析
    def parse_ngwords(self, chr_code):
        ini_ngwords = self.inifile['NGWORDS']
        filename = ini_ngwords.get('ng_words_filename')
        with open('../'+filename, mode='r', encoding=chr_code) as f:
            self.ng_words = [unicodedata.normalize('NFC',word.strip()) for word in f if word != '\n']
        self.ng_words
