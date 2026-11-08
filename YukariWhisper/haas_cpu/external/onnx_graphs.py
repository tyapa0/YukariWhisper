from pathlib import Path
import numpy as np
import onnxruntime as ort

ENCODER_INPUTS = ('mel', 'mel_length')
ENCODER_OUTPUTS = ('enc_proj', 'enc_length')
PREDICTION_INPUTS = ('token', 'kda_state', 'conv_state')
PREDICTION_OUTPUTS = ('pred_proj', 'kda_state_out', 'conv_state_out')
JOINT_INPUTS = ('enc_frame', 'pred_proj')
JOINT_OUTPUTS = ('logits',)


def make_session(path: Path, threads: int, spinning: bool):
    if threads < 1:
        raise ValueError('threads must be positive')
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.add_session_config_entry('session.intra_op.allow_spinning', '1' if spinning else '0')
    session = ort.InferenceSession(str(path), options, providers=['CPUExecutionProvider'])
    assert session.get_providers()[0] == 'CPUExecutionProvider'
    return session


class EncoderGraph:
    def __init__(self, path, threads):
        self.session = make_session(path, threads, False)

    def run(self, mel, mel_length):
        if mel.shape[2] > 8000:
            raise ValueError('エンコーダ入力は8000フレーム以下にしてください')
        encoded, length = self.session.run(list(ENCODER_OUTPUTS), dict(zip(ENCODER_INPUTS, (mel, mel_length))))
        count = int(length[0])
        return np.ascontiguousarray(encoded[0, :count]), count


class PredictionGraph:
    def __init__(self, path):
        self.session = make_session(path, 1, False)

    @staticmethod
    def empty_state():
        return np.zeros((2, 1, 5, 64, 64), np.float32), np.zeros((2, 1, 3, 320, 4), np.float32)

    def step(self, token, state):
        values = (np.array([token], dtype=np.int64), *state)
        pred, kda, conv = self.session.run(list(PREDICTION_OUTPUTS), dict(zip(PREDICTION_INPUTS, values)))
        return pred, (kda, conv)


class JointGraph:
    def __init__(self, path):
        self.session = make_session(path, 1, False)

    def logits(self, enc_frame, pred_proj):
        return self.session.run(list(JOINT_OUTPUTS), dict(zip(JOINT_INPUTS, (enc_frame, pred_proj))))[0][0]
