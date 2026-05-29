"""共享图片处理工具 — 颜色提取、类型推断等，供多个模块复用。"""

import logging
import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger(__name__)


def extract_dominant_color(source, method="kmeans"):
    """从图片中提取主色调（中文结果）。

    参数
    ----
    source : str 或 PIL.Image.Image
        图片文件路径，或已打开的 PIL Image 对象。
    method : str
        ``"kmeans"``（默认，更准确）或 ``"mean"``（更快但粗糙）。

    返回
    ----
    str
        中文颜色名，例如 "黑色"、"蓝色"、"白色" 等。
    """
    if method == "mean":
        return _extract_via_mean(source)

    try:
        if isinstance(source, str):
            data = np.fromfile(source, dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        else:
            # PIL Image → numpy
            image = np.array(source.convert("RGB"))
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if image is None:
            return "未知"

        image = cv2.resize(image, (50, 50))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pixels = np.float32(image.reshape(-1, 3))

        k = 5
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        counts = np.bincount(labels.flatten())
        sorted_indices = np.argsort(counts)[::-1]

        for idx in sorted_indices:
            color_rgb = centers[idx].astype(int)
            color_hsv = cv2.cvtColor(np.uint8([[color_rgb]]), cv2.COLOR_RGB2HSV)[0][0]
            h, s, v = color_hsv

            is_background_white = (s < 20 and v > 230)
            is_background_black = (v < 40)

            if idx == sorted_indices[0] and len(sorted_indices) > 1:
                if is_background_white or is_background_black:
                    continue

            return _classify_hsv(h, s, v)

        return "其他"

    except Exception:
        logger.exception("KMeans 颜色提取失败，回退到均值法")
        return _extract_via_mean(source)


def _classify_hsv(h, s, v):
    """基于 HSV 值将颜色归类为中文名称。"""
    if v < 45:
        return "黑色"
    if s < 15 and v > 210:
        return "白色"
    if s < 40:
        return "灰色"

    if 0 <= h <= 10 or 340 <= h <= 360:
        if v < 120 or (s < 80 and v < 180):
            return "棕色"
        return "红色"

    if 11 <= h <= 25:
        if v < 160 or s < 120:
            return "棕色"
        return "橙色"

    if 26 <= h <= 35:
        if v < 100:
            return "棕色"
        return "黄色"

    if 36 <= h <= 85:
        if v < 60:
            return "黑色"
        return "绿色"

    if 86 <= h <= 170:
        if v < 60:
            return "黑色"
        return "蓝色"

    if 171 <= h <= 260:
        return "紫色"

    if 261 <= h <= 320:
        if s < 40 and v > 200:
            return "白色"
        return "粉色"

    if 321 <= h <= 340:
        return "棕色"

    return "其他"


def _extract_via_mean(source):
    """基于 RGB 均值的简易颜色判断（KMeans 失败时的回退）。"""
    try:
        if isinstance(source, str):
            image = Image.open(source).convert("RGB")
        else:
            image = source.convert("RGB")

        array = np.array(image.resize((80, 80))).reshape(-1, 3)
        mean_rgb = array.mean(axis=0)
        red, green, blue = mean_rgb

        if max(mean_rgb) < 55:
            return "黑色"
        if min(mean_rgb) > 215 and np.std(mean_rgb) < 15:
            return "白色"
        if abs(red - green) < 12 and abs(green - blue) < 12:
            return "灰色"
        if blue >= red and blue >= green:
            return "蓝色"
        if red >= blue and red >= green:
            if green > 150:
                return "黄色"
            if blue > 135:
                return "粉色"
            return "红色"
        if green >= red and green >= blue:
            return "棕色" if red > 140 else "绿色"
        return "卡其色"

    except Exception:
        logger.exception("均值颜色提取失败")
        return "未知"
