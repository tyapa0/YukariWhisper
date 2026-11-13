# Utterance interval detection using silero_vad.
# This origilal source is
# https://github.com/reriiasu/speech-to-text/blob/main/speech_to_text/vad.py

import numpy as np
import os
import onnxruntime

current_dir = os.path.dirname(os.path.abspath(__file__))

# デジタル無音 (全サンプル 0) がこのチャンク数続いたら、VAD の推論を
# 止めて即 False を返す。1 チャンク = マイクコールバック 1 回 = 100ms。
# ミュートしたマイクや無音デバイスの待機電力を削るのが目的
# 音が戻ったときは、無音を流し続けた場合の定常状態 (h, c) に戻してから推論を再開する
SILENCE_SKIP_CHUNKS = 10  # 10 チャンク = 1 秒

# 無音定常状態を求めるためにゼロ入力を繰り返す回数
SILENCE_STATE_ITERS = 64


class Vad:
    def __init__(self, threshold: float = 0.1):
        model_path = os.path.join(current_dir, "../assets", "silero_vad.onnx")

        options = onnxruntime.SessionOptions()
        options.log_severity_level = 4
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        options.add_session_config_entry("session.inter_op.allow_spinning", "0")

        self.inference_session = onnxruntime.InferenceSession(
            model_path, sess_options=options
        )
        self.SAMPLING_RATE = 16000
        self.threshold = threshold
        self.h = np.zeros((2, 1, 64), dtype=np.float32)
        self.c = np.zeros((2, 1, 64), dtype=np.float32)
        self._silence_chunks = 0      # 連続したデジタル無音チャンク数
        self._silence_skipped = False  # 推論をスキップ中か
        self._silence_state = self._compute_silence_state()

    def _compute_silence_state(self):
        # ゼロ入力を流し続けたときの (h, c) の定常状態を求める。
        h = np.zeros((2, 1, 64), dtype=np.float32)
        c = np.zeros((2, 1, 64), dtype=np.float32)
        input_data = {
            "input": np.zeros((1, 1600), dtype=np.float32),
            "sr": np.array([self.SAMPLING_RATE], dtype=np.int64),
        }
        for _ in range(SILENCE_STATE_ITERS):
            _, h, c = self.inference_session.run(
                None, {**input_data, "h": h, "c": c})
        return h, c

    def is_speech(self, audio_data: np.ndarray) -> bool:
        if not np.any(audio_data):
            # 完全なデジタル無音
            self._silence_chunks += 1
            if self._silence_chunks > SILENCE_SKIP_CHUNKS:
                self._silence_skipped = True
                return False
        else:
            self._silence_chunks = 0
            if self._silence_skipped:
                # 無音を回し続けた場合と同じ状態から再開する
                self.h = self._silence_state[0].copy()
                self.c = self._silence_state[1].copy()
                self._silence_skipped = False

        new_array = audio_data.astype(np.float32, copy=False)
        input_data = {
            "input": new_array.reshape(1, -1),
            "sr": np.array([self.SAMPLING_RATE], dtype=np.int64),
            "h": self.h,
            "c": self.c,
        }
        out, h, c = self.inference_session.run(None, input_data)
        self.h, self.c = h, c
        return out > self.threshold
