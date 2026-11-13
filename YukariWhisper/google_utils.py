#!/usr/bin/env python3
import json
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

# Same endpoint and default key as SpeechRecognition.recognize_google().
GOOGLE_SPEECH_API_URL = "https://www.google.com/speech-api/v2/recognize"
DEFAULT_GOOGLE_API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"


class GoogleUnknownValueError(Exception):
    """The API answered, but no transcript could be extracted.

    Replaces ``speech_recognition.UnknownValueError``.
    """


class GoogleRequestError(Exception):
    """The API could not be reached, or answered with an HTTP error.

    Replaces ``speech_recognition.RequestError``.
    """


class GoogleSpeechRecognizer:
    """Minimal replacement for the one SpeechRecognition call we used."""

    def __init__(self, api_key=None, language="ja-JP", timeout=15.0):
        self.api_key = api_key or DEFAULT_GOOGLE_API_KEY
        self.language = language
        self.timeout = timeout

    def transcribe(self, audio, sample_rate=16000):
        """Recognize a float32 mono numpy array and return the text.

        Raises GoogleUnknownValueError when nothing was recognized and
        GoogleRequestError when the request itself failed - the same
        contract recognize_worker() relied on before.
        """
        audio = np.asarray(audio, dtype=np.float32).flatten()
        if audio.size == 0:
            raise GoogleUnknownValueError("音声データが空です")

        # float32 (-1.0 .. 1.0) -> 16-bit PCM, little-endian ("l16").
        # The old code did the same conversion for sr.AudioData.
        pcm_bytes = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2").tobytes()

        query = urllib.parse.urlencode({
            "output": "json",
            "lang": self.language,
            "key": self.api_key,
            "client": "chromium",
        })
        request = urllib.request.Request(
            f"{GOOGLE_SPEECH_API_URL}?{query}",
            data=pcm_bytes,
            headers={"Content-Type": f"audio/l16; rate={sample_rate}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_text = response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError) as e:
            raise GoogleRequestError(f"Google音声認識APIへのリクエストに失敗しました: {e}") from e

        return self._first_transcript(response_text)

    @staticmethod
    def _first_transcript(response_text):
        """Extract the transcript SpeechRecognition would have returned.

        The response is one JSON object per line; empty results look like
        ``{"result":[]}``.  Following SpeechRecognition's OutputParser,
        the first line with a non-empty result wins, and its first
        alternative is the transcript.  Anything else (no result, no
        alternative, no transcript) is an UnknownValue error.
        """
        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results = json.loads(line).get("result", [])
            except json.JSONDecodeError:
                continue
            if not results:
                continue
            alternatives = results[0].get("alternative", [])
            if not alternatives or not alternatives[0].get("transcript"):
                break
            return alternatives[0]["transcript"]
        raise GoogleUnknownValueError("Google音声認識で結果が得られませんでした")
