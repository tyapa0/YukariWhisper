"""Batch-one NeMo TDT label-looping rules, independent of graph execution."""
from collections.abc import Callable
import numpy as np
from .types import DecodingConfig


def tdt_greedy_decode(num_frames: int, joint_at: Callable, predict: Callable,
                      start: tuple, cfg: DecodingConfig) -> list[int]:
    pred, state = start
    t, last_ts, lasts = 0, -1, 0
    out = []
    while t < num_frames:
        while True:
            t_label = t
            logits = joint_at(t, pred)
            token = int(np.argmax(logits[:cfg.num_tokens + 1]))
            duration = cfg.durations[int(np.argmax(logits[cfg.num_tokens + 1:]))]
            if token == cfg.blank_id and duration == 0:
                duration = 1
            t += duration
            if token != cfg.blank_id or t >= num_frames:
                break
        if token == cfg.blank_id:
            break
        out.append(token)
        lasts = lasts + 1 if last_ts == t_label else 1
        last_ts = t_label
        pred, state = predict(token, state)
        if t < num_frames and lasts >= cfg.max_symbols and last_ts == t:
            t += 1
    return out
