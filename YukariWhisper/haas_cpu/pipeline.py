import time
import numpy as np
from .core.features import LogMelFrontend
from .core.tdt import tdt_greedy_decode
from .core.detokenize import Detokenizer
from .core.chunking import split_at_quiet_points
from .core.types import Timings, TranscriptionResult
from .external.bundle import Bundle
from .external.onnx_graphs import EncoderGraph, PredictionGraph, JointGraph


class Transcriber:
    def __init__(self, models_dir=None, fmt: str = 'int4-onecomp', threads: int = 4, encoder_path=None):
        # YukariWhisper modification: pass fmt so that a snapshot holding
        # only the selected encoder format can be opened (see bundle.py).
        bundle = Bundle.open(models_dir, fmt=fmt)
        self.frontend = LogMelFrontend(bundle.frontend)
        self.detokenizer = Detokenizer(bundle.tokens)
        self.cfg = bundle.decoding
        self.encoder = EncoderGraph(encoder_path or bundle.encoder(fmt), threads)
        self.prediction = PredictionGraph(bundle.common('prediction'))
        self.joint = JointGraph(bundle.common('joint'))
        self.start = self.prediction.step(self.cfg.blank_id, self.prediction.empty_state())
        for array in (self.start[0], *self.start[1]):
            array.setflags(write=False)

    def transcribe(self, audio: np.ndarray) -> TranscriptionResult:
        started = time.perf_counter()
        mel, length = self.frontend(audio)
        features_end = time.perf_counter()
        encoded, frames = self.encoder.run(mel, length)
        encoder_end = time.perf_counter()
        ids = tdt_greedy_decode(frames, lambda t, pred: self.joint.logits(encoded[t:t + 1], pred),
                                self.prediction.step, self.start, self.cfg)
        text = self.detokenizer.decode(ids).strip()
        ended = time.perf_counter()
        return TranscriptionResult(text, ids, len(audio) / 16000,
                                   Timings(features_end - started, encoder_end - features_end,
                                           ended - encoder_end, ended - started))

    def transcribe_long(self, audio: np.ndarray) -> TranscriptionResult:
        started = time.perf_counter()
        bounds = split_at_quiet_points(audio, chunk_seconds=28., search_seconds=2., window_seconds=.1)
        results = [self.transcribe(audio[start:end]) for start, end in bounds]
        times = Timings(*(sum(getattr(r.timings, field) for r in results)
                          for field in ('features_s', 'encoder_s', 'decode_s')), time.perf_counter() - started)
        return TranscriptionResult(''.join(r.text for r in results),
                                   [token for r in results for token in r.token_ids], len(audio) / 16000, times)
