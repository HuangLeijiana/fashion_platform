import cv2
import numpy as np
from PIL import Image
import io


def preprocess_image(image_data):
    """预处理图片"""
    try:
        # 转换为numpy数组
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 调整尺寸
        height, width = img.shape[:2]
        max_size = 800
        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))

        return img
    except Exception as e:
        print(f"图片预处理错误: {e}")
        return None


def extract_color_histogram(image):
    """提取颜色直方图特征"""
    try:
        # 转换到HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 计算直方图
        hist_h = cv2.calcHist([hsv], [0], None, [50], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [50], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [50], [0, 256])

        # 归一化
        cv2.normalize(hist_h, hist_h)
        cv2.normalize(hist_s, hist_s)
        cv2.normalize(hist_v, hist_v)

        # 合并特征
        histogram = np.concatenate([hist_h, hist_s, hist_v]).flatten()

        return histogram
    except Exception as e:
        print(f"颜色特征提取错误: {e}")
        return None