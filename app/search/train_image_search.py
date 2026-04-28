import os
import sys

# 修复zlibwapi.dll问题
zlib_path = r"D:\Anaconda\envs\tensorflow\DLLs"
if os.path.exists(zlib_path):
    os.environ['PATH'] = zlib_path + os.pathsep + os.environ['PATH']
    print(f"✅ 已添加DLL路径: {zlib_path}")
else:
    print(f"❌ DLL路径不存在: {zlib_path}")

# 现在导入tensorflow
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
import numpy as np
import pickle
from pathlib import Path
import json
from datetime import datetime


class ImageSearchTrainer:
    def __init__(self, image_dir=None, model_save_path="app/search/image_features.pkl"):
        # 如果没有指定图片目录，自动检测项目根目录
        if image_dir is None:
            # 获取当前脚本的绝对路径
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            # 获取项目根目录（当前脚本的父目录的父目录）
            project_root = os.path.dirname(os.path.dirname(current_script_dir))
            # 构建正确的图片目录路径
            image_dir = os.path.join(project_root, "static", "images", "products")

        self.image_dir = image_dir
        self.model_save_path = model_save_path
        self.model = None
        self.feature_dict = {}

        # 配置GPU
        self.setup_gpu()

    def setup_gpu(self):
        """配置GPU设置"""
        # 检查是否有GPU可用
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            try:
                # 设置GPU内存增长
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                print(f"✅ 找到 {len(gpus)} 个GPU设备")

                # 显示GPU信息
                for gpu in gpus:
                    details = tf.config.experimental.get_device_details(gpu)
                    print(f"   - {gpu.name}: {details.get('device_name', 'Unknown')}")

            except RuntimeError as e:
                print(f"⚠️ GPU配置错误: {e}")
        else:
            print("⚠️ 未找到GPU，将使用CPU")

    def load_model(self):
        """加载预训练模型"""
        print("🔄 加载MobileNetV2模型...")
        try:
            self.model = MobileNetV2(
                weights='imagenet',
                include_top=False,  # 不包括顶层分类器
                pooling='avg'  # 全局平均池化
            )
            print("✅ 模型加载完成")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise

    def extract_features(self, image_path):
        """从单张图片提取特征"""
        try:
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                print(f"❌ 图片文件不存在: {image_path}")
                return None

            print(f"   📖 读取图片: {os.path.basename(image_path)}")

            # 加载和预处理图片
            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            print(f"   🔄 提取特征...")
            # 提取特征
            features = self.model.predict(img_array, verbose=0)
            print(f"   ✅ 特征提取完成")
            return features.flatten()
        except Exception as e:
            print(f"❌ 提取特征失败 {image_path}: {e}")
            return None

    def scan_image_directory(self):
        """扫描图片目录并构建特征数据库"""
        print(f"🔍 扫描图片目录: {self.image_dir}")

        # 检查目录是否存在
        if not os.path.exists(self.image_dir):
            print(f"❌ 图片目录不存在: {self.image_dir}")

            # 显示项目结构
            print("\n📂 项目结构:")
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            for root, dirs, files in os.walk(project_root):
                level = root.replace(project_root, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # 只显示前5个文件
                    if file.endswith(('.jpg', '.jpeg', '.png', '.py')):
                        print(f'{subindent}{file}')
                if len(files) > 5:
                    print(f'{subindent}... 还有 {len(files) - 5} 个文件')

            return []

        # 支持的图片格式
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        image_files = []

        for root, dirs, files in os.walk(self.image_dir):
            for file in files:
                if Path(file).suffix.lower() in valid_extensions:
                    full_path = os.path.join(root, file)
                    image_files.append(full_path)

        print(f"📁 找到 {len(image_files)} 张图片")

        # 显示找到的图片
        if image_files:
            print("🖼️ 找到的图片:")
            for img in image_files[:10]:  # 只显示前10个
                print(f"   - {os.path.basename(img)}")
            if len(image_files) > 10:
                print(f"   ... 还有 {len(image_files) - 10} 张图片")
        else:
            print("💡 提示: 请在 static/images/products 目录下放置商品图片")
            # 创建示例图片文件
            self.create_sample_images()
            # 重新扫描
            return self.scan_image_directory()

        return image_files

    def create_sample_images(self):
        """创建示例图片文件（用于测试）"""
        print("🔄 创建示例图片文件...")
        try:
            # 创建一些简单的测试图片
            import cv2
            import numpy as np

            sample_images = [
                ('red_shirt.jpg', (255, 0, 0), "红色衬衫"),
                ('blue_jeans.jpg', (0, 0, 255), "蓝色牛仔裤"),
                ('black_shoes.jpg', (0, 0, 0), "黑色鞋子"),
                ('white_hat.jpg', (255, 255, 255), "白色帽子"),
                ('green_bag.jpg', (0, 255, 0), "绿色背包")
            ]

            for filename, color, description in sample_images:
                img_path = os.path.join(self.image_dir, filename)
                # 创建纯色图片
                img = np.ones((300, 200, 3), dtype=np.uint8)
                img[:, :] = color
                # 添加文字
                cv2.putText(img, description, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.imwrite(img_path, img)
                print(f"   ✅ 创建: {filename}")

            print("📝 已创建示例图片，您可以用自己的商品图片替换它们")

        except Exception as e:
            print(f"❌ 创建示例图片失败: {e}")
            print("💡 请手动在 static/images/products 目录下放置商品图片")

    def train(self):
        """训练图像搜索模型"""
        print("🚀 开始训练图像搜索模型...")

        # 加载模型
        self.load_model()

        # 扫描图片目录
        image_files = self.scan_image_directory()
        if not image_files:
            print("❌ 没有找到图片文件")
            return False

        # 提取特征
        successful_extractions = 0
        for i, img_path in enumerate(image_files):
            print(f"\n🔄 处理图片 {i + 1}/{len(image_files)}")

            features = self.extract_features(img_path)
            if features is not None:
                # 使用相对于static目录的路径作为键
                static_index = img_path.find('static' + os.sep)
                if static_index != -1:
                    relative_path = img_path[static_index:]
                else:
                    relative_path = os.path.basename(img_path)

                self.feature_dict[relative_path] = {
                    'features': features,
                    'filename': os.path.basename(img_path),
                    'full_path': img_path
                }
                successful_extractions += 1
                print(f"   ✅ 成功提取特征")
            else:
                print(f"   ❌ 特征提取失败")

        print(f"\n✅ 成功提取 {successful_extractions}/{len(image_files)} 张图片的特征")

        if successful_extractions == 0:
            print("❌ 没有成功提取任何图片特征")
            return False

        # 保存特征数据库
        self.save_features()
        return True

    def save_features(self):
        """保存特征数据库"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.model_save_path), exist_ok=True)

            # 保存特征数据
            with open(self.model_save_path, 'wb') as f:
                pickle.dump({
                    'feature_dict': self.feature_dict,
                    'training_time': datetime.now().isoformat(),
                    'total_images': len(self.feature_dict),
                    'image_dir': self.image_dir
                }, f)

            print(f"💾 特征数据库已保存到: {self.model_save_path}")
            print(f"📊 包含 {len(self.feature_dict)} 张图片的特征")

        except Exception as e:
            print(f"❌ 保存特征数据库失败: {e}")

    def load_features(self):
        """加载特征数据库"""
        try:
            if os.path.exists(self.model_save_path):
                with open(self.model_save_path, 'rb') as f:
                    data = pickle.load(f)
                    self.feature_dict = data['feature_dict']
                print(f"✅ 加载特征数据库成功，包含 {len(self.feature_dict)} 张图片")
                return True
            else:
                print("❌ 特征数据库不存在，请先训练模型")
                return False
        except Exception as e:
            print(f"❌ 加载特征数据库失败: {e}")
            return False


def main():
    """主训练函数"""
    print("=" * 50)
    print("🖼️  图像搜索模型训练脚本")
    print("=" * 50)

    # 创建训练器实例 - 自动检测项目根目录
    trainer = ImageSearchTrainer(
        model_save_path="image_features.pkl"
    )

    # 开始训练
    success = trainer.train()

    if success:
        print("\n🎉 训练完成！")
        print("📁 特征数据库已保存，现在可以使用图像搜索功能")
    else:
        print("\n❌ 训练失败，请检查错误信息")


if __name__ == "__main__":
    main()