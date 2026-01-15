import os
import queue
import threading
import time
import requests
import re
import pyaudio
import wave
import collections
import webrtcvad
from faster_whisper import WhisperModel
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

# --- 配置区 ---
VLLM_API_BASE = "http://192.168.123.100:18000/v1"
FISH_SPEECH_API = "http://127.0.0.1:8080/v1/tts"
WHISPER_MODEL_PATH = "base"
DEVICE = "cpu"


# --- 1. 异步 TTS 播放队列 (解决阻塞问题) ---
class TTSWorker(threading.Thread):
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.queue = queue.Queue()
        self.daemon = True  # 随主线程退出
        self.start()

    def add_task(self, text):
        if text.strip():
            self.queue.put(text)

    def run(self):
        while True:
            text = self.queue.get()
            if text is None: break

            print(f"[TTS] 正在合成并播放: {text}")
            payload = {
                "text": text,
                "format": "mp3",
                "reference_id": "你的参考音频ID"
            }
            try:
                response = requests.post(self.api_url, json=payload)
                if response.status_code == 200:
                    with open("temp_output.mp3", "wb") as f:
                        f.write(response.content)
                    # 使用 ffplay 播放，-nodisp 不显示窗口，-autoexit 播放完退出
                    os.system("ffplay -nodisp -autoexit temp_output.mp3 > /dev/null 2>&1")
            except Exception as e:
                print(f"TTS 线程错误: {e}")
            finally:
                self.queue.task_done()


# --- 2. VAD 录音器 (实现“说完即停”) ---
class VADRecorder:
    def __init__(self):
        self.vad = webrtcvad.Vad(2)  # 灵敏度 0-3，3 最灵敏
        self.rate = 16000
        self.frame_duration = 30  # 毫秒
        self.frame_size = int(self.rate * self.frame_duration / 1000)  # 480 bytes

    def listen(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=self.rate,
                        input=True, frames_per_buffer=self.frame_size)

        print("\n[VAD] 正在倾听...")
        frames = []
        is_speaking = False
        silent_frames = 0
        max_silent_frames = 30  # 约 0.9 秒静音则停止录音

        # 环形缓冲区，用于保留说话前的一点音频
        ring_buffer = collections.deque(maxlen=10)

        while True:
            frame = stream.read(self.frame_size)
            is_speech = self.vad.is_speech(frame, self.rate)

            if not is_speaking:
                if is_speech:
                    print("[VAD] 检测到语音...")
                    is_speaking = True
                    frames.extend(list(ring_buffer))
                    frames.append(frame)
                else:
                    ring_buffer.append(frame)
            else:
                frames.append(frame)
                if not is_speech:
                    silent_frames += 1
                else:
                    silent_frames = 0

                # 如果静音超过一定时长，停止录音
                if silent_frames > max_silent_frames:
                    print("[VAD] 语音结束。")
                    break

        stream.stop_stream()
        stream.close()
        p.terminate()

        # 保存临时文件
        wf = wave.open("input.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return "input.wav"


# --- 3. 核心逻辑集成 ---
def run_optimized_agent():
    # 初始化组件
    recorder = VADRecorder()
    stt_model = WhisperModel(WHISPER_MODEL_PATH, device=DEVICE, compute_type="int8")
    tts_worker = TTSWorker(FISH_SPEECH_API)

    # 初始化 Agent
    model = LiteLLMModel(
        model_id="openai/Qwen/Qwen3-4B-Instruct-2507",
        api_base=VLLM_API_BASE,
        api_key="vllm-token"
    )
    agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model, add_base_tools=True)

    print("--- 多模态 Agent 已启动 (VAD + 异步播放) ---")

    while True:
        # Step 1: VAD 录音
        audio_file = recorder.listen()

        # Step 2: STT 识别
        segments, _ = stt_model.transcribe(audio_file, beam_size=5)
        user_input = "".join([s.text for s in segments]).strip()

        if not user_input:
            continue
        print(f"用户: {user_input}")

        if "退出" in user_input:
            tts_worker.add_task("好的，再见。")
            time.sleep(2)  # 等待播报完
            break

        # Step 3: Agent 运行
        print("[Agent] 思考中...")
        full_response = agent.run(user_input)

        # Step 4: 自动切分并加入异步播放队列
        # 使用正则表达式按句切分，避免等待整段生成
        sentences = re.split(r'(?<=[。！？；\n])', full_response)
        for sentence in sentences:
            if sentence.strip():
                # 将句子丢进队列，主线程立刻继续处理下一句或准备听下一轮
                tts_worker.add_task(sentence.strip())


if __name__ == "__main__":
    run_optimized_agent()