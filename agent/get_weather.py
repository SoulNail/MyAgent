import requests
from smolagents import Tool

class WeatherTool(Tool):
    # 1. 定义工具元数据（Agent 会阅读这些信息）
    name = "get_weather"
    description = "查询指定城市的实时天气情况（使用心知天气 API）。"
    inputs = {
        "city": {
            "type": "string",
            "description": "城市名称，例如 '上海' 或 'Beijing'。",
        }
    }
    output_type = "string"

    def __init__(self, weather_config, **kwargs):
        super().__init__(**kwargs)
        # 2. 注入配置：这确保了工具使用的 Key 与 main.py 加载的一致
        self.wea_config = weather_config

    def forward(self, city: str) -> str:
        # 3. 具体的业务逻辑
        params = {
            "key": self.wea_config.seniverse_key,
            "location": city,
            "language": "zh-Hans",
            "unit": "c"
        }

        try:
            response = requests.get(self.wea_config.api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                res = data['results'][0]
                return f"{res['location']['name']}当前天气：{res['now']['text']}，温度：{res['now']['temperature']}℃。"
            return f"天气查询失败，错误码：{response.status_code}"
        except Exception as e:
            return f"工具执行异常: {str(e)}"