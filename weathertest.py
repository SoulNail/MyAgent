import requests

def get_weather_seniverse(city, key):
    url = "https://api.seniverse.com/v3/weather/now.json"
    params = {
        "key": key,
        "location": city,
        "language": "zh-Hans",
        "unit": "c"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# 使用示例
key = "Stqu08wWqILJtfygD"
weather = get_weather_seniverse("上海", key)
print(weather)