#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频去水印工具 - PyQt6 GUI版本

采用扁平玻璃化设计风格的用户界面
"""

import sys
import os
import json
import webbrowser
import time
import requests
import urllib.parse
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QProgressBar, QMessageBox, QFrame, QScrollArea, QCheckBox, QTabWidget,
    QSpinBox, QFileDialog, QGroupBox, QRadioButton, QButtonGroup,
    QSplitter, QStatusBar, QMenuBar, QToolBar, QSlider
)
from PyQt6.QtGui import QAction, QFont, QIcon, QPixmap, QPalette, QColor, QLinearGradient, QPainter, QBrush, QPen, QRegion, QBitmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize, QPoint

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src import URLParser
    from src.exceptions import VideoWatermarkError
except ImportError:
    print("❌ 无法导入必要的模块，请确保在正确的目录中运行此脚本")
    sys.exit(1)


class GlassEffectWidget(QWidget):
    """玻璃效果基础组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        """绘制玻璃效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建圆角矩形路径
        rect = self.rect()
        radius = 15
        path = QPainter.Path()
        path.addRoundedRect(rect, radius, radius)
        
        # 设置玻璃效果背景
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(255, 255, 255, 30))
        gradient.setColorAt(1, QColor(255, 255, 255, 10))
        
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制边框
        pen = QPen(QColor(255, 255, 255, 60), 1)
        painter.setPen(pen)
        painter.drawPath(path)


class ModernButton(QPushButton):
    """现代化按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 149, 237, 180);
                border: none;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(100, 149, 237, 220);
            }
            QPushButton:pressed {
                background-color: rgba(100, 149, 237, 150);
            }
            QPushButton:disabled {
                background-color: rgba(150, 150, 150, 100);
                color: rgba(255, 255, 255, 150);
            }
        """)


class ModernLineEdit(QLineEdit):
    """现代化输入框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 40);
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
                selection-background-color: rgba(100, 149, 237, 100);
            }
            QLineEdit:focus {
                border: 1px solid rgba(100, 149, 237, 180);
                background-color: rgba(255, 255, 255, 30);
            }
        """)


class ModernComboBox(QComboBox):
    """现代化下拉框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 40);
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
                min-width: 150px;
            }
            QComboBox:hover {
                border: 1px solid rgba(100, 149, 237, 180);
                background-color: rgba(255, 255, 255, 30);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid rgba(255, 255, 255, 150);
            }
            QComboBox QAbstractItemView {
                background-color: rgba(30, 30, 30, 240);
                border: 1px solid rgba(255, 255, 255, 40);
                color: white;
                selection-background-color: rgba(100, 149, 237, 100);
                border-radius: 8px;
                padding: 5px;
            }
        """)


class ExpandableResultArea(QWidget):
    """结果区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标题栏 - 只保留标题，移除展开按钮
        title_layout = QHBoxLayout()
        
        title_label = QLabel("处理结果")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 内容区域 - 直接显示，不再有展开/收起功能
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建一个包含标题、封面图片和按钮的容器
        result_container = QWidget()
        result_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        container_layout = QVBoxLayout(result_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        
        # 视频标题
        self.title_label = QLabel("视频标题")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
                background-color: rgba(255, 255, 255, 15);
                border-radius: 8px;
            }
        """)
        self.title_label.setWordWrap(True)
        container_layout.addWidget(self.title_label)
        
        # 封面图片
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 5px;
            }
        """)
        self.cover_label.setMinimumHeight(200)
        self.cover_label.setText("封面图片")
        container_layout.addWidget(self.cover_label)
        
        # 操作按钮区域 - 横向排列
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        buttons_layout.setSpacing(10)
        
        self.download_button = ModernButton("下载视频")
        self.download_button.setEnabled(False)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 149, 237, 180);
                border: none;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(100, 149, 237, 220);
            }
            QPushButton:pressed {
                background-color: rgba(100, 149, 237, 150);
            }
            QPushButton:disabled {
                background-color: rgba(150, 150, 150, 100);
                color: rgba(255, 255, 255, 150);
            }
        """)
        buttons_layout.addWidget(self.download_button)
        
        self.open_video_button = ModernButton("打开视频")
        self.open_video_button.setEnabled(False)
        self.open_video_button.setStyleSheet(self.download_button.styleSheet())
        buttons_layout.addWidget(self.open_video_button)
        
        self.open_cover_button = ModernButton("打开封面")
        self.open_cover_button.setEnabled(False)
        self.open_cover_button.setStyleSheet(self.download_button.styleSheet())
        buttons_layout.addWidget(self.open_cover_button)
        
        self.copy_link_button = ModernButton("复制链接")
        self.copy_link_button.setEnabled(False)
        self.copy_link_button.setStyleSheet(self.download_button.styleSheet())
        buttons_layout.addWidget(self.copy_link_button)
        
        buttons_layout.addStretch()
        
        container_layout.addLayout(buttons_layout)
        content_layout.addWidget(result_container)
        layout.addLayout(content_layout)
        
    def set_result(self, result):
        """设置结果"""
        self.current_result = result
        
        # 设置标题
        self.title_label.setText(result['title'])
        
        # 加载并显示封面图片
        self.load_cover_image(result['cover_url'])
        
        # 启用按钮
        self.enable_buttons()
        
    def load_cover_image(self, cover_url):
        """加载封面图片"""
        try:
            # 创建网络请求
            import requests
            from PyQt6.QtGui import QPixmap
            
            response = requests.get(cover_url, timeout=10)
            if response.status_code == 200:
                # 从响应数据创建QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                # 缩放图片以适应标签大小，保持宽高比
                scaled_pixmap = pixmap.scaled(
                    self.cover_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 显示图片
                self.cover_label.setPixmap(scaled_pixmap)
            else:
                self.cover_label.setText("无法加载封面图片")
        except Exception as e:
            print(f"加载封面图片失败: {e}")
            self.cover_label.setText("封面图片加载失败")
        
    def get_result_text(self):
        """获取结果文本"""
        return getattr(self, 'current_result', {})
        
    def enable_buttons(self):
        """启用所有按钮"""
        self.download_button.setEnabled(True)
        self.open_video_button.setEnabled(True)
        self.open_cover_button.setEnabled(True)
        self.copy_link_button.setEnabled(True)
        
    def disable_buttons(self):
        """禁用所有按钮"""
        self.download_button.setEnabled(False)
        self.open_video_button.setEnabled(False)
        self.open_cover_button.setEnabled(False)
        self.copy_link_button.setEnabled(False)


class ModernTextEdit(QTextEdit):
    """现代化文本编辑框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 40);
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
                selection-background-color: rgba(100, 149, 237, 100);
            }
            QTextEdit:focus {
                border: 1px solid rgba(100, 149, 237, 180);
                background-color: rgba(255, 255, 255, 30);
            }
        """)


class VideoProcessThread(QThread):
    """视频处理线程"""
    
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, video_url, platform_key):
        super().__init__()
        self.video_url = video_url
        self.platform_key = platform_key
        
    def run(self):
        """执行视频处理"""
        try:
            self.status_updated.emit("正在初始化...")
            self.progress_updated.emit(10)
            
            # 选择客户端
            client = ImprovedVideoWatermarkClient()
            self.status_updated.emit("连接API服务器...")
            
            self.progress_updated.emit(30)
            
            with client:
                self.status_updated.emit("正在解析视频链接...")
                self.progress_updated.emit(50)
                
                result = client.remove_watermark(
                    self.video_url, 
                    timeout=30
                )
                
                self.status_updated.emit("视频解析成功！")
                self.progress_updated.emit(100)
                
                self.result_ready.emit(result)
                
        except VideoWatermarkError as e:
            self.error_occurred.emit(f"处理失败：{e.message}")
        except Exception as e:
            self.error_occurred.emit(f"未知错误：{str(e)}")


class ImprovedVideoWatermarkClient:
    """改进的视频去水印API客户端"""
    
    def __init__(self):
        """初始化客户端，配置多个API地址"""
        self.client_id = "202037162"
        self.client_secret_key = "32CAF695EED14BA145512443BBB3229C4501F22384B8997806"
        
        # 配置多个API地址，按优先级排序
        self.api_endpoints = [
            "https://qsy.ppt6.top/api/dsp/",  # 主要API地址
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
                # 测试连接性
                if not self.test_api_connectivity(base_url):
                    continue
                
                api_url = self.build_api_url(video_url, base_url)
                response = self.session.get(api_url, timeout=timeout)
                response.raise_for_status()
                
                # 解析响应
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    continue
                
                # 检查响应状态
                if not isinstance(data, dict):
                    continue
                
                # 处理API错误状态码
                if 'code' in data and data['code'] != 200:
                    status_code = data['code']
                    message = data.get('msg', f"API错误 (状态码: {status_code})")
                    
                    # 对于某些错误，不尝试其他API
                    if status_code in [103, 108, 109, 115]:
                        raise VideoWatermarkError(message, status_code)
                    
                    last_error = VideoWatermarkError(message, status_code)
                    continue
                
                # 验证成功响应的数据结构
                if 'data' not in data:
                    continue
                
                video_data = data['data']
                
                # 检查必要字段
                required_fields = ['url', 'title', 'cover']
                for field in required_fields:
                    if field not in video_data:
                        continue
                
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
                last_error = VideoWatermarkError("请求超时")
            except requests.exceptions.ConnectionError:
                last_error = VideoWatermarkError("网络连接错误")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    last_error = VideoWatermarkError("API地址不存在")
                elif e.response.status_code == 500:
                    last_error = VideoWatermarkError("服务器内部错误")
                else:
                    last_error = VideoWatermarkError(f"HTTP错误: {e.response.status_code}")
            except Exception as e:
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


class VideoWatermarkGUI(QMainWindow):
    """视频去水印GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频去水印工具 - 现代化界面")
        self.setMinimumSize(900, 850)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 支持的平台
        self.platforms = {
            "抖音": {
                "key": "douyin",
                "example": "https://v.douyin.com/3ir1Xw2ulGo/",
                "share_example": "4.33 复制打开抖音，看看【小鱼的作品】 https://v.douyin.com/3ir1Xw2ulGo/"
            },
            "快手": {
                "key": "kuaishou",
                "example": "https://v.kuaishou.com/nigsINQH",
                "share_example": "https://v.kuaishou.com/nigsINQH 111 该作品在快手被播放过1次"
            },
            "小红书": {
                "key": "xiaohongshu",
                "example": "http://xhslink.com/o/8KJF6Dy0t6l",
                "share_example": "Biu～～ http://xhslink.com/o/8KJF6Dy0t6l 复制后打开【小红书】查看笔记！"
            }
        }
        
        self.process_thread = None
        self.current_result = None
        
        self.init_ui()
        self.setup_connections()
        
        # 设置窗口拖动
        self.drag_pos = None
        
    def init_ui(self):
        """初始化UI界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建一个统一的容器，包含所有内容
        unified_container = QWidget()
        unified_container.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 180);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 15px;
            }
        """)
        
        container_layout = QVBoxLayout(unified_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题栏 - 无边框，只是标题和按钮
        title_layout = QHBoxLayout()
        
        # 标题
        title = QLabel("视频去水印工具")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 控制按钮
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: none;
                color: white;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 100, 100, 100);
                border: none;
                color: white;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 150);
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 20);
                color: white;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: rgba(100, 149, 237, 150);
            }
            QTabBar::tab:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        
        # 主处理选项卡
        main_tab = self.create_main_tab()
        tab_widget.addTab(main_tab, "视频处理")
        
        # 设置选项卡
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "设置")
        
        # 关于选项卡
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "关于")
        
        container_layout.addWidget(tab_widget)
        
        # 状态栏 - 简化为底部一行
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 10, 0, 0)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 180);
                font-size: 12px;
            }
        """)
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 模式指示器
        self.mode_indicator = QLabel("真实模式")
        self.mode_indicator.setStyleSheet("""
            QLabel {
                color: rgba(100, 255, 100, 180);
                font-size: 12px;
                padding: 3px 8px;
                border-radius: 10px;
                background-color: rgba(100, 255, 100, 30);
            }
        """)
        status_layout.addWidget(self.mode_indicator)
        
        container_layout.addLayout(status_layout)
        
        # 将统一容器添加到中央窗口部件
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(unified_container)
        
    def create_title_bar(self):
        """创建标题栏"""
        title_bar = QFrame()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 180);
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border: 1px solid rgba(255, 255, 255, 20);
                border-bottom: none;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 标题
        title = QLabel("视频去水印工具")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 控制按钮
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: none;
                color: white;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 100, 100, 100);
                border: none;
                color: white;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 150);
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return title_bar
    
    def create_content_area(self):
        """创建主要内容区域"""
        content_area = QFrame()
        content_area.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 180);
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border: 1px solid rgba(255, 255, 255, 20);
                border-top: none;
                border-bottom: none;
            }
        """)
        
        layout = QVBoxLayout(content_area)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 20);
                background-color: rgba(30, 30, 30, 100);
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 20);
                color: white;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: rgba(100, 149, 237, 150);
            }
            QTabBar::tab:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        
        # 主处理选项卡
        main_tab = self.create_main_tab()
        tab_widget.addTab(main_tab, "视频处理")
        
        # 设置选项卡
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "设置")
        
        # 关于选项卡
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "关于")
        
        layout.addWidget(tab_widget)
        
        return content_area
    
    def create_main_tab(self):
        """创建主处理选项卡"""
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 平台选择区域
        platform_group = QGroupBox("选择平台")
        platform_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: rgba(255, 255, 255, 10);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
            }
        """)
        
        platform_layout = QHBoxLayout(platform_group)
        
        # 平台选择下拉框
        self.platform_combo = ModernComboBox()
        self.platform_combo.addItems(list(self.platforms.keys()))
        platform_layout.addWidget(QLabel("选择视频平台:"))
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        
        layout.addWidget(platform_group)
        
        # URL输入区域
        url_group = QGroupBox("视频链接")
        url_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: rgba(255, 255, 255, 10);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
            }
        """)
        
        url_layout = QVBoxLayout(url_group)
        
        # URL输入框
        self.url_input = ModernLineEdit("请粘贴视频分享链接或视频链接...")
        url_layout.addWidget(self.url_input)
        
        # 示例链接
        self.example_label = QLabel("示例链接: https://v.douyin.com/3ir1Xw2ulGo/")
        self.example_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 150);
                font-size: 12px;
                padding: 5px;
            }
        """)
        url_layout.addWidget(self.example_label)
        
        layout.addWidget(url_group)
        
        # 处理按钮
        self.process_button = ModernButton("开始处理")
        self.process_button.setFixedHeight(50)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 149, 237, 180);
                border: none;
                color: white;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(100, 149, 237, 220);
            }
            QPushButton:pressed {
                background-color: rgba(100, 149, 237, 150);
            }
            QPushButton:disabled {
                background-color: rgba(150, 150, 150, 100);
                color: rgba(255, 255, 255, 150);
            }
        """)
        layout.addWidget(self.process_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 20);
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: rgba(100, 149, 237, 180);
                border-radius: 5px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 结果显示区域
        self.result_area = ExpandableResultArea()
        self.result_area.setStyleSheet("""
            ExpandableResultArea {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        layout.addWidget(self.result_area)
        
        return main_tab
    
    def create_settings_tab(self):
        """创建设置选项卡"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        layout.setSpacing(20)
        
        # 下载设置组
        download_group = QGroupBox("下载设置")
        download_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: rgba(255, 255, 255, 10);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
            }
        """)
        
        download_layout = QVBoxLayout(download_group)
        
        # 下载目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("下载目录:"))
        
        self.download_dir_input = ModernLineEdit()
        self.download_dir_input.setPlaceholderText("选择下载目录...")
        self.download_dir_input.setText(os.path.expanduser("~/Downloads"))
        dir_layout.addWidget(self.download_dir_input)
        
        self.browse_button = ModernButton("浏览")
        self.browse_button.clicked.connect(self.browse_download_dir)
        dir_layout.addWidget(self.browse_button)
        
        download_layout.addLayout(dir_layout)
        
        layout.addWidget(download_group)
        layout.addStretch()
        
        return settings_tab
    
    def create_about_tab(self):
        """创建关于选项卡"""
        about_tab = QWidget()
        layout = QVBoxLayout(about_tab)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 应用图标和标题
        title_label = QLabel("视频去水印工具")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 开发者信息
        developer_label = QLabel("开发者：厉温")
        developer_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 180);
                font-size: 16px;
                padding: 10px;
            }
        """)
        layout.addWidget(developer_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # GitHub地址
        github_label = QLabel("GitHub地址：<a href='https://github.com/qianyi888666/python-Short-Video-Download-Without-Watermark/releases'>https://github.com/qianyi888666/python-Short-Video-Download-Without-Watermark/releases</a>")
        github_label.setOpenExternalLinks(True)
        github_label.setStyleSheet("""
            QLabel {
                color: rgba(100, 149, 237, 200);
                font-size: 14px;
                padding: 10px;
            }
            QLabel:hover {
                color: rgba(100, 149, 237, 255);
                text-decoration: underline;
            }
        """)
        layout.addWidget(github_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 描述信息
        desc_label = QLabel("一个现代化的视频去水印工具，支持抖音、快手、小红书等主流平台")
        desc_label.setWordWrap(True)
        desc_label.setMinimumWidth(500)
        desc_label.setMinimumHeight(60)
        desc_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                padding: 15px;
                line-height: 1.5;
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(desc_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 功能特性
        features_label = QLabel("主要特性:")
        features_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(features_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        features_text = QLabel("""
        • 支持抖音、快手、小红书等主流平台
        • 现代化扁平玻璃化UI设计
        • 多API地址自动切换
        • 视频下载功能
        """)
        features_text.setWordWrap(True)
        features_text.setMinimumWidth(400)
        features_text.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 14px;
                padding: 30px;
                line-height: 1.5;
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 8px;
            }
        """)
        layout.addWidget(features_text, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 版权信息
        copyright_label = QLabel("© 2026 视频去水印工具. 版本号：V2.0.0")
        copyright_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 120);
                font-size: 12px;
                padding: 20px;
            }
        """)
        layout.addWidget(copyright_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        
        return about_tab
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QFrame()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 180);
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 15px;
                border-bottom-right-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 20);
                border-top: none;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 180);
                font-size: 12px;
            }
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 模式指示器
        self.mode_indicator = QLabel("真实模式")
        self.mode_indicator.setStyleSheet("""
            QLabel {
                color: rgba(100, 255, 100, 180);
                font-size: 12px;
                padding: 3px 8px;
                border-radius: 10px;
                background-color: rgba(100, 255, 100, 30);
            }
        """)
        layout.addWidget(self.mode_indicator)
        
        return status_bar
    
    def setup_connections(self):
        """设置信号连接"""
        self.process_button.clicked.connect(self.start_processing)
        self.result_area.download_button.clicked.connect(self.download_video)
        self.result_area.open_video_button.clicked.connect(self.open_video_url)
        self.result_area.open_cover_button.clicked.connect(self.open_cover_url)
        self.result_area.copy_link_button.clicked.connect(self.copy_video_link)
        self.platform_combo.currentTextChanged.connect(self.update_example)
        
    def update_example(self, platform_name):
        """更新示例链接"""
        if platform_name in self.platforms:
            example = self.platforms[platform_name]["example"]
            self.example_label.setText(f"示例链接: {example}")
    
    def browse_download_dir(self):
        """浏览下载目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if dir_path:
            self.download_dir_input.setText(dir_path)
    
    def start_processing(self):
        """开始处理视频"""
        # 获取输入
        platform_name = self.platform_combo.currentText()
        video_url = self.url_input.text().strip()
        # 验证输入
        if not video_url:
            QMessageBox.warning(self, "输入错误", "请输入视频链接")
            return
        
        try:
            # 解析和验证URL
            clean_url, detected_platform = URLParser.parse_and_validate(video_url)
            
            # 检查平台是否匹配
            selected_platform = self.platforms[platform_name]["key"]
            if detected_platform != selected_platform:
                reply = QMessageBox.question(
                    self, 
                    "平台不匹配", 
                    f"检测到的平台是{detected_platform}，但您选择的是{selected_platform}。是否继续处理？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 禁用控件
            self.process_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.result_area.get_result_text().clear()
            self.result_area.disable_buttons()
            
            # 创建处理线程
            self.process_thread = VideoProcessThread(clean_url, selected_platform)
            self.process_thread.progress_updated.connect(self.update_progress)
            self.process_thread.result_ready.connect(self.handle_result)
            self.process_thread.error_occurred.connect(self.handle_error)
            self.process_thread.status_updated.connect(self.update_status)
            
            # 启动线程
            self.process_thread.start()
            
        except ValueError as e:
            QMessageBox.warning(self, "链接错误", f"链接解析失败：{e}")
        except Exception as e:
            QMessageBox.critical(self, "未知错误", f"发生未知错误：{str(e)}")
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(status)
    
    def handle_result(self, result):
        """处理结果"""
        self.current_result = result
        
        # 显示结果 - 只显示标题和封面图片
        self.result_area.set_result(result)
        
        # 启用结果按钮
        self.result_area.enable_buttons()
        
        # 恢复处理按钮
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 更新状态
        self.status_label.setText("处理完成")
        
        QMessageBox.information(self, "处理成功", "视频处理成功！")
    
    def handle_error(self, error_msg):
        """处理错误"""
        self.result_area.set_result(f"错误: {error_msg}")
        
        # 恢复处理按钮
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 更新状态
        self.status_label.setText("处理失败")
        
        QMessageBox.critical(self, "处理失败", error_msg)
    
    def download_video(self):
        """下载视频"""
        if not self.current_result:
            return
        
        video_url = self.current_result['video_url']
        title = self.current_result['title']
        download_dir = self.download_dir_input.text()
        
        try:
            # 获取下载目录
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # 构建文件名
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.mp4"
            filepath = os.path.join(download_dir, filename)
            
            # 下载文件
            self.status_label.setText("正在下载视频...")
            
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.status_label.setText(f"正在下载视频... {progress}%")
            
            self.status_label.setText("下载完成")
            
            # 询问是否打开文件夹
            reply = QMessageBox.question(
                self,
                "下载完成",
                f"视频已下载到: {filepath}\n\n是否打开所在文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if sys.platform == 'win32':
                    os.startfile(download_dir)
                elif sys.platform == 'darwin':
                    os.system(f'open "{download_dir}"')
                else:
                    os.system(f'xdg-open "{download_dir}"')
                    
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "下载失败", f"网络错误: {str(e)}")
        except PermissionError:
            QMessageBox.critical(self, "下载失败", "权限不足，请检查目录权限")
        except Exception as e:
            QMessageBox.critical(self, "下载失败", f"未知错误: {str(e)}")
    
    def open_video_url(self):
        """打开视频链接"""
        if not self.current_result:
            return
        
        video_url = self.current_result['video_url']
        try:
            webbrowser.open(video_url)
            self.status_label.setText("已在浏览器中打开视频链接")
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"无法打开链接: {str(e)}")
    
    def open_cover_url(self):
        """打开封面链接"""
        if not self.current_result:
            return
        
        cover_url = self.current_result['cover_url']
        try:
            webbrowser.open(cover_url)
            self.status_label.setText("已在浏览器中打开封面链接")
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"无法打开链接: {str(e)}")
    
    def copy_video_link(self):
        """复制视频链接"""
        if not self.current_result:
            return
        
        video_url = self.current_result['video_url']
        
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(video_url)
        
        self.status_label.setText("链接已复制到剪贴板")
        QMessageBox.information(self, "复制成功", "视频链接已复制到剪贴板")
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.drag_pos = None


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置全局样式
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30, 200))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45, 200))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(60, 60, 60, 200))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(100, 149, 237, 200))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(100, 149, 237, 180))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 100, 100))
    palette.setColor(QPalette.ColorRole.Link, QColor(100, 149, 237, 200))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 149, 237, 200))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    # 创建主窗口
    window = VideoWatermarkGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()