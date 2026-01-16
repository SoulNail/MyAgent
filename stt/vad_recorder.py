import pyaudio
import wave
import collections
import webrtcvad
from config.settings import VADConfig


class VADRecorder:
    """基于 WebRTC VAD 的语音录音器"""

    def __init__(self, config: VADConfig):
        self.config = config
        self.vad = webrtcvad.Vad(config.aggressiveness)
        self.frame_size = int(
            config.sample_rate * config.frame_duration_ms / 1000
        )

    def listen(self, output_file: str = "input.wav") -> str:
        """
        监听并录制语音

        Args:
            output_file: 输出文件路径

        Returns:
            录制的音频文件路径
        """
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.frame_size
        )

        print("\n[VAD] 正在倾听...")
        frames = []
        is_speaking = False
        silent_frames = 0
        ring_buffer = collections.deque(maxlen=self.config.ring_buffer_size)

        try:
            while True:
                frame = stream.read(self.frame_size, exception_on_overflow=False)
                is_speech = self.vad.is_speech(frame, self.config.sample_rate)

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

                    if silent_frames > self.config.max_silent_frames:
                        print("[VAD] 语音结束")
                        break
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        # 保存音频
        wf = wave.open(output_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.config.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return output_file