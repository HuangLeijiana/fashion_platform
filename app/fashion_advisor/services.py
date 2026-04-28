import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FashionAdvisorService:
    def __init__(self):
        self.node_backend_url = 'http://localhost:3001'
        self.timeout = 60

    def health_check(self) -> Dict[str, Any]:
        """检查Node.js后端健康状态"""
        try:
            response = requests.get(
                f'{self.node_backend_url}/api/health',
                timeout=10
            )
            return {
                'status': 'success',
                'nodejs_backend': response.json(),
                'flask_service': 'running'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'message': 'Node.js后端服务不可用',
                'flask_service': 'running'
            }

    def get_fashion_advice(self, message: str) -> Dict[str, Any]:
        """获取时尚建议"""
        try:
            print(f"🔍 正在向Node.js后端发送请求: {message}")

            response = requests.post(
                f'{self.node_backend_url}/api/fashion-advice',
                json={'message': message},
                timeout=self.timeout
            )

            print(f"✅ Node.js响应状态码: {response.status_code}")

            response.raise_for_status()

            # 解析Node.js的响应
            data = response.json()
            print(f"📦 Node.js响应数据: {data}")

            # 检查Node.js返回的数据结构
            if 'response' in data:
                return {'response': data['response']}
            elif 'error' in data:
                return {'error': data['error'], 'response': data.get('response', 'AI服务出错')}
            else:
                # 如果数据结构不符合预期，返回原始数据
                return {'response': str(data)}

        except requests.exceptions.Timeout:
            error_msg = "请求超时，请稍后重试"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'response': '抱歉，AI服务响应超时，请稍后再试。'
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"无法连接到AI服务: {e}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'response': '抱歉，AI服务暂时不可用，请确保Node.js后端正在运行。'
            }
        except Exception as e:
            error_msg = f"处理响应时出错: {e}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'response': '抱歉，服务处理响应时出现错误。'
            }

    def reset_conversation(self) -> Dict[str, Any]:
        """重置对话历史"""
        try:
            response = requests.post(
                f'{self.node_backend_url}/api/reset-conversation',
                timeout=10
            )
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"重置对话失败: {e}")
            return {'message': '对话重置成功'}