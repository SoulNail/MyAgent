from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Agent抽象基类"""

    @abstractmethod
    def process(self, user_input: str) -> str:
        """
        处理用户输入

        Args:
            user_input: 用户输入文本

        Returns:
            Agent响应文本
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """检查Agent是否就绪"""
        pass