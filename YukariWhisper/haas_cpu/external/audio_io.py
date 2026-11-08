from math import gcd
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def read_audio(path):
    try:
        audio, sr = sf.read(path, dtype='float32', always_2d=True)
    except sf.SoundFileError as exc:
        raise ValueError(f'音声を読み込めません: {path}: {exc}') from exc
    if not audio.size or not np.isfinite(audio).all():
        raise ValueError('音声が空か、不正な数値が含まれています')
    audio = audio.mean(axis=1, dtype=np.float32)
    if sr != 16000:
        divisor = gcd(sr, 16000)
        audio = resample_poly(audio, 16000 // divisor, sr // divisor)
    return np.ascontiguousarray(audio, dtype=np.float32)
