"""
API客户端模块

负责与去水印API进行通信，处理请求和响应。
"""

import json
from typing import Dict, Any, Optional
import requests
try:
    from .exceptions import create_exception_by_status_code, VideoWatermarkError
except ImportError:
    from exceptions import create_exception_by_status_code, VideoWatermarkError


class VideoWatermarkClient:
    """视频去水印API客户端"""
    
    def __init__(self, client_id: str = "demo_client_id_12345", 
                 client_secret_key: str = "demo_secret_key_abcdef123456789",
                 base_url: str = "https://api.example.com/video/dsp"):
        """初始化API客户端
        
        Args:
            client_id: 客户端ID
            client_secret_key: 客户端密钥
            base_url: API基础URL
        """
        self.client_id = client_id
        self.client_secret_key = client_secret_key
        self.base_url = base_url
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def build_api_url(self, video_url: str) -> str:
        """构建API请求URL
        
        Args:
            video_url: 视频URL
            
        Returns:
            完整的API请求URL
        """
        return f"{self.base_url}/{self.client_secret_key}/{self.client_id}/?url={video_url}"
    
    def remove_watermark(self, video_url: str, timeout: int = 30) -> Dict[str, Any]:
        """去除视频水印
        
        Args:
            video_url: 视频URL
            timeout: 请求超时时间（秒）
            
        Returns:
            包含视频信息的字典，包括封面、视频地址和标题
            
        Raises:
            VideoWatermarkError: 当API调用失败时
        """
        api_url = self.build_api_url(video_url)
        
        try:
            response = self.session.get(api_url, timeout=timeout)
            response.raise_for_status()
            
            # 解析响应
            try:
                data = response.json()
            except json.JSONDecodeError:
                raise VideoWatermarkError("API返回数据格式错误")
            
            # 检查响应状态
            if not isinstance(data, dict):
                raise VideoWatermarkError("API返回数据结构错误")
            
            # 处理API错误状态码
            if 'code' in data and data['code'] != 200:
                status_code = data['code']
                message = data.get('msg', f"API错误 (状态码: {status_code})")
                raise create_exception_by_status_code(status_code, message)
            
            # 验证成功响应的数据结构
            if 'data' not in data:
                raise VideoWatermarkError("API响应缺少必要的数据字段")
            
            video_data = data['data']
            
            # 检查必要字段
            required_fields = ['url', 'title', 'cover']
            for field in required_fields:
                if field not in video_data:
                    raise VideoWatermarkError(f"API响应缺少必要字段: {field}")
            
            return {
                'success': True,
                'video_url': video_data['url'],
                'title': video_data['title'],
                'cover_url': video_data['cover'],
                'raw_data': data
            }
            
        except VideoWatermarkError:
            # 重新抛出我们自己的异常
            raise
        except requests.exceptions.Timeout:
            raise VideoWatermarkError("请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            raise VideoWatermarkError("网络连接错误，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise VideoWatermarkError("API地址不存在")
            elif e.response.status_code == 500:
                raise VideoWatermarkError("服务器内部错误")
            else:
                raise VideoWatermarkError(f"HTTP错误: {e.response.status_code}")
        except Exception as e:
            # 处理其他所有异常，包括网络异常和JSON解析异常
            raise VideoWatermarkError(f"请求异常: {str(e)}")
    
    def remove_watermark_with_retry(self, video_url: str, max_retries: int = 3, 
                                   timeout: int = 30) -> Dict[str, Any]:
        """带重试机制的去水印功能
        
        Args:
            video_url: 视频URL
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
            
        Returns:
            包含视频信息的字典
            
        Raises:
            VideoWatermarkError: 当所有重试都失败时
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return self.remove_watermark(video_url, timeout)
            except VideoWatermarkError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # 对于某些错误类型不进行重试
                    if e.status_code in [103, 108, 109, 115]:
                        break
                    continue
        
        raise last_exception
    
    def close(self):
        """关闭会话"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()