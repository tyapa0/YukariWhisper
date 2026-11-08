"""SentencePiece BPE byte fallback, with one replacement per invalid byte."""
from .types import TokenTable


def decode_bytes(data: bytearray) -> str:
    result = []
    i = 0
    while i < len(data):
        first = data[i]
        size = (1 if first < 0x80 else 2 if 0xC2 <= first <= 0xDF else
                3 if 0xE0 <= first <= 0xEF else 4 if 0xF0 <= first <= 0xF4 else 0)
        if size and i + size <= len(data):
            try:
                result.append(data[i:i + size].decode('utf-8', errors='strict'))
                i += size
                continue
            except UnicodeDecodeError:
                pass
        result.append('\ufffd')
        i += 1
    return ''.join(result)


class Detokenizer:
    def __init__(self, table: TokenTable):
        self.table = table

    def decode(self, ids: list[int]) -> str:
        parts, pending = [], bytearray()
        for token in ids:
            piece = self.table.pieces[token]
            if len(piece) == 6 and piece.startswith('<0x') and piece.endswith('>'):
                pending.append(int(piece[3:5], 16))
                continue
            if pending:
                parts.append(decode_bytes(pending))
                pending.clear()
            if token == self.table.unk_id:
                parts.append(' ⁇ ')
            else:
                if not parts and self.table.add_dummy_prefix and piece.startswith('▁'):
                    piece = piece[1:]
                parts.append(piece.replace('▁', ' '))
        if pending:
            parts.append(decode_bytes(pending))
        return ''.join(parts)
