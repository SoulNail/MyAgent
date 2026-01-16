import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class TTSConfig:
    """TTS配置"""
    api_url: str = "http://192.168.123.100:8080/v1/tts"
    timeout: int = 30


@dataclass
class STTConfig:
    """STT配置"""
    model_path: str = "base"
    device: Literal["cpu", "cuda"] = "cpu"
    compute_type: str = "int8"  # cpu用int8, cuda用float16
    beam_size: int = 5


@dataclass
class VADConfig:
    """VAD配置"""
    aggressiveness: int = 2  # 0-3，越大越激进
    sample_rate: int = 16000
    frame_duration_ms: int = 30
    max_silent_frames: int = 30
    ring_buffer_size: int = 10


@dataclass
class AgentConfig:
    """Agent配置"""
    api_base: str = "http://192.168.123.100:18000/v1"
    model_id: str = "openai/Qwen/Qwen3-4B-Instruct-2507"
    api_key: str = "vllm-token"


@dataclass
class AppConfig:
    """应用总配置"""
    tts: TTSConfig
    stt: STTConfig
    vad: VADConfig
    agent: AgentConfig

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            tts=TTSConfig(
                api_url=os.getenv("TTS_API_URL", TTSConfig.api_url)
            ),
            stt=STTConfig(
                model_path=os.getenv("STT_MODEL_PATH", STTConfig.model_path),
                device=os.getenv("STT_DEVICE", STTConfig.device)
            ),
            vad=VADConfig(),
            agent=AgentConfig(
                api_base=os.getenv("AGENT_API_BASE", AgentConfig.api_base)
            )
        )


# 默认配置实例
default_config = AppConfig(
    tts=TTSConfig(),
    stt=STTConfig(),
    vad=VADConfig(),
    agent=AgentConfig()
)