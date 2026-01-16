from abc import ABC, abstractmethod
from typing import Optional


class BaseSTT(ABC):
    """STT抽象基类"""

    @abstractmethod
    def transcribe(self, audio_file: str) -> str:
        """
        转录音频文件

        Args:
            audio_file: 音频文件路径

        Returns:
            识别的文本
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """检查STT是否就绪"""
        pass