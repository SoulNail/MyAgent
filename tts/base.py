from abc import ABC, abstractmethod


class BaseTTS(ABC):
    """TTS抽象基类"""

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """
        合成语音

        Args:
            text: 要合成的文本

        Returns:
            音频数据（bytes）
        """
        pass

    @abstractmethod
    def speak(self, text: str):
        """
        合成并播放语音

        Args:
            text: 要播放的文本
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """检查TTS是否就绪"""
        pass