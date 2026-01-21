import sys
from config.settings import AppConfig, default_config
from orchestrator import VoiceAgentOrchestrator
from tts.fish_speech_tts import FishSpeechTTS, AsyncTTSWorker


def test_tts():
    """测试TTS功能"""
    print("--- 测试 Fish Speech TTS ---")

    tts = FishSpeechTTS(default_config.tts)
    worker = AsyncTTSWorker(tts)

    test_texts = [
        "你好，我是智能助手。",
        "这是一个测试。",
    ]

    for text in test_texts:
        print(f"\n测试: {text}")
        worker.add_task(text)

    worker.wait_complete()
    print("\n所有测试完成")
    worker.stop()


def main():
    """主程序入口"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test-tts":
        test_tts()
    else:
        config = AppConfig.from_env()
        orchestrator = VoiceAgentOrchestrator(config)
        orchestrator.run()


if __name__ == "__main__":
    main()