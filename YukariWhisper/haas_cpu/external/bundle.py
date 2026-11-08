import hashlib
import json
import os
from pathlib import Path
from .frontend_config import load_frontend
from ..core.types import DecodingConfig, TokenTable

FORMATS = ('fp32', 'int8', 'int4-onecomp')


class Bundle:
    # --- YukariWhisper modification (encoding) ---------------------------
    # Every read_text() below passes encoding='utf-8' explicitly.  The
    # model JSON files are UTF-8, but Path.read_text() without an encoding
    # uses the locale default, which on Japanese Windows is cp932 and
    # raises UnicodeDecodeError on tokens.json (byte 0x99 in position
    # 3623).  Upstream (Linux, UTF-8 locale) never sees this.
    #
    # --- YukariWhisper modification -------------------------------------
    # Upstream requires *every* file listed in manifest.json to exist, so a
    # Hugging Face snapshot that contains only one encoder format
    # (e.g. only int8/) cannot be opened.  When ``fmt`` is given, only the
    # files actually needed are required instead: the common files, the
    # chosen encoder (and its external .data file, when one is listed).
    # With fmt=None the original all-files behaviour is kept.
    @classmethod
    def _required_files(cls, manifest, fmt):
        if fmt is None:
            return list(manifest['files'])
        if fmt not in manifest['formats']:
            raise ValueError(f'未対応の形式です: {fmt}')
        required = list(manifest['common'].values())
        encoder = manifest['formats'][fmt]['encoder']
        required.append(encoder)
        if encoder + '.data' in manifest['files']:
            required.append(encoder + '.data')
        return required

    @classmethod
    def open(cls, directory=None, verify=False, fmt=None):
        obj = cls()
        obj.directory = Path(directory or os.environ.get('HAAS_CPU_MODELS') or Path(__file__).resolve().parents[2])
        obj.manifest = json.loads((obj.directory / 'manifest.json').read_text(encoding='utf-8'))
        if obj.manifest['schema'] != 1:
            raise ValueError('未対応のモデルmanifest schemaです')
        required = cls._required_files(obj.manifest, fmt)
        for name, info in ((name, obj.manifest['files'][name]) for name in required):
            path = obj.directory / name
            if not path.is_file():
                raise FileNotFoundError(path)
            if verify:
                if path.stat().st_size != info['bytes']:
                    raise ValueError(f'モデルファイルの大きさが一致しません: {name}')
                with path.open('rb') as f:
                    if hashlib.file_digest(f, 'sha256').hexdigest() != info['sha256']:
                        raise ValueError(f'モデルファイルのSHA256が一致しません: {name}')
        obj.frontend = load_frontend(obj.common('frontend'))
        tokens = json.loads(obj.common('tokens').read_text(encoding='utf-8'))
        assert tokens['byte_fallback'] and len(tokens['pieces']) == 3072
        obj.tokens = TokenTable(tuple(tokens['pieces']), tokens['unk_id'], tokens['add_dummy_prefix'])
        decoding = json.loads(obj.common('decoding').read_text(encoding='utf-8'))
        obj.decoding = DecodingConfig(decoding['blank_id'], tuple(decoding['durations']),
                                     decoding['max_symbols'], decoding['num_tokens'])
        return obj

    def common(self, name):
        return self.directory / self.manifest['common'][name]

    def encoder(self, fmt):
        return self.directory / self.manifest['formats'][fmt]['encoder']
