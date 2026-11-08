"""Deterministic log-mel frontend from DESIGN_v2 §6."""
import numpy as np
from .types import FrontendConfig


class LogMelFrontend:
    def __init__(self, config: FrontendConfig):
        self.config = config
        c = config
        self.window = np.zeros(c.n_fft, dtype=np.float64)
        start = (c.n_fft - c.win_length) // 2
        self.window[start:start + c.win_length] = c.window
        self.fb = np.asarray(c.mel_filter, dtype=np.float32)

    def __call__(self, audio):
        c = self.config
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim != 1 or not np.isfinite(audio).all():
            raise ValueError('音声は有限の値を持つ1次元配列で指定してください')
        valid = len(audio) // c.hop_length
        if valid < 2:
            raise ValueError('音声が短すぎます（20 ms 未満）')
        x = np.concatenate((audio[:1], audio[1:] - np.float32(c.preemph) * audio[:-1]))
        xp = np.pad(x, (c.n_fft // 2,) * 2)
        frames = np.lib.stride_tricks.sliding_window_view(xp, c.n_fft)[::c.hop_length]
        spectrum = np.fft.rfft(frames.astype(np.float64) * self.window, n=c.n_fft)
        power = (np.sqrt(spectrum.real**2 + spectrum.imag**2)**2).astype(np.float32)
        mel = np.log(self.fb @ power.T + np.float32(c.log_zero_guard))
        mean = mel[:, :valid].mean(1, keepdims=True)
        std = np.sqrt(np.sum((mel[:, :valid] - mean)**2, axis=1, keepdims=True) / (valid - 1))
        mel = (mel - mean) / (std + np.float32(c.std_eps))
        mel[:, valid:] = 0
        mel = np.pad(mel, ((0, 0), (0, (-mel.shape[1]) % c.pad_to)))
        return np.ascontiguousarray(mel[None], dtype=np.float32), np.array([valid], dtype=np.int64)
