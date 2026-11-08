import json
from pathlib import Path
import numpy as np
from haas_cpu.core.types import FrontendConfig


def load_frontend(path):
    # YukariWhisper modification: encoding='utf-8' explicitly (see bundle.py;
    # without it, Japanese Windows defaults to cp932 and UTF-8 JSON can fail).
    c = json.loads(Path(path).read_text(encoding='utf-8'))
    expected = dict(normalize='per_feature', log_zero_guard_type='add',
                    mag_power=2.0, exact_pad=False, frame_splicing=1, pad_value=0)
    for name, value in expected.items():
        if c[name] != value:
            raise ValueError(f'Unsupported frontend: {name}={c[name]!r}')
    assert (c['sample_rate'], c['n_fft'], c['win_length'], c['hop_length'], c['pad_to']) == (16000, 512, 400, 160, 16)
    return FrontendConfig(c['sample_rate'], c['n_fft'], c['win_length'], c['hop_length'],
                          c['preemph'], c['log_zero_guard_value'], c['pad_to'], 1e-5,
                          np.asarray(c['window'], dtype=np.float32),
                          np.asarray(c['mel_filter'], dtype=np.float32))
