from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)

_JUHE_API_KEY = '93273738eb385cccac845a7ccfb4ef8c'
_JUHE_API_URL = 'http://apis.juhe.cn/simpleWeather/query'
_IP_LOCATION_URL = 'https://ipapi.co/{ip}/json/'
_DEFAULT_CITY = '北京'
_DEFAULT_TEMP = 20.0
_DEFAULT_CONDITION = '晴朗'


class WeatherService:
    """天气服务，供推荐模块和顾问模块共用。"""

    def __init__(self) -> None:
        self.timeout = 6

    def get_weather(self, city_name: str | None = None, ip: str | None = None) -> dict[str, Any]:
        if not current_app.config.get('FEATURE_WEATHER_SERVICE', True):
            return self._build_result(city_name or _DEFAULT_CITY, _DEFAULT_TEMP, _DEFAULT_CONDITION)

        try:
            resolved_city = city_name or self._resolve_city_by_ip(ip)
        except Exception:
            logger.warning('IP定位失败，使用默认城市')
            resolved_city = city_name or _DEFAULT_CITY

        try:
            resp = requests.get(
                _JUHE_API_URL,
                params={'key': _JUHE_API_KEY, 'city': resolved_city},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get('error_code') != 0:
                logger.warning('天气API返回错误: %s', data.get('reason', ''))
                return self._build_result(resolved_city, _DEFAULT_TEMP, _DEFAULT_CONDITION)

            realtime = data['result']['realtime']
            temp = float(realtime.get('temperature', _DEFAULT_TEMP))
            condition = realtime.get('info', _DEFAULT_CONDITION)
            humidity = realtime.get('humidity', '')
            wind = realtime.get('direct', '') + realtime.get('power', '')

            return self._build_result(resolved_city, temp, condition, humidity, wind)

        except Exception:
            logger.exception('天气API调用失败')
            return self._build_result(resolved_city or _DEFAULT_CITY, _DEFAULT_TEMP, _DEFAULT_CONDITION)

    def get_suggestion_for_temp(self, temp: float) -> str:
        if temp >= 30:
            return '气温偏高，建议选择透气、轻盈、易活动的搭配。'
        if temp >= 25:
            return '气温较高，可以用轻薄材质和浅色系来保持清爽。'
        if temp >= 18:
            return '气温适中，可在质感和层次之间取得平衡。'
        if temp >= 10:
            return '天气微凉，建议加入轻薄外套或针织开衫，保持灵活层次。'
        return '气温偏低，建议加入保暖层或提升材质厚度。'

    def _resolve_city_by_ip(self, ip: str | None) -> str:
        if not ip:
            return _DEFAULT_CITY
        resp = requests.get(_IP_LOCATION_URL.format(ip=ip), timeout=self.timeout)
        data = resp.json()
        return data.get('city', _DEFAULT_CITY)

    def _build_result(
        self,
        city: str,
        temperature: float,
        condition: str,
        humidity: str = '',
        wind: str = '',
    ) -> dict[str, Any]:
        return {
            'city': city,
            'temperature': temperature,
            'condition': condition,
            'humidity': humidity,
            'wind': wind,
            'suggestion': self.get_suggestion_for_temp(temperature),
        }


weather_service = WeatherService()
