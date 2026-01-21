import argparse
from config.settings import AppConfig
from orchestrator import VoiceAgentOrchestrator
import warnings
import os

# 忽略 Pydantic 序列化警告
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")
# 或者更粗暴地忽略所有 UserWarning
# warnings.filterwarnings("ignore", category=UserWarning)

# 有时候 LiteLLM 还会通过环境变量触发一些日志，顺便关掉
os.environ["LITELLM_LOG"] = "ERROR"

def main():
    """主程序入口"""
    # 1. 配置命令行参数解析
    parser = argparse.ArgumentParser(description="SmolAgents 多模态对话系统")

    # 添加 --launch 参数
    # choices 限制了只能输入 text 或 talk
    # default="talk" 确保了如果直接运行 python main.py，它默认进入语音模式
    parser.add_argument(
        "--launch",
        choices=["text", "talk"],
        default="talk",
        help="启动模式: text (文字模式) 或 talk (语音模式)"
    )

    args = parser.parse_args()

    # 2. 加载配置
    config = AppConfig.from_env()

    # 3. 启动协调器
    orchestrator = VoiceAgentOrchestrator(config, launch_mode=args.launch)

    try:
        orchestrator.run()
    except Exception as e:
        print(f"\n[程序异常] {e}")
    finally:
        # 确保在退出时执行清理工作
        if hasattr(orchestrator, 'shutdown'):
            orchestrator.shutdown()


if __name__ == "__main__":
    main()