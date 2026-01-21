from config.settings import AppConfig
from stt.whisper_stt import WhisperSTT
from stt.vad_recorder import VADRecorder
from tts.fish_speech_tts import FishSpeechTTS, AsyncTTSWorker
from agent.code_agent import SmolCodeAgent
from utils.text_splitter import SentenceSplitter
import os

class VoiceAgentOrchestrator:
    """语音Agent协调器"""

    def __init__(self, config: AppConfig, launch_mode: str = "talk"):
        self.config = config
        self.launch_mode = launch_mode

        # 1. 基础组件：无论什么模式都需要 Agent
        self.agent = SmolCodeAgent(config.agent, config.weather)
        self.splitter = SentenceSplitter()
        # 2. 语音组件：只有在 talk 模式下才初始化，节省资源
        if self.launch_mode == "talk":
            self.stt = WhisperSTT(config.stt)
            self.recorder = VADRecorder(config.vad)
            self.tts = FishSpeechTTS(config.tts)
            self.tts_worker = AsyncTTSWorker(self.tts)

            # 语音组件状态检查
            if not all([self.stt.is_ready(), self.tts.is_ready()]):
                raise RuntimeError("语音组件初始化失败")
        else:
            # text 模式下，将语音组件设为 None，避免后续调用报错
            self.stt = None
            self.recorder = None
            self.tts = None
            self.tts_worker = None

        self.memory = []
        self.max_memory_length = 10  # 限制记忆轮数，防止 Token 超限

        # Agent 状态检查
        if not self.agent.is_ready():
            raise RuntimeError("Agent 初始化失败")

        print(f"\n系统已就绪！当前模式：{self.launch_mode.upper()}")

    def run(self):
        """运行主循环"""
        if self.launch_mode == "text":
            self._run_text_loop()
        else:
            # 将原本语音模式的代码逻辑
            # 封装到 _run_talk_loop 中，或者直接写在这里
            self._run_talk_loop()

    def _run_text_loop(self):
        """文字模式的专属循环"""
        print("\n" + "=" * 50)
        print("文字交互模式已就绪！输入 '退出' 结束程序。")
        print("=" * 50 + "\n")

        try:
            while True:
                # 使用 Python 原生的 input 获取键盘输入
                user_input = input("用户 (Text): ").strip()

                if not user_input:
                    continue

                # 检查退出指令
                if self._is_exit_command(user_input):
                    print("Agent: 好的，再见。")
                    break

                # Agent 处理
                print("[Agent] 思考中...")
                response = self.agent.process(user_input)
                print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\n[系统] 键盘中断")

    def _run_talk_loop(self):
        """运行主循环"""
        try:
            while True:
                # 1. 录音
                audio_file = self.recorder.listen()

                # 检查文件是否存在且大小正常
                if not audio_file or not os.path.exists(audio_file):
                    continue

                # 2. 语音转文本
                print("[STT] 正在识别...")
                user_input = self.stt.transcribe(audio_file)

                # --- 关键逻辑：识别后立即删除临时音频文件 ---
                try:
                    os.remove(audio_file)
                except:
                    pass

                # 3. 过滤掉幻觉内容
                # 如果识别结果跟你的 initial_prompt 高度相似，直接舍弃
                if not user_input or "普通话" in user_input or "简体中文" in user_input:
                    print("[系统] 忽略无效输入或幻觉")
                    continue

                # if not user_input:
                #     print("[STT] 未识别到有效内容")
                #     continue

                print(f"\n用户: {user_input}")

                # 3. 检查退出指令
                if self._is_exit_command(user_input):
                    self.tts_worker.add_task("好的，再见。")
                    self.tts_worker.wait_complete()
                    break

                # 4. Agent处理
                print("[Agent] 思考中...")
                response = self.agent.process(user_input)
                print(f"\nAgent: {response}\n")

                # 5. 切分句子并异步播放
                sentences = self.splitter.split(response)
                for sentence in sentences:
                    self.tts_worker.add_task(sentence)

        except KeyboardInterrupt:
            print("\n\n[系统] 接收到中断信号")
        finally:
            self.shutdown()

    def _is_exit_command(self, text: str) -> bool:
        """检查是否为退出指令"""
        exit_keywords = ["退出", "再见", "结束", "拜拜"]
        return any(word in text for word in exit_keywords)

    def shutdown(self):
        """关闭系统"""
        print("[系统] 正在关闭...")
        # 关键点：增加判断，只有在语音模式且 worker 存在时才停止
        if self.launch_mode == "talk" and self.tts_worker:
            self.tts_worker.stop()
        print("[系统] 已安全退出")