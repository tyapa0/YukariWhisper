#!/usr/bin/env python3

from device_list import get_devicxe_list
from gpu_list import get_gpu_list
import recognizer

if __name__ == "__main__":

    #GPUリストの表示
    get_gpu_list()

    #音声認識モジュールの初期化
    rec = recognizer.myrecognizer()

    # デバイス番号を取得
    if rec.is_automatic_recognition():
        device_index = rec.get_recognition_device()
    else:
        get_devicxe_list()
        device_index = int(input("\n使用するデバイスの番号を入力してください: "))

    # 文字認識開始
    rec.start(device_index)
