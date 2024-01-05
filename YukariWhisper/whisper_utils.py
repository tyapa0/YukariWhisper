from faster_whisper import WhisperModel

# faster-Whisper本体
class WhisperModelWrapper:
    def __init__(self, model_size_or_path, dev, type, index):
        self.model = WhisperModel(model_size_or_path, device=dev, device_index=index ,compute_type=type)

    def transcribe(self, audio):
        segments, _ = self.model.transcribe(
            audio=audio, beam_size=5, language="ja", without_timestamps=True,
        )
        return segments
