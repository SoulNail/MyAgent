from smolagents import CodeAgent, DuckDuckGoSearchTool, VisitWebpageTool, LiteLLMModel

# 1. 配置 vLLM 运行的远程模型
# 注意：vLLM 的 api_base 通常需要包含 /v1 后缀
model = LiteLLMModel(
    # 必须与日志中的 served_model_name 一致
    model_id="openai/Qwen/Qwen3-4B-Instruct-2507",

    # 确保包含 /v1 且 IP/端口正确
    api_base="http://192.168.123.100:18000/v1",

    # vLLM 不需要 Key，但 LiteLLM 必须传一个非空字符串
    api_key="vllm-token",

    # 你的日志显示 max_model_len 为 10240，这里设置稍微小一点留出生成空间
    num_ctx=10240,

    extra_body = {
        "timeout": 300
    }
)

# 2. 初始化工具列表
# 一个 Agent 可以挂载无限个工具，只需放入列表
tools = [
    DuckDuckGoSearchTool(),
    VisitWebpageTool()
]

# 3. 创建 Agent
agent = CodeAgent(
    tools=tools,
    model=model,
    add_base_tools=True,
    max_steps=10,
)

# 4. 执行多工具协同任务
# 这个任务强制 Agent 先搜索，再判断链接，再抓取内容
prompt = (
    "搜索 2025 年发布的最新版 smolagents 框架有哪些重大更新。 "
    "从结果中挑一个 Hugging Face 的官方链接，使用网页访问工具深入读取内容， "
    "最后总结该框架对本地模型（如 Qwen）的支持情况。"
)


agent.run(prompt)