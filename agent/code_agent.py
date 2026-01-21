from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel
from .base import BaseAgent
from config.settings import AgentConfig


class SmolCodeAgent(BaseAgent):
    """
    基于 smolagents 的 Code Agent
    具备上下文记忆能力
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent = None
        self._initialize()

    def _initialize(self):
        """初始化Agent"""
        try:
            model = LiteLLMModel(
                model_id=self.config.model_id,
                api_base=self.config.api_base,
                api_key=self.config.api_key
            )

            self.agent = CodeAgent(
                tools=[DuckDuckGoSearchTool()],
                model=model,
                add_base_tools=True,
            )
            print(f"[Agent] 初始化成功")
        except Exception as e:
            print(f"[Agent错误] 初始化失败: {e}")
            raise

    def process(self, user_input: str) -> str:
        """处理用户输入"""
        if not self.agent:
            return "Agent未初始化"

        try:
            response = self.agent.run(user_input, reset=False)  # reset=False会让 Agent 保留之前的对话记录和执行日志
            return str(response)
        except Exception as e:
            print(f"[Agent错误] 处理失败: {e}")
            return "抱歉，处理时出现错误。"

    def is_ready(self) -> bool:
        return self.agent is not None