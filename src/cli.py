"""
命令行界面模块

提供用户友好的命令行交互界面。
"""

import argparse
import sys
from typing import Optional
try:
    from .api_client import VideoWatermarkClient
    from .url_parser import URLParser
    from .exceptions import VideoWatermarkError
except ImportError:
    from api_client import VideoWatermarkClient
    from url_parser import URLParser
    from exceptions import VideoWatermarkError


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器
    
    Returns:
        配置好的ArgumentParser实例
    """
    parser = argparse.ArgumentParser(
        description="视频去水印工具 - 支持抖音、快手、小红书等平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s "https://v.douyin.com/3ir1Xw2ulGo/"
  %(prog)s "4.33 复制打开抖音，看看【小鱼的作品】 https://v.douyin.com/3ir1Xw2ulGo/"
  %(prog)s --url "https://v.kuaishou.com/nigsINQH" --output result.json
  %(prog)s --url "http://xhslink.com/o/8KJF6Dy0t6l" --timeout 60

支持的平台:
  - 抖音: https://v.douyin.com/...
  - 快手: https://v.kuaishou.com/...
  - 小红书: http://xhslink.com/...
        """
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="视频链接或包含链接的分享文本"
    )
    
    parser.add_argument(
        "--url", "-u",
        dest="url_option",
        help="视频链接或包含链接的分享文本"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（JSON格式），不指定则打印到控制台"
    )
    
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="API请求超时时间（秒），默认30秒"
    )
    
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=3,
        help="失败重试次数，默认3次"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息"
    )
    
    parser.add_argument(
        "--list-platforms",
        action="store_true",
        help="列出所有支持的平台"
    )
    
    return parser


def print_success_info(result: dict, verbose: bool = False):
    """打印成功信息
    
    Args:
        result: API返回的结果
        verbose: 是否显示详细信息
    """
    print("✅ 视频解析成功!")
    print(f"📹 标题: {result['title']}")
    print(f"🔗 无水印视频链接: {result['video_url']}")
    print(f"🖼️ 封面链接: {result['cover_url']}")
    
    if verbose:
        print("\n📋 详细信息:")
        print(f"原始响应数据: {result['raw_data']}")


def print_error_info(error: VideoWatermarkError, verbose: bool = False):
    """打印错误信息
    
    Args:
        error: 异常对象
        verbose: 是否显示详细信息
    """
    print(f"❌ 错误: {error.message}")
    
    if error.status_code:
        print(f"🔢 状态码: {error.status_code}")
    
    if verbose:
        print(f"📋 异常类型: {type(error).__name__}")


def save_result_to_file(result: dict, file_path: str):
    """保存结果到文件
    
    Args:
        result: 要保存的结果
        file_path: 文件路径
    """
    import json
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"📁 结果已保存到: {file_path}")
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")
        sys.exit(1)


def list_supported_platforms():
    """列出所有支持的平台"""
    platforms = URLParser.get_supported_platforms()
    
    print("📱 支持的平台:")
    for platform, config in platforms.items():
        platform_names = {
            "douyin": "抖音",
            "kuaishou": "快手",
            "xiaohongshu": "小红书"
        }
        
        name = platform_names.get(platform, platform)
        example = config["example"]
        print(f"  - {name}: {example}")


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 处理--list-platforms参数
    if args.list_platforms:
        list_supported_platforms()
        return
    
    # 获取URL参数
    url = args.url or args.url_option
    if not url:
        parser.print_help()
        print("\n❌ 错误: 请提供视频链接")
        sys.exit(1)
    
    try:
        # 解析和验证URL
        if args.verbose:
            print(f"🔍 解析URL: {url}")
        
        clean_url, platform = URLParser.parse_and_validate(url)
        
        if args.verbose:
            platform_names = {
                "douyin": "抖音",
                "kuaishou": "快手",
                "xiaohongshu": "小红书"
            }
            platform_name = platform_names.get(platform, platform)
            print(f"📱 识别平台: {platform_name}")
            print(f"🔗 清理后URL: {clean_url}")
        
        # 调用API去除水印
        with VideoWatermarkClient() as client:
            if args.verbose:
                print(f"⏳ 正在调用API...")
                print(f"🔄 最大重试次数: {args.retries}")
                print(f"⏱️ 超时时间: {args.timeout}秒")
            
            result = client.remove_watermark_with_retry(
                clean_url, 
                max_retries=args.retries,
                timeout=args.timeout
            )
            
            # 输出结果
            if args.output:
                save_result_to_file(result, args.output)
            else:
                print_success_info(result, args.verbose)
    
    except VideoWatermarkError as e:
        print_error_info(e, args.verbose)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()