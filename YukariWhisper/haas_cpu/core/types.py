from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class FrontendConfig:
    sample_rate: int
    n_fft: int
    win_length: int
    hop_length: int
    preemph: float
    log_zero_guard: float
    pad_to: int
    std_eps: float
    window: np.ndarray
    mel_filter: np.ndarray


@dataclass(frozen=True)
class DecodingConfig:
    blank_id: int
    durations: tuple[int, ...]
    max_symbols: int
    num_tokens: int


@dataclass(frozen=True)
class TokenTable:
    pieces: tuple[str, ...]
    unk_id: int
    add_dummy_prefix: bool


@dataclass
class Timings:
    features_s: float
    encoder_s: float
    decode_s: float
    total_s: float


@dataclass
class TranscriptionResult:
    text: str
    token_ids: list[int]
    audio_seconds: float
    timings: Timings
