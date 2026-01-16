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
FISH_SPEECH_API = "http://192.168.123.100:8080/v1/tts"
WHISPER_MODEL_PATH = "base"
DEVICE = "cpu"  # ← 先改为 CPU，解决 CUDA 问题


# --- 1. 异步 TTS 播放队列 ---
class TTSWorker(threading.Thread):
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.queue = queue.Queue()
        self.daemon = True
        self.start()

    def add_task(self, text):
        if text.strip():
            self.queue.put(text)

    def run(self):
        while True:
            text = self.queue.get()
            if text is None:
                break

            print(f"[TTS] 正在合成并播放: {text}")

            payload = {
                "text": text,
                "streaming": False
            }

            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )

                if response.status_code == 200:
                    temp_file = f"temp_output_{int(time.time())}.wav"
                    with open(temp_file, "wb") as f:
                        f.write(response.content)

                    # Windows 播放
                    if os.name == 'nt':
                        import winsound
                        winsound.PlaySound(temp_file, winsound.SND_FILENAME)

                    # 删除临时文件
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                else:
                    print(f"[TTS 错误] HTTP {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                print(f"[TTS 错误] 请求超时")
            except requests.exceptions.ConnectionError:
                print(f"[TTS 错误] 无法连接到 {self.api_url}")
            except Exception as e:
                print(f"[TTS 错误] {type(e).__name__}: {e}")
            finally:
                self.queue.task_done()

    def stop(self):
        self.queue.put(None)
        self.join(timeout=5)


# --- 2. VAD 录音器 ---
class VADRecorder:
    def __init__(self):
        self.vad = webrtcvad.Vad(2)
        self.rate = 16000
        self.frame_duration = 30
        self.frame_size = int(self.rate * self.frame_duration / 1000)

    def listen(self):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frame_size
        )

        print("\n[VAD] 正在倾听...")
        frames = []
        is_speaking = False
        silent_frames = 0
        max_silent_frames = 30

        ring_buffer = collections.deque(maxlen=10)

        try:
            while True:
                frame = stream.read(self.frame_size, exception_on_overflow=False)
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

                    if silent_frames > max_silent_frames:
                        print("[VAD] 语音结束。")
                        break
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        audio_file = "input.wav"
        wf = wave.open(audio_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return audio_file


# --- 3. 核心逻辑 ---
def run_optimized_agent():
    print("--- 正在测试服务连接 ---")

    # 修正：测试正确的端点
    try:
        # 尝试多个可能的健康检查端点
        endpoints = [
            "http://192.168.123.100:8080/health",
            "http://192.168.123.100:8080/v1/health",
            "http://192.168.123.100:8080/",
        ]

        connected = False
        for endpoint in endpoints:
            try:
                print(f"  尝试连接: {endpoint}")
                resp = requests.get(endpoint, timeout=3)
                print(f"  ✓ 响应 {resp.status_code}: {resp.text[:100]}")
                connected = True
                break
            except:
                continue

        if not connected:
            print("  [警告] 无法连接到 Fish Speech，但继续运行...")

    except Exception as e:
        print(f"  [警告] 连接测试失败: {e}")

    # 初始化组件
    print("\n--- 初始化组件 ---")
    recorder = VADRecorder()

    print(f"[STT] 加载 Whisper 模型: {WHISPER_MODEL_PATH} (设备: {DEVICE})")
    try:
        stt_model = WhisperModel(
            WHISPER_MODEL_PATH,
            device=DEVICE,
            compute_type="int8" if DEVICE == "cpu" else "float16"
        )
    except Exception as e:
        print(f"[错误] Whisper 模型加载失败: {e}")
        return

    print("[TTS] 启动异步播放线程")
    tts_worker = TTSWorker(FISH_SPEECH_API)

    # 初始化 Agent
    print("[Agent] 初始化 LLM 和工具")
    try:
        model = LiteLLMModel(
            model_id="openai/Qwen/Qwen3-4B-Instruct-2507",
            api_base=VLLM_API_BASE,
            api_key="vllm-token"
        )
        agent = CodeAgent(
            tools=[DuckDuckGoSearchTool()],
            model=model,
            add_base_tools=True
        )
    except Exception as e:
        print(f"[错误] Agent 初始化失败: {e}")
        return

    print("\n" + "=" * 50)
    print("多模态 Agent 已启动!")
    print("说话后会自动识别，说'退出'结束程序")
    print("=" * 50 + "\n")

    try:
        while True:
            audio_file = recorder.listen()

            print("[STT] 正在识别...")
            try:
                segments, _ = stt_model.transcribe(audio_file, beam_size=5)
                user_input = "".join([s.text for s in segments]).strip()
            except Exception as e:
                print(f"[STT 错误] {e}")
                continue

            if not user_input:
                print("[STT] 未识别到有效内容")
                continue

            print(f"\n用户: {user_input}")

            if any(word in user_input for word in ["退出", "再见", "结束"]):
                tts_worker.add_task("好的，再见。")
                tts_worker.queue.join()
                break

            print("[Agent] 思考中...")
            try:
                full_response = str(agent.run(user_input))
                print(f"\nAgent: {full_response}\n")
            except Exception as e:
                full_response = f"抱歉，处理时出现错误。"
                print(f"[Agent 错误] {e}")

            # 切分句子并播放
            sentences = re.split(r'([。！？；\n]+)', full_response)

            current_sentence = ""
            for part in sentences:
                if re.match(r'[。！？；\n]+', part):
                    current_sentence += part
                    if current_sentence.strip():
                        tts_worker.add_task(current_sentence.strip())
                    current_sentence = ""
                else:
                    current_sentence += part

            if current_sentence.strip():
                tts_worker.add_task(current_sentence.strip())

    except KeyboardInterrupt:
        print("\n\n[系统] 接收到中断信号")
    finally:
        print("[系统] 正在关闭...")
        tts_worker.stop()
        print("[系统] 已退出")


# --- 测试函数 ---
def test_tts_only():
    """测试 TTS"""
    print("--- 测试 Fish Speech TTS ---")

    tts_worker = TTSWorker(FISH_SPEECH_API)

    test_texts = [
        "你好，我是智能助手。",
        "这是一个测试。",
    ]

    for text in test_texts:
        print(f"\n测试: {text}")
        tts_worker.add_task(text)

    tts_worker.queue.join()
    print("\n所有测试完成")
    tts_worker.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test-tts":
        test_tts_only()
    else:
        run_optimized_agent()