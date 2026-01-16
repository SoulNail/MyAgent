import unittest
from config.settings import TTSConfig
from tts.fish_speech_tts import FishSpeechTTS


class TestTTS(unittest.TestCase):

    def setUp(self):
        self.config = TTSConfig()
        self.tts = FishSpeechTTS(self.config)

    def test_synthesize_empty_text(self):
        """测试空文本"""
        result = self.tts.synthesize("")
        self.assertEqual(result, b"")

    def test_synthesize_valid_text(self):
        """测试有效文本"""
        result = self.tts.synthesize("测试")
        # 如果服务可用，应返回音频数据
        # 这个测试需要服务在线
        if self.tts.is_ready():
            self.assertIsInstance(result, bytes)


if __name__ == "__main__":
    unittest.main()