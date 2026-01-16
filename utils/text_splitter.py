import re
from typing import List


class SentenceSplitter:
    """句子切分器"""

    @staticmethod
    def split(text: str) -> List[str]:
        """
        将文本切分为句子

        Args:
            text: 输入文本

        Returns:
            句子列表
        """
        # 按标点符号切分
        parts = re.split(r'([。！？；\n]+)', text)

        sentences = []
        current = ""

        for part in parts:
            if re.match(r'[。！？；\n]+', part):
                current += part
                if current.strip():
                    sentences.append(current.strip())
                current = ""
            else:
                current += part

        # 添加剩余部分
        if current.strip():
            sentences.append(current.strip())

        return sentences