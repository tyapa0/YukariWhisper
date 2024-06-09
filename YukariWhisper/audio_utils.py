import sounddevice as sd

class AudioDeviceWrapper:
    def __init__(self):
        self.devices = sd.query_devices()
        self.hostapis = sd.query_hostapis()

    # Show list of enabled microphone devices
    def get_device_list(self):
        for device_info in self.devices:
            if device_info["max_input_channels"] > 0:
                device_info["host_api_name"] = self.hostapis[device_info["hostapi"]]["name"]
                if device_info["host_api_name"] == 'MME':
                    print(
                        f"{str(device_info['index']).rjust(3, ' ')} : {str(device_info['name']).ljust(30, ' ')}, チャンネル数: {device_info['max_input_channels']}"
                    )

    # create an audio stream
    def create_audio_stream(self, device_index, callback, chunk):

        sd.default.device = device_index
        RATE = 16000
        CHUNK = 1600
        CHANNELS = 1
        DTYPE = "float32"

        stream = sd.InputStream(
            #device=selected_device,
            channels=CHANNELS,
            samplerate=RATE,
            callback=callback,
            dtype=DTYPE,
            blocksize=CHUNK,
        )

        return stream