"""
自定义异常类模块

定义了视频去水印过程中可能出现的各种异常情况。
"""


class VideoWatermarkError(Exception):
    """视频去水印基础异常类"""
    
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InvalidURLError(VideoWatermarkError):
    """无效URL异常"""
    
    def __init__(self, message: str = "请输入正确的链接"):
        super().__init__(message, status_code=103)


class APINotAvailableError(VideoWatermarkError):
    """接口不可用异常"""
    
    def __init__(self, message: str = "接口不存在/暂停使用"):
        super().__init__(message, status_code=104)


class DataStructureError(VideoWatermarkError):
    """数据结构异常"""
    
    def __init__(self, message: str = "数据结构异常"):
        super().__init__(message, status_code=107)


class MemberAPIError(VideoWatermarkError):
    """会员接口异常"""
    
    def __init__(self, message: str = "会员接口不存在"):
        super().__init__(message, status_code=108)


class APIClosedError(VideoWatermarkError):
    """接口被关闭异常"""
    
    def __init__(self, message: str = "接口被系统管理员关闭"):
        super().__init__(message, status_code=109)


class InsufficientQuotaError(VideoWatermarkError):
    """次数不足异常"""
    
    def __init__(self, message: str = "次数不足，请升级VIP等级或明天再试"):
        super().__init__(message, status_code=110)


class ParseFailedError(VideoWatermarkError):
    """解析失败异常"""
    
    def __init__(self, message: str = "解析失败"):
        super().__init__(message, status_code=113)


class InsufficientLevelError(VideoWatermarkError):
    """会员等级不足异常"""
    
    def __init__(self, message: str = "会员等级不足"):
        super().__init__(message, status_code=115)


def create_exception_by_status_code(status_code: int, message: str = None) -> VideoWatermarkError:
    """根据状态码创建对应的异常实例
    
    Args:
        status_code: API返回的状态码
        message: 自定义错误消息
        
    Returns:
        对应的异常实例
    """
    status_code_map = {
        103: InvalidURLError,
        104: APINotAvailableError,
        107: DataStructureError,
        108: MemberAPIError,
        109: APIClosedError,
        110: InsufficientQuotaError,
        113: ParseFailedError,
        115: InsufficientLevelError,
    }
    
    exception_class = status_code_map.get(status_code, VideoWatermarkError)
    
    # 使用默认消息或自定义消息
    default_messages = {
        103: "请输入正确的链接",
        104: "接口不存在/暂停使用",
        107: "数据结构异常",
        108: "会员接口不存在",
        109: "接口被系统管理员关闭",
        110: "次数不足，请升级VIP等级或明天再试",
        113: "解析失败",
        115: "会员等级不足",
    }
    
    error_message = message or default_messages.get(status_code, f"未知错误 (状态码: {status_code})")
    
    return exception_class(error_message)