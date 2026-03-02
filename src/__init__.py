"""
视频去水印工具包

支持抖音、快手、小红书等平台的视频去水印功能。
"""

from .api_client import VideoWatermarkClient
from .url_parser import URLParser
from .exceptions import (
    VideoWatermarkError,
    InvalidURLError,
    APINotAvailableError,
    DataStructureError,
    MemberAPIError,
    APIClosedError,
    InsufficientQuotaError,
    ParseFailedError,
    InsufficientLevelError,
    create_exception_by_status_code
)

__version__ = "1.0.0"
__author__ = "PyDev Team"
__email__ = "support@pydev.com"

__all__ = [
    "VideoWatermarkClient",
    "URLParser",
    "VideoWatermarkError",
    "InvalidURLError",
    "APINotAvailableError",
    "DataStructureError",
    "MemberAPIError",
    "APIClosedError",
    "InsufficientQuotaError",
    "ParseFailedError",
    "InsufficientLevelError",
    "create_exception_by_status_code"
]