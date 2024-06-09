from faster_whisper import WhisperModel

# faster-Whisper本体
class WhisperModelWrapper:
    def __init__(self, model_size_or_path, dev, type, index, beam, vad_f, vad_th):
        #print(f"compute_type: {type}")
        self.model = WhisperModel(model_size_or_path, device=dev, device_index=index ,compute_type=type)
        self.beam_size = beam
        self.vad_filter = vad_f
        self.threshold = vad_th

    def transcribe(self, audio):
        segments, _ = self.model.transcribe(
            audio=audio, beam_size=self.beam_size, language="ja", condition_on_previous_text=False, without_timestamps=True,
            vad_filter=self.vad_filter, vad_parameters=dict(threshold=self.threshold),
        )
        return segments
