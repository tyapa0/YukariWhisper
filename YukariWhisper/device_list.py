import pyaudio

# 有効なマイクデバイのリストを表示
def get_devicxe_list():
    devices = []
    audio = pyaudio.PyAudio()
    device_count = audio.get_device_count()
    host_api_info = audio.get_default_host_api_info()
    host_api_index = host_api_info["index"]

    for i in range(device_count):
        device_info = audio.get_device_info_by_index(i)
        if (
            device_info["maxInputChannels"] > 0
            and device_info["hostApi"] == host_api_index
        ):
            devices.append(device_info)

    for device_info in devices:
        print(
            f"{device_info['index']} : {device_info['name']}, チャンネル数: {device_info['maxInputChannels']}"
        )
