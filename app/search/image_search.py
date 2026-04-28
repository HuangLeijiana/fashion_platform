import json
import logging
import os
import pickle

import numpy as np
from flask import current_app
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Product

logger = logging.getLogger(__name__)


class ImageSearchUnavailable(RuntimeError):
    """图像搜索服务不可用。"""


class ImageSearcher:
    """基于本地特征文件的图像相似商品搜索。"""

    def __init__(self, features_path=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.features_path = features_path or os.path.join(current_dir, 'image_features.pkl')
        self.feature_dict = None
        self.model = None

    def _load_model(self):
        if self.model is not None:
            return self.model

        try:
            from tensorflow.keras.applications import MobileNetV2
        except Exception as exc:
            raise ImageSearchUnavailable(f'图像搜索依赖未安装：{exc}') from exc

        self.model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')
        return self.model

    def _load_features(self):
        if self.feature_dict is not None:
            return self.feature_dict

        if not os.path.exists(self.features_path):
            logger.warning('图像特征文件不存在：%s', self.features_path)
            self.feature_dict = {}
            return self.feature_dict

        try:
            with open(self.features_path, 'rb') as handle:
                data = pickle.load(handle)
            self.feature_dict = data.get('feature_dict', {})
            logger.info('图像特征加载完成，共 %s 张图片', len(self.feature_dict))
            return self.feature_dict
        except Exception as exc:
            raise ImageSearchUnavailable(f'图像特征文件加载失败：{exc}') from exc

    def extract_features(self, image_path):
        if not os.path.exists(image_path):
            raise ImageSearchUnavailable(f'查询图片不存在：{image_path}')

        self._load_model()

        try:
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
            from tensorflow.keras.preprocessing import image

            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            features = self.model.predict(img_array, verbose=0).flatten()
            return features / (np.linalg.norm(features) + 1e-10)
        except Exception as exc:
            raise ImageSearchUnavailable(f'查询图片特征提取失败：{exc}') from exc

    def search_similar_products(self, query_image_path, top_k=20):
        feature_dict = self._load_features()
        if not feature_dict:
            return []

        query_features = self.extract_features(query_image_path)
        similarities = []

        for image_path, feature_data in feature_dict.items():
            stored_features = feature_data.get('features') if isinstance(feature_data, dict) else None
            if stored_features is None:
                continue

            stored_features = np.asarray(stored_features).flatten()
            if stored_features.shape != query_features.shape:
                continue

            stored_norm = stored_features / (np.linalg.norm(stored_features) + 1e-10)
            similarity = float(cosine_similarity(
                query_features.reshape(1, -1),
                stored_norm.reshape(1, -1)
            )[0][0])
            similarity = float(np.clip(similarity, 0.0, 1.0))

            if not np.isnan(similarity) and not np.isinf(similarity):
                similarities.append({'image_path': image_path, 'similarity': similarity})

        similarities.sort(key=lambda item: item['similarity'], reverse=True)
        return self._build_results(similarities[:top_k])

    def _build_results(self, image_results):
        results = []
        for item in image_results:
            image_path = item['image_path']
            similarity = item['similarity']
            filename = os.path.basename(image_path)

            product = self._find_product_by_image(filename)
            if product:
                result = product.to_dict()
            else:
                result = self._fallback_result(filename)

            result['similarity_score'] = similarity
            result['similarity_percent'] = round(similarity * 100, 2)
            results.append(result)

        return results

    def _find_product_by_image(self, filename):
        patterns = [
            f'%{filename}%',
            f'%/static/images/products/{filename}%',
            f'%products/{filename}%',
        ]
        for pattern in patterns:
            product = Product.query.filter(Product.images.like(pattern)).first()
            if product:
                return product
        return None

    def _fallback_result(self, filename):
        return {
            'id': None,
            'name': os.path.splitext(filename)[0].replace('_', ' ').title(),
            'description': '本地图库中的相似图片',
            'price': 0.0,
            'category': '图库图片',
            'brand': '本地图库',
            'images': [f'/static/images/products/{filename}'],
            'attributes': {},
        }


image_searcher = ImageSearcher()
