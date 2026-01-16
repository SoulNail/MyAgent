import queue
import threading
import time
import requests
from .base import BaseTTS
from .player import AudioPlayer
from config.settings import TTSConfig
import ormsgpack  # 必须引入这个库
import os

class FishSpeechTTS(BaseTTS):
    """Fish Speech TTS 实现"""

    def __init__(self, config: TTSConfig):
        self.config = config
        self.player = AudioPlayer()
        self._ready = self._check_connection()

    def _check_connection(self) -> bool:
        """检查服务连接"""
        try:
            # 只尝试实际的TTS端点
            response = requests.post(
                self.config.api_url,
                json={"text": "test"},
                timeout=3
            )
            print(f"[TTS] Fish Speech连接成功")
            return True
        except Exception as e:
            print(f"[TTS警告] 无法连接到 {self.config.api_url}: {e}")
            return False

    def synthesize(self, text: str) -> bytes:
        """合成语音"""
        if not text.strip():
            return b""

        # 1. 读取参考音频数据 (如果配置了路径)
        ref_audio_bytes = b""
        if hasattr(self.config, 'ref_audio_path') and self.config.ref_audio_path:
            if os.path.exists(self.config.ref_audio_path):
                try:
                    with open(self.config.ref_audio_path, "rb") as f:
                        ref_audio_bytes = f.read()
                except Exception as e:
                    print(f"[TTS警告] 读取参考音频失败: {e}")
            else:
                print(f"[TTS警告] 参考音频文件不存在: {self.config.ref_audio_path}")

        # 2. 构造请求 Payload (符合 Fish Speech 标准格式)
        # 注意：这里构造的是一个字典，等下用 msgpack 打包
        request_data = {
            "text": text,
            "streaming": False,
            "format": "wav",
        }

        # 如果有参考音频，塞进去
        if ref_audio_bytes:
            request_data["references"] = [
                {
                    "audio": ref_audio_bytes, # 直接传 bytes
                    "text": self.config.ref_text if hasattr(self.config, 'ref_text') else ""
                }
            ]

        try:
            # 3. 使用 ormsgpack 进行打包 (这也是 Fish Speech 高效的原因)
            # headers 必须改为 application/msgpack
            response = requests.post(
                self.config.api_url,
                data=ormsgpack.packb(request_data),  # 使用 packb 打包二进制
                headers={"Content-Type": "application/msgpack"},
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                return response.content
            else:
                print(f"[TTS错误] HTTP {response.status_code}: {response.text}")
                return b""
        except Exception as e:
            print(f"[TTS错误] {type(e).__name__}: {e}")
            return b""

    def speak(self, text: str):
        """合成并播放"""
        audio_data = self.synthesize(text)
        if audio_data:
            self.player.play(audio_data)

    def is_ready(self) -> bool:
        return self._ready


class AsyncTTSWorker(threading.Thread):
    """异步TTS播放队列"""

    def __init__(self, tts: BaseTTS):
        super().__init__()
        self.tts = tts
        self.queue = queue.Queue()
        self.daemon = True
        self._stop_event = threading.Event()
        self.start()

    def add_task(self, text: str):
        """添加播放任务"""
        if text.strip():
            self.queue.put(text)

    def run(self):
        """工作线程"""
        while not self._stop_event.is_set():
            try:
                text = self.queue.get(timeout=0.5)
                if text is None:
                    break

                print(f"[TTS] 正在合成: {text[:50]}...")
                self.tts.speak(text)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TTS Worker错误] {e}")

    def stop(self):
        """停止工作线程"""
        self._stop_event.set()
        self.queue.put(None)
        self.join(timeout=5)

    def wait_complete(self):
        """等待所有任务完成"""
        self.queue.join()