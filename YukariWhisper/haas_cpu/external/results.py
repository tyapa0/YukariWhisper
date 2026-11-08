"""JSON serialization for command output and resumable evaluation records.

YukariWhisper modification: all text I/O below passes encoding='utf-8'
explicitly (see bundle.py; the locale default is cp932 on Japanese
Windows, which corrupts or fails on UTF-8 JSONL with Japanese text).
"""
from dataclasses import asdict
import json
from pathlib import Path


def print_transcription(path, result, as_json):
    if not as_json:
        print(result.text, flush=True)
        return
    seconds = result.timings.total_s
    print(json.dumps(dict(file=str(path), text=result.text, audio_seconds=result.audio_seconds,
                          seconds=seconds, rtfx=result.audio_seconds / seconds if seconds else 0,
                          timings=asdict(result.timings)), ensure_ascii=False), flush=True)


def evaluation_inputs(manifests):
    for manifest in manifests:
        path = Path(manifest)
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            yield row.get('subset', path.stem), row['id'], path.parent / row['audio']


def completed_ids(path):
    if not Path(path).exists():
        return set()
    return {(row['subset'], row['id']) for row in map(json.loads, Path(path).read_text(encoding='utf-8').splitlines())}


def append_result(path, subset, identifier, result):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(json.dumps(dict(subset=subset, id=identifier, text=result.text, tokens=result.token_ids,
                               audio_seconds=result.audio_seconds, timings=asdict(result.timings)), ensure_ascii=False) + '\n')
        f.flush()
