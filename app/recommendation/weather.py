"""天气模块：获取天气数据并生成穿搭建议。"""

import os
import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def get_weather(
    city_name: str | None = None, ip: str | None = None
) -> tuple[str, float, str]:
    """获取指定城市（或通过IP推断）的实时天气。

    Returns:
        (city_name, temperature_celsius, condition_chinese)
    """
    try:
        if not city_name:
            city_api = f"https://ipapi.co/{ip}/json/"
            city_resp = requests.get(city_api, timeout=6).json()
            city_name = city_resp.get("city", "北京")

        api_url = "http://apis.juhe.cn/simpleWeather/query"
        api_key = current_app.config.get("WEATHER_API_KEY") or os.environ.get(
            "WEATHER_API_KEY", ""
        )
        params = {"key": api_key, "city": city_name}
        weather_resp = requests.get(api_url, params=params, timeout=6).json()

        if weather_resp.get("error_code") != 0:
            return city_name, 20, "晴朗"

        realtime = weather_resp["result"]["realtime"]
        temp = float(realtime.get("temperature", 20))
        condition = realtime.get("info", "晴朗")
        return city_name, temp, condition
    except Exception as e:
        logger.error("天气获取失败: %s", e)
        return city_name or "未知城市", 20, "晴朗"


def get_weather_outfit_suggestion(
    temp: float, condition: str, cloth_type: str
) -> str:
    """根据气温、天气状况和衣物类型生成纯中文穿搭建议。

    Args:
        temp: 气温（℃）
        condition: 天气状况（中文）
        cloth_type: 衣物类型（中文）
    """
    # 温度分段建议
    if temp >= 30:
        temp_suggest = "高温天气"
        outfit_tip = f"{cloth_type}材质透气舒适，适合高温环境，能有效散热"
    elif 20 <= temp < 30:
        temp_suggest = "适宜温度"
        outfit_tip = f"{cloth_type}厚度适中，适配当前气温，穿搭舒适无负担"
    elif 10 <= temp < 20:
        temp_suggest = "微凉天气"
        outfit_tip = f"{cloth_type}保暖性较好，可搭配薄外套穿着，应对微凉气温"
    else:
        temp_suggest = "低温天气"
        outfit_tip = f"{cloth_type}保暖性强，适合低温环境，能有效抵御寒冷"

    # 天气状况补充建议
    weather_supplement = ""
    if "雨" in condition:
        weather_supplement = " 雨天路面湿滑，搭配防水鞋履更佳"
    elif "雪" in condition:
        weather_supplement = " 雪天寒冷且路面易滑，建议搭配防滑鞋和厚袜子"
    elif "晴" in condition:
        weather_supplement = " 晴天阳光充足，可搭配遮阳帽或太阳镜"
    elif "阴" in condition:
        weather_supplement = " 阴天无强烈日晒，穿搭灵活性高"

    return f"{temp_suggest}（{temp}℃，{condition}）{outfit_tip}{weather_supplement}"
