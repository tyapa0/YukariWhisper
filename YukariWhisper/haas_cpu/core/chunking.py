"""Quiet-point splitting, copied from haas_asr.longform (§10.3).

Only the default chunk duration changes from 30 to 28 seconds.
"""
import numpy as np


def split_at_quiet_points(
    audio: np.ndarray,
    *,
    sample_rate: int = 16000,
    chunk_seconds: float = 28.0,
    search_seconds: float = 2.0,
    window_seconds: float = 0.1,
) -> list[tuple[int, int]]:
    step = int(chunk_seconds * sample_rate)
    search = int(search_seconds * sample_rate)
    window = int(window_seconds * sample_rate)
    bounds = []
    start = 0
    while audio.size - start > step:
        target = start + step
        low = max(start + step // 2, target - search)
        high = min(audio.size - window, target + search)
        cut = target
        if high > low:
            cut = low + _quietest_window(audio[low:high + window], window) + window // 2
        bounds.append((start, cut))
        start = cut
    if start < audio.size:
        bounds.append((start, audio.size))
    return bounds


def _quietest_window(audio: np.ndarray, window: int) -> int:
    energy = np.cumsum(np.concatenate([[0.0], audio.astype(np.float64) ** 2]))
    return int(np.argmin(energy[window:] - energy[:-window]))
