"""公共服务层单元测试 — 图片工具、配置管理。"""

import os
import tempfile

import pytest
import numpy as np
from PIL import Image

from app.services.image_utils import extract_dominant_color, _classify_hsv


class TestExtractDominantColor:
    def test_kmeans_black_image(self):
        """全黑图片应返回 '黑色'。"""
        img = Image.new("RGB", (100, 100), color=(10, 10, 10))
        result = extract_dominant_color(img, method="kmeans")
        assert result == "黑色"

    def test_kmeans_white_image(self):
        """全白图片应返回 '白色'。"""
        img = Image.new("RGB", (100, 100), color=(250, 250, 250))
        result = extract_dominant_color(img, method="kmeans")
        assert result in ("白色", "灰色")

    def test_kmeans_red_image(self):
        """纯红图片应返回 '红色'。"""
        img = Image.new("RGB", (100, 100), color=(200, 30, 30))
        result = extract_dominant_color(img, method="kmeans")
        assert result == "红色"

    def test_kmeans_blue_image(self):
        """纯蓝图片应返回 '蓝色'。"""
        img = Image.new("RGB", (100, 100), color=(30, 60, 200))
        result = extract_dominant_color(img, method="kmeans")
        assert result == "蓝色"

    def test_mean_fallback(self):
        """均值法作为回退方案应也能得出合理结果。"""
        img = Image.new("RGB", (100, 100), color=(20, 20, 20))
        result = extract_dominant_color(img, method="mean")
        assert result == "黑色"

    def test_from_file_path(self):
        """从文件路径提取颜色。"""
        fd, path = tempfile.mkstemp(suffix=".jpg")
        img = Image.new("RGB", (80, 80), color=(220, 30, 30))
        img.save(path)
        try:
            result = extract_dominant_color(path, method="kmeans")
            assert result in ("红色", "其他")
        finally:
            os.close(fd)
            os.unlink(path)


class TestHSVClassifier:
    def test_black(self):
        assert _classify_hsv(0, 0, 20) == "黑色"

    def test_white(self):
        assert _classify_hsv(0, 5, 220) == "白色"

    def test_red(self):
        assert _classify_hsv(5, 200, 150) == "红色"

    def test_blue(self):
        assert _classify_hsv(120, 200, 150) == "蓝色"

    def test_green(self):
        assert _classify_hsv(60, 200, 150) == "绿色"

    def test_purple(self):
        assert _classify_hsv(200, 200, 150) == "紫色"
