#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频去水印交互式工具 - 改进版

增加了更好的错误处理、备用API地址和模拟功能。
"""

import sys
import os
import json
import webbrowser
import time
import requests
import urllib.parse
from typing import Optional, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src import URLParser
    from src.exceptions import VideoWatermarkError
except ImportError:
    print("❌ 无法导入必要的模块，请确保在正确的目录中运行此脚本")
    sys.exit(1)


class ImprovedVideoWatermarkClient:
    """改进的视频去水印API客户端"""
    
    def __init__(self):
        """初始化客户端，配置多个API地址"""
        self.client_id = "demo_client_id_12345"
        self.client_secret_key = "demo_secret_key_abcdef123456789"
        
        # 配置多个API地址，按优先级排序
        self.api_endpoints = [
            "https://api.example.com/video/dsp",  # 主要API地址
            "https://backup-api.example.com/dsp",  # 备用API地址
            "http://api.example.com/video/dsp",   # HTTP版本
            "https://api.fallback.com/dsp"        # 备用域名
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def build_api_url(self, video_url: str, base_url: str) -> str:
        """构建API请求URL"""
        return f"{base_url}/{self.client_secret_key}/{self.client_id}/?url={video_url}"
    
    def test_api_connectivity(self, base_url: str) -> bool:
        """测试API连接性"""
        try:
            test_url = self.build_api_url("https://v.douyin.com/test/", base_url)
            response = self.session.get(test_url, timeout=5)
            return response.status_code != 404
        except:
            return False
    
    def remove_watermark(self, video_url: str, timeout: int = 30) -> Dict[str, Any]:
        """去除视频水印，尝试多个API地址"""
        last_error = None
        
        for i, base_url in enumerate(self.api_endpoints):
            try:
                # print(f"🔄 尝试API地址 {i+1}/{len(self.api_endpoints)}: {base_url}")  # 隐藏详细尝试信息
                
                # 测试连接性
                if not self.test_api_connectivity(base_url):
                    # print(f"⚠️ API地址 {base_url} 不可用，尝试下一个...")  # 隐藏详细尝试信息
                    continue
                
                api_url = self.build_api_url(video_url, base_url)
                response = self.session.get(api_url, timeout=timeout)
                response.raise_for_status()
                
                # 解析响应
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    print(f"⚠️ API地址 {base_url} 返回无效JSON，尝试下一个...")
                    continue
                
                # 检查响应状态
                if not isinstance(data, dict):
                    print(f"⚠️ API地址 {base_url} 返回无效数据结构，尝试下一个...")
                    continue
                
                # 处理API错误状态码
                if 'code' in data and data['code'] != 200:
                    status_code = data['code']
                    message = data.get('msg', f"API错误 (状态码: {status_code})")
                    
                    # 对于某些错误，不尝试其他API
                    if status_code in [103, 108, 109, 115]:
                        raise VideoWatermarkError(message, status_code)
                    
                    # print(f"⚠️ API地址 {base_url} 返回错误: {message}，尝试下一个...")  # 隐藏详细尝试信息
                    last_error = VideoWatermarkError(message, status_code)
                    continue
                
                # 验证成功响应的数据结构
                if 'data' not in data:
                    # print(f"⚠️ API地址 {base_url} 响应缺少数据字段，尝试下一个...")  # 隐藏详细尝试信息
                    continue
                
                video_data = data['data']
                
                # 检查必要字段
                required_fields = ['url', 'title', 'cover']
                for field in required_fields:
                    if field not in video_data:
                        # print(f"⚠️ API地址 {base_url} 响应缺少字段 {field}，尝试下一个...")  # 隐藏详细尝试信息
                        continue
                
                # print(f"✅ API地址 {base_url} 响应成功")  # 隐藏成功信息
                return {
                    'success': True,
                    'video_url': video_data['url'],
                    'title': video_data['title'],
                    'cover_url': video_data['cover'],
                    'raw_data': data,
                    'api_used': base_url
                }
                
            except VideoWatermarkError:
                # 重新抛出我们自己的异常
                raise
            except requests.exceptions.Timeout:
                # print(f"⚠️ API地址 {base_url} 请求超时，尝试下一个...")  # 隐藏详细尝试信息
                last_error = VideoWatermarkError("请求超时")
            except requests.exceptions.ConnectionError:
                # print(f"⚠️ API地址 {base_url} 连接错误，尝试下一个...")  # 隐藏详细尝试信息
                last_error = VideoWatermarkError("网络连接错误")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # print(f"⚠️ API地址 {base_url} 不存在，尝试下一个...")  # 隐藏详细尝试信息
                    last_error = VideoWatermarkError("API地址不存在")
                elif e.response.status_code == 500:
                    # print(f"⚠️ API地址 {base_url} 服务器错误，尝试下一个...")  # 隐藏详细尝试信息
                    last_error = VideoWatermarkError("服务器内部错误")
                else:
                    # print(f"⚠️ API地址 {base_url} HTTP错误 {e.response.status_code}，尝试下一个...")  # 隐藏详细尝试信息
                    last_error = VideoWatermarkError(f"HTTP错误: {e.response.status_code}")
            except Exception as e:
                # print(f"⚠️ API地址 {base_url} 未知错误: {str(e)}，尝试下一个...")  # 隐藏详细尝试信息
                last_error = VideoWatermarkError(f"请求异常: {str(e)}")
        
        # 所有API地址都尝试失败
        if last_error:
            raise last_error
        else:
            raise VideoWatermarkError("所有API地址都不可用")
    
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


class MockVideoWatermarkClient:
    """模拟视频去水印API客户端，用于演示和测试"""
    
    def remove_watermark(self, video_url: str, timeout: int = 30) -> Dict[str, Any]:
        """模拟去除视频水印"""
        print("🔄 使用模拟API进行演示...")
        
        # 模拟处理时间
        time.sleep(2)
        
        # 根据URL生成模拟数据
        if "douyin.com" in video_url:
            title = "抖音视频 - 模拟演示"
            video_url_result = "https://example.com/douyin_video_no_watermark.mp4"
            cover_url = "https://example.com/douyin_cover.jpg"
        elif "kuaishou.com" in video_url:
            title = "快手视频 - 模拟演示"
            video_url_result = "https://example.com/kuaishou_video_no_watermark.mp4"
            cover_url = "https://example.com/kuaishou_cover.jpg"
        elif "xhslink.com" in video_url:
            title = "小红书视频 - 模拟演示"
            video_url_result = "https://example.com/xiaohongshu_video_no_watermark.mp4"
            cover_url = "https://example.com/xiaohongshu_cover.jpg"
        else:
            title = "未知平台视频 - 模拟演示"
            video_url_result = "https://example.com/video_no_watermark.mp4"
            cover_url = "https://example.com/cover.jpg"
        
        return {
            'success': True,
            'video_url': video_url_result,
            'title': title,
            'cover_url': cover_url,
            'raw_data': {
                'code': 200,
                'msg': 'success',
                'data': {
                    'url': video_url_result,
                    'title': title,
                    'cover': cover_url
                }
            },
            'api_used': 'Mock API (演示模式)',
            'note': '这是模拟数据，仅用于演示工具功能'
        }
    
    def close(self):
        """关闭会话"""
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class VideoWatermarkInteractiveTool:
    """视频去水印交互式工具类 - 改进版"""
    
    def __init__(self):
        """初始化交互式工具"""
        self.platforms = {
            "1": {
                "name": "抖音",
                "key": "douyin",
                "example": "https://v.douyin.com/3ir1Xw2ulGo/",
                "share_example": "4.33 复制打开抖音，看看【小鱼的作品】 https://v.douyin.com/3ir1Xw2ulGo/"
            },
            "2": {
                "name": "快手",
                "key": "kuaishou",
                "example": "https://v.kuaishou.com/nigsINQH",
                "share_example": "https://v.kuaishou.com/nigsINQH 111 该作品在快手被播放过1次"
            },
            "3": {
                "name": "小红书",
                "key": "xiaohongshu",
                "example": "http://xhslink.com/o/8KJF6Dy0t6l",
                "share_example": "Biu～～ http://xhslink.com/o/8KJF6Dy0t6l 复制后打开【小红书】查看笔记！"
            }
        }
        
        self.use_mock_api = False
    
    def display_banner(self):
        """显示程序横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                视频去水印交互式工具 - 改进版                    ║
║                                                              ║
║  支持平台：抖音、快手、小红书                                  ║
║  新特性：多API地址、模拟模式、增强错误处理                      ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def display_platform_menu(self):
        """显示平台选择菜单"""
        print("\n📱 请选择视频平台：")
        print("-" * 40)
        
        for key, platform in self.platforms.items():
            print(f"{key}. {platform['name']}")
        
        print("0. 退出程序")
        print("m. 切换到模拟模式（当前: " + ("模拟模式" if self.use_mock_api else "真实模式") + ")")
        print("-" * 40)
    
    def get_platform_choice(self) -> Optional[str]:
        """获取用户平台选择"""
        while True:
            try:
                choice = input("\n请输入选项数字 (0-3) 或 'm' 切换模式: ").strip()
                
                if choice.lower() == "m":
                    self.use_mock_api = not self.use_mock_api
                    mode = "模拟模式" if self.use_mock_api else "真实模式"
                    print(f"✅ 已切换到{mode}")
                    continue
                
                if choice == "0":
                    return None
                
                if choice in self.platforms:
                    return choice
                
                print("❌ 无效选项，请输入 0-3 之间的数字或 'm' 切换模式")
            except KeyboardInterrupt:
                print("\n\n👋 感谢使用，再见！")
                return None
            except EOFError:
                print("\n\n👋 感谢使用，再见！")
                return None
    
    def display_platform_info(self, platform_key: str):
        """显示平台信息"""
        platform = self.platforms[platform_key]
        mode_info = " (模拟演示)" if self.use_mock_api else ""
        print(f"\n📋 您选择了：{platform['name']}{mode_info}")
        print(f"🔗 链接示例：{platform['example']}")
        print(f"📝 分享文本示例：{platform['share_example']}")
        
        if self.use_mock_api:
            print("\n⚠️ 当前为模拟模式，将返回演示数据")
            print("💡 如需使用真实API，请输入 'm' 切换到真实模式")
    
    def get_video_url(self, platform_key: str) -> Optional[str]:
        """获取视频URL"""
        platform = self.platforms[platform_key]
        
        while True:
            print(f"\n📋 请粘贴{platform['name']}的分享链接或视频链接：")
            print("(提示：可以直接粘贴完整的分享文本，程序会自动提取链接)")
            print("输入 'q' 返回主菜单，输入 '0' 退出程序")
            
            try:
                user_input = input("\n链接: ").strip()
                
                if user_input.lower() == 'q':
                    return None
                elif user_input.lower() == '0':
                    print("\n👋 感谢使用，再见！")
                    sys.exit(0)
                
                if not user_input:
                    print("❌ 请输入链接")
                    continue
                
                # 尝试解析和验证URL
                try:
                    clean_url, detected_platform = URLParser.parse_and_validate(user_input)
                    
                    # 检查检测到的平台是否与选择的一致
                    if detected_platform != platform['key']:
                        print(f"⚠️ 警告：检测到的平台是{detected_platform}，但您选择的是{platform['key']}")
                        confirm = input("是否继续处理？(y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    
                    return clean_url
                
                except ValueError as e:
                    print(f"❌ 链接解析失败：{e}")
                    retry = input("是否重新输入？(y/n): ").strip().lower()
                    if retry != 'y':
                        return None
                
            except KeyboardInterrupt:
                print("\n\n👋 感谢使用，再见！")
                sys.exit(0)
            except EOFError:
                print("\n\n👋 感谢使用，再见！")
                sys.exit(0)
    
    def process_video(self, video_url: str, platform_key: str):
        """处理视频"""
        platform = self.platforms[platform_key]
        print(f"\n⏳ 正在处理{platform['name']}视频...")
        print(f"🔗 链接：{video_url}")
        
        try:
            # 选择客户端
            if self.use_mock_api:
                client = MockVideoWatermarkClient()
            else:
                client = ImprovedVideoWatermarkClient()
            
            with client:
                if self.use_mock_api:
                    print("🔄 正在使用模拟API进行演示...")
                else:
                    # print("🔄 正在尝试多个API地址...")  # 隐藏尝试信息
                    pass
                
                result = client.remove_watermark(
                    video_url, 
                    timeout=30
                )
                
                # 显示成功结果
                self.display_success_result(result, platform)
                
        except VideoWatermarkError as e:
            print(f"\n❌ 处理失败：{e.message}")
            if e.status_code:
                print(f"🔢 错误代码：{e.status_code}")
                
                # 根据错误代码提供建议
                error_suggestions = {
                    103: "请检查链接是否正确，确保复制了完整的分享内容",
                    104: "API服务暂时不可用，请稍后重试或尝试模拟模式",
                    107: "数据结构异常，请联系管理员",
                    108: "会员接口不存在，请检查账号状态",
                    109: "接口被管理员关闭，请联系客服",
                    110: "今日次数已用完，请明天再试、升级VIP或使用模拟模式",
                    113: "解析失败，请检查链接是否有效",
                    115: "会员等级不足，请升级会员"
                }
                
                suggestion = error_suggestions.get(e.status_code, "请稍后重试或尝试模拟模式")
                print(f"💡 建议：{suggestion}")
                
                # 如果是API不可用错误，提示切换到模拟模式
                if e.status_code in [104, 109] or "API地址不存在" in e.message:
                    print(f"\n💡 提示：您可以输入 'm' 切换到模拟模式进行演示")
                
        except Exception as e:
            print(f"\n❌ 未知错误：{str(e)}")
            print("💡 建议：请检查网络连接、稍后重试或尝试模拟模式")
    
    def display_success_result(self, result: dict, platform: dict):
        """显示成功结果"""
        print("\n" + "=" * 50)
        print("🎉 视频解析成功！")
        print("=" * 50)
        
        print(f"📹 标题：{result['title']}")
        print(f"🔗 无水印视频链接：{result['video_url']}")
        print(f"🖼️ 封面链接：{result['cover_url']}")
        
        if 'api_used' in result:
            print(f"🌐 使用的API：{result['api_used']}")
        
        if 'note' in result:
            print(f"📝 说明：{result['note']}")
        
        print("\n" + "-" * 50)
        print("📋 操作选项：")
        print("1. 下载视频到本地")
        print("2. 打开视频链接")
        print("3. 打开封面链接")
        print("4. 保存结果到文件")
        print("5. 复制视频链接到剪贴板")
        print("6. 返回主菜单")
        print("0. 退出程序")
        print("-" * 50)
        
        while True:
            try:
                choice = input("\n请选择操作 (0-6): ").strip()
                
                if choice == "0":
                    print("\n👋 感谢使用，再见！")
                    sys.exit(0)
                elif choice == "1":
                    self.download_video(result['video_url'], result['title'])
                    break
                elif choice == "2":
                    self.open_url(result['video_url'])
                    break
                elif choice == "3":
                    self.open_url(result['cover_url'])
                    break
                elif choice == "4":
                    self.save_result_to_file(result, platform)
                    break
                elif choice == "5":
                    self.copy_to_clipboard(result['video_url'])
                    break
                elif choice == "6":
                    break
                else:
                    print("❌ 无效选项，请输入 0-6 之间的数字")
                    
            except KeyboardInterrupt:
                print("\n\n👋 感谢使用，再见！")
                sys.exit(0)
            except EOFError:
                print("\n\n👋 感谢使用，再见！")
                sys.exit(0)
    
    def open_url(self, url: str):
        """打开URL"""
        try:
            print(f"🌐 正在打开链接：{url}")
            webbrowser.open(url)
            print("✅ 链接已在浏览器中打开")
        except Exception as e:
            print(f"❌ 打开链接失败：{str(e)}")
            print(f"🔗 请手动复制链接到浏览器：{url}")
    
    def save_result_to_file(self, result: dict, platform: dict):
        """保存结果到文件"""
        try:
            # 生成文件名
            safe_title = "".join(c for c in result['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            mode_prefix = "模拟_" if self.use_mock_api else ""
            filename = f"{mode_prefix}{platform['name']}_{safe_title}.json"
            
            # 准备保存数据
            save_data = {
                "platform": platform['name'],
                "title": result['title'],
                "video_url": result['video_url'],
                "cover_url": result['cover_url'],
                "raw_data": result['raw_data']
            }
            
            if 'api_used' in result:
                save_data['api_used'] = result['api_used']
            
            if 'note' in result:
                save_data['note'] = result['note']
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 结果已保存到文件：{filename}")
            
        except Exception as e:
            print(f"❌ 保存文件失败：{str(e)}")
    
    def copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        try:
            import pyperclip
            pyperclip.copy(text)
            print("✅ 链接已复制到剪贴板")
        except ImportError:
            print("⚠️ 需要安装 pyperclip 库才能使用剪贴板功能")
            print("🔗 请手动复制链接：")
            print(text)
        except Exception as e:
            print(f"❌ 复制到剪贴板失败：{str(e)}")
            print("🔗 请手动复制链接：")
            print(text)
    
    def download_video(self, video_url: str, title: str):
        """下载视频到本地"""
        try:
            # 创建下载目录
            download_dir = os.path.join(os.getcwd(), "downloads")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # 清理文件名中的非法字符
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_title:
                safe_title = f"video_{int(time.time())}"
            
            # 从URL中获取文件扩展名
            parsed_url = urllib.parse.urlparse(video_url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = ".mp4"  # 默认扩展名
            
            # 构建文件路径
            filename = f"{safe_title}{ext}"
            filepath = os.path.join(download_dir, filename)
            
            # 如果文件已存在，添加时间戳
            if os.path.exists(filepath):
                filename = f"{safe_title}_{int(time.time())}{ext}"
                filepath = os.path.join(download_dir, filename)
            
            print(f"🔄 开始下载视频...")
            print(f"   目标文件: {filepath}")
            
            # 下载文件
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r   下载进度: {progress:.1f}% ({downloaded}/{total_size} bytes)", end="")
            
            print(f"\n✅ 视频下载成功！")
            print(f"   文件位置: {filepath}")
            print(f"   文件大小: {downloaded} bytes")
            
            # 询问是否打开文件夹
            try:
                open_folder = input("\n是否打开下载文件夹？(y/n): ").strip().lower()
                if open_folder in ['y', 'yes', '是']:
                    if sys.platform == 'win32':
                        os.startfile(download_dir)
                    elif sys.platform == 'darwin':
                        os.system(f'open "{download_dir}"')
                    else:
                        os.system(f'xdg-open "{download_dir}"')
            except KeyboardInterrupt:
                pass
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 下载失败：网络错误 - {str(e)}")
        except PermissionError:
            print(f"❌ 下载失败：权限不足，请检查目录权限")
        except Exception as e:
            print(f"❌ 下载失败：{str(e)}")
    
    def run(self):
        """运行交互式工具"""
        self.display_banner()
        
        while True:
            try:
                self.display_platform_menu()
                platform_choice = self.get_platform_choice()
                
                if platform_choice is None:
                    break
                
                self.display_platform_info(platform_choice)
                video_url = self.get_video_url(platform_choice)
                
                if video_url is None:
                    continue
                
                self.process_video(video_url, platform_choice)
                
                # 询问是否继续
                print("\n" + "=" * 50)
                continue_choice = input("是否继续处理其他视频？(y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("\n👋 感谢使用，再见！")
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 感谢使用，再见！")
                break
            except EOFError:
                print("\n\n👋 感谢使用，再见！")
                break
            except Exception as e:
                print(f"\n❌ 发生未知错误：{str(e)}")
                print("💡 程序将重新启动...")
                continue


def main():
    """主函数"""
    try:
        tool = VideoWatermarkInteractiveTool()
        tool.run()
    except Exception as e:
        print(f"❌ 程序启动失败：{str(e)}")
        print("💡 请检查程序文件是否完整")
        sys.exit(1)


if __name__ == "__main__":
    main()