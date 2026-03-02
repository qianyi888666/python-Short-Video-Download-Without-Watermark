"""
URL解析和验证模块

负责解析和验证不同平台的视频链接。
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class URLParser:
    """URL解析器类，支持抖音、快手、小红书等平台的链接解析"""
    
    # 各平台URL正则表达式模式
    PLATFORM_PATTERNS = {
        "douyin": {
            "pattern": r"https?://v\.douyin\.com/[A-Za-z0-9]+/?",
            "example": "https://v.douyin.com/3ir1Xw2ulGo/"
        },
        "kuaishou": {
            "pattern": r"https?://v\.kuaishou\.com/[A-Za-z0-9]+/?",
            "example": "https://v.kuaishou.com/nigsINQH"
        },
        "xiaohongshu": {
            "pattern": r"https?://xhslink\.com/[a-zA-Z0-9/]+",
            "example": "http://xhslink.com/o/8KJF6Dy0t6l"
        }
    }
    
    @classmethod
    def extract_clean_url(cls, url: str) -> Optional[str]:
        """从复杂的分享文本中提取纯链接
        
        Args:
            url: 可能包含额外文本的URL字符串
            
        Returns:
            清理后的纯URL，如果无法提取则返回None
        """
        # 使用正则表达式提取URL
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, url)
        
        if match:
            extracted_url = match.group(0).strip()
            # 移除末尾可能的标点符号
            extracted_url = extracted_url.rstrip('.,;:!?)')
            return extracted_url
        
        return None
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """验证URL格式是否正确
        
        Args:
            url: 要验证的URL
            
        Returns:
            URL是否有效
        """
        if not url:
            return False
        
        try:
            result = urlparse(url)
            # 检查协议是否为http或https
            if result.scheme not in ['http', 'https']:
                return False
            # 检查网络位置是否有效
            if not result.netloc or result.netloc.startswith('.'):
                return False
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @classmethod
    def identify_platform(cls, url: str) -> Optional[str]:
        """识别URL所属的平台
        
        Args:
            url: 要识别的URL
            
        Returns:
            平台名称，如果不支持则返回None
        """
        if not cls.validate_url(url):
            return None
        
        for platform, config in cls.PLATFORM_PATTERNS.items():
            pattern = config["pattern"]
            if re.match(pattern, url):
                return platform
        
        return None
    
    @classmethod
    def parse_and_validate(cls, url: str) -> Tuple[str, str]:
        """解析并验证URL，返回清理后的URL和平台名称
        
        Args:
            url: 原始URL字符串
            
        Returns:
            元组 (清理后的URL, 平台名称)
            
        Raises:
            ValueError: 当URL无效或平台不支持时
        """
        # 提取纯URL
        clean_url = cls.extract_clean_url(url)
        if not clean_url:
            raise ValueError("无法从输入中提取有效的URL")
        
        # 验证URL格式
        if not cls.validate_url(clean_url):
            raise ValueError("URL格式无效")
        
        # 识别平台
        platform = cls.identify_platform(clean_url)
        if not platform:
            raise ValueError("不支持的平台或URL格式")
        
        return clean_url, platform
    
    @classmethod
    def get_supported_platforms(cls) -> dict:
        """获取所有支持的平台信息
        
        Returns:
            包含平台信息的字典
        """
        return cls.PLATFORM_PATTERNS.copy()
    
    @classmethod
    def is_platform_supported(cls, platform: str) -> bool:
        """检查指定平台是否支持
        
        Args:
            platform: 平台名称
            
        Returns:
            是否支持该平台
        """
        return platform in cls.PLATFORM_PATTERNS