from typing import Optional
from faster_whisper import WhisperModel
from .base import BaseSTT
from config.settings import STTConfig


class WhisperSTT(BaseSTT):
    """基于 Faster-Whisper 的 STT 实现"""

    def __init__(self, config: STTConfig):
        self.config = config
        self.model: Optional[WhisperModel] = None
        self._initialize()

    def _initialize(self):
        """初始化模型"""
        try:
            compute_type = self.config.compute_type
            if self.config.device == "cpu" and compute_type == "float16":
                compute_type = "int8"

            self.model = WhisperModel(
                self.config.model_path,
                device=self.config.device,
                compute_type=compute_type
            )
            print(f"[STT] Whisper模型加载成功: {self.config.model_path} ({self.config.device})")
        except Exception as e:
            print(f"[STT错误] 模型加载失败: {e}")
            raise

    def transcribe(self, audio_file: str) -> str:
        """转录音频"""
        if not self.model:
            raise RuntimeError("STT模型未初始化")

        try:
            segments, _ = self.model.transcribe(
                audio_file,
                beam_size=self.config.beam_size,
                language = "zh",  # 强制使用中文
                initial_prompt="简体中文。",
                vad_filter = True,
                vad_parameters = dict(min_silence_duration_ms=500),
                no_speech_threshold=0.6
            )
            text = "".join([s.text for s in segments]).strip()
            return text
        except Exception as e:
            print(f"[STT错误] 转录失败: {e}")
            return ""

    def is_ready(self) -> bool:
        """检查是否就绪"""
        return self.model is not None