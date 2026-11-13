#!/usr/bin/env python3
import os
from dataclasses import dataclass

import numpy as np

# ONNX conversion of Haas-ja-v1.0 (weights + manifest are downloaded from here)
HAAS_ONNX_REPO_ID = "kizuna-intelligence/Haas-ja-v1.0-OneCompression-ONNX"
# Encoder formats published in that repository
HAAS_FORMATS = ("int8", "int4-onecomp", "fp32")
DEFAULT_HAAS_FORMAT = "int8"  # fastest in the model card's benchmark
DEFAULT_HAAS_THREADS = 4

_HAAS_MODEL_NAMES = {
    "haas-ja-v1.0",
    "third-intelligence/haas-ja-v1.0",
    "kizuna-intelligence/haas-ja-v1.0-onecompression-onnx",
}


def normalize_haas_format(fmt):
    """Return a valid encoder format name, or the default with a warning."""
    if fmt is None:
        return DEFAULT_HAAS_FORMAT
    fmt = str(fmt).strip().lower()
    if fmt in HAAS_FORMATS:
        return fmt
    print(f"haas_format={fmt!r} は未対応のため {DEFAULT_HAAS_FORMAT} を使用します。"
          f"対応形式: {', '.join(HAAS_FORMATS)}")
    return DEFAULT_HAAS_FORMAT


def is_haas_model_name(model_size_or_path):
    """True when ``whisper_model_size`` asks for Haas-ja-v1.0.

    Accepts the repository ids and the ``Haas-ja-v1.0.nemo`` spelling, and
    also a local path whose folder name is one of those (e.g. a manually
    downloaded snapshot folder).
    """
    if not model_size_or_path:
        return False
    name = str(model_size_or_path).strip().replace("\\", "/").rstrip("/").lower()
    if name.endswith(".nemo"):
        name = name[: -len(".nemo")]
    if name in _HAAS_MODEL_NAMES:
        return True
    # local path: ".../Haas-ja-v1.0" or ".../Haas-ja-v1.0-OneCompression-ONNX"
    base = name.rsplit("/", 1)[-1]
    return base in {"haas-ja-v1.0", "haas-ja-v1.0-onecompression-onnx"}


def download_haas_model(fmt=DEFAULT_HAAS_FORMAT, repo_id=HAAS_ONNX_REPO_ID):
    """Download only the files needed for ``fmt`` and return the local path.

    Uses the Hugging Face cache, so the second and later starts work
    offline, the same as the faster-whisper models did.
    """
    # Xet storage transfers fail behind some proxies / firewalls
    # (ProxyError on the xet-read-token endpoint).  Plain HTTPS always
    # works, so prefer it unless the user configured Xet themselves.
    # Must be set before huggingface_hub is imported, hence the lazy import.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import snapshot_download

    fmt = normalize_haas_format(fmt)
    print(f"Haas-ja-v1.0 (ONNX/{fmt}) を取得します: {repo_id}")
    print("初回のみダウンロードが始まります。終わるまでお待ちください...")
    local_dir = snapshot_download(
        repo_id=repo_id,
        allow_patterns=[
            "manifest.json",
            "common/*",
            f"{fmt}/*",
            "LICENSE",
            "NOTICE",
        ],
    )
    print(f"Haas-ja-v1.0 の保存先: {local_dir}")
    return local_dir


@dataclass
class HaasSegment:
    """faster-whisper の Segment と同じ `.text` だけを持つ最小の結果型。

    recognizer.py は ``segment.text`` しか使わないため、これで差し替え可能。
    """

    text: str


class HaasModelWrapper:
    """Drop-in replacement for WhisperModelWrapper (same transcribe() shape).

    Input:  16 kHz mono float32 numpy array (the same array the
            faster-whisper wrapper receives from the microphone callback).
    Output: a list with at most one HaasSegment.
    """

    def __init__(self, model_size_or_path, fmt=DEFAULT_HAAS_FORMAT,
                 threads=DEFAULT_HAAS_THREADS, repo_id=HAAS_ONNX_REPO_ID):
        self.fmt = normalize_haas_format(fmt)
        try:
            self.threads = max(1, int(threads))
        except (TypeError, ValueError):
            self.threads = DEFAULT_HAAS_THREADS

        if model_size_or_path and os.path.isdir(str(model_size_or_path)):
            # local snapshot folder given in whisper_model_size
            models_dir = str(model_size_or_path)
            print(f"Haas-ja-v1.0 (ONNX/{self.fmt}) をローカルから読み込みます: {models_dir}")
        else:
            models_dir = download_haas_model(self.fmt, repo_id or HAAS_ONNX_REPO_ID)

        # Vendored inference code from the ONNX repository (Apache-2.0).
        # Imported here so that the faster-whisper / google paths never pay
        # for importing it, and so a missing model only breaks this backend.
        from haas_cpu.pipeline import Transcriber

        self._transcriber = Transcriber(models_dir, fmt=self.fmt, threads=self.threads)
        print(f"Haas-ja-v1.0 (ONNX/{self.fmt}, CPU {self.threads} threads) の読み込みが完了しました")

    def transcribe(self, audio):
        audio = np.asarray(audio, dtype=np.float32).flatten()
        # LogMelFrontend needs at least 20 ms of audio.
        if audio.size < 320:
            return []
        # Digital silence can be hallucinated into short utterances: the
        # frontend normalizes per feature, so an all-zero input is blown up
        # to full scale.  YukariWhisper's VAD normally keeps silence out,
        # but drop it here too.  -80 dBFS is far below any real microphone
        # noise floor, so actual (even very quiet) speech is unaffected.
        if float(np.max(np.abs(audio))) < 1e-4:
            return []
        # YukariWhisper hands over at most ~25 s (see recognizer.py), so the
        # single-shot path is the normal one; transcribe_long() only splits
        # longer input at quiet points.
        if audio.size > 28 * 16000:
            result = self._transcriber.transcribe_long(audio)
        else:
            result = self._transcriber.transcribe(audio)
        text = (result.text or "").strip()
        return [HaasSegment(text)] if text else []
