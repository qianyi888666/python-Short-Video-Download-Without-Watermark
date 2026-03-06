#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频去水印工具 - PyQt6 GUI版本

采用扁平玻璃化设计风格的用户界面
"""

import sys
import os
import json
import time
import requests
import urllib.parse
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QProgressBar, QMessageBox, QFrame, QScrollArea, QCheckBox,
    QSpinBox, QFileDialog, QGroupBox, QRadioButton, QButtonGroup,
    QSizePolicy, QDialog
)
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QLinearGradient, QPainter, QBrush, QPen
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
    """玻璃效果基础组件 - 新视觉风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        """绘制玻璃效果 - 磨砂质感"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建圆角矩形路径
        rect = self.rect()
        radius = 20
        path = QPainter.Path()
        path.addRoundedRect(rect, radius, radius)
        
        # 设置磨砂玻璃效果背景 - 温暖米白色调
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(250, 248, 245, 180))
        gradient.setColorAt(0.5, QColor(248, 245, 240, 160))
        gradient.setColorAt(1, QColor(245, 242, 238, 140))
        
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制柔和边框
        pen = QPen(QColor(255, 255, 255, 80), 1.5)
        painter.setPen(pen)
        painter.drawPath(path)


class ModernButton(QPushButton):
    """现代化按钮 - 新视觉风格"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 140, 0, 180);
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 140, 0, 220);
            }
            QPushButton:pressed {
                background-color: rgba(255, 140, 0, 150);
            }
            QPushButton:disabled {
                background-color: rgba(200, 200, 200, 100);
                color: rgba(100, 100, 100, 150);
            }
        """)


class ModernLineEdit(QLineEdit):
    """现代化输入框 - 新视觉风格"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(240, 235, 230, 0.6);
                border: none;
                color: #2c2c2c;
                padding: 0px 12px;
                border-radius: 8px;
                font-size: 15px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                selection-background-color: rgba(255, 140, 0, 100);
            }
            QLineEdit:focus {
                background-color: rgba(255, 250, 245, 0.8);
            }
            QLineEdit::placeholder {
                color: rgba(100, 100, 100, 150);
            }
        """)


class ModernComboBox(QComboBox):
    """现代化下拉框 - 新视觉风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: rgba(240, 235, 230, 0.6);
                border: none;
                color: #2c2c2c;
                padding: 0px 12px;
                border-radius: 8px;
                font-size: 15px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                min-width: 100px;
                max-width: 120px;
            }
            QComboBox:hover {
                background-color: rgba(255, 250, 245, 0.8);
            }
            QComboBox:focus {
                background-color: rgba(255, 250, 245, 0.9);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid rgba(100, 100, 100, 180);
            }
            QComboBox QAbstractItemView {
                background-color: rgba(255, 255, 255, 255);
                border: 2px solid rgba(200, 200, 200, 150);
                color: #2c2c2c;
                selection-background-color: rgba(255, 140, 0, 180);
                selection-color: white;
                border-radius: 8px;
                padding: 8px;
                font-size: 15px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                min-width: 100px;
                max-width: 120px;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(255, 140, 0, 0.15);
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(255, 140, 0, 180);
                color: white;
            }
        """)


class ExpandableResultArea(QWidget):
    """结果区域 - 新视觉风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI - 仅删除空白拉伸，卡片/大小/左右区域完全不变"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # 保持原间距不变
        
        # 设置结果区域的尺寸策略，确保能够扩展填充空间
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 结果展示卡片
        result_card = QWidget()
        result_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        result_card.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 255);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(result_card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        # 卡片标题
        card_title = QLabel("处理结果")
        card_title.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 17px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                background-color: transparent;
                border: none;
            }
        """)
        card_layout.addWidget(card_title)
        
        # 两列布局
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(16)
        
        # 左列 - 文本框和按钮（60%宽度）
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(12)
        
        # 视频文案 - 白色圆角文本框
        self.title_label = QLabel("视频标题")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 15px;
                font-weight: 600;
                padding: 12px;
                background-color: rgba(255, 255, 255, 255);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
        """)
        self.title_label.setWordWrap(True)
        left_column_layout.addWidget(self.title_label)
        
        # 功能按钮 - 水平排列
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.download_button = ModernButton("下载内容")
        self.download_button.setEnabled(False)
        self.download_button.setFixedHeight(36)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 140, 0, 180);
                border: none;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 140, 0, 220);
            }
            QPushButton:pressed {
                background-color: rgba(255, 140, 0, 150);
            }
            QPushButton:disabled {
                background-color: rgba(200, 200, 200, 100);
                color: rgba(100, 100, 100, 150);
            }
        """)
        buttons_layout.addWidget(self.download_button)
        
        self.open_cover_button = ModernButton("打开封面")
        self.open_cover_button.setEnabled(False)
        self.open_cover_button.setFixedHeight(36)
        self.open_cover_button.setStyleSheet(self.download_button.styleSheet())
        buttons_layout.addWidget(self.open_cover_button)
        
        self.copy_link_button = ModernButton("复制链接")
        self.copy_link_button.setEnabled(False)
        self.copy_link_button.setFixedHeight(36)
        self.copy_link_button.setStyleSheet(self.download_button.styleSheet())
        buttons_layout.addWidget(self.copy_link_button)
        
        left_column_layout.addLayout(buttons_layout)
        columns_layout.addWidget(left_column, stretch=6)
        
        # 右列 - 封面预览（40%宽度）
        right_column = QWidget()
        right_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        
        # 封面图片容器
        cover_container = QWidget()
        cover_container.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 235, 230, 0.5);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
            }
        """)
        cover_layout = QVBoxLayout(cover_container)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        
        # 封面图片
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setScaledContents(False)
        self.cover_label.setMinimumSize(280, 200)
        self.cover_label.setText("封面图片")
        self.cover_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 15px;
                font-weight: 600;
                background-color: transparent;
            }
        """)
        cover_layout.addWidget(self.cover_label)
        
        right_column_layout.addWidget(cover_container)
        columns_layout.addWidget(right_column, stretch=4)
        
        card_layout.addLayout(columns_layout)
        layout.addWidget(result_card)
        
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
        """加载封面图片 - 保持宽高比适配显示"""
        try:
            # 创建网络请求
            import requests
            from PyQt6.QtGui import QPixmap
            
            response = requests.get(cover_url, timeout=10)
            if response.status_code == 200:
                # 从响应数据创建QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                # 获取封面标签的当前尺寸
                label_size = self.cover_label.size()
                
                # 缩放图片以保持宽高比，尽可能填充区域
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 显示图片，保持宽高比不变形
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
        self.open_cover_button.setEnabled(True)
        self.copy_link_button.setEnabled(True)
        
    def disable_buttons(self):
        """禁用所有按钮"""
        self.download_button.setEnabled(False)
        self.open_cover_button.setEnabled(False)
        self.copy_link_button.setEnabled(False)


class ImagePreviewDialog(QDialog):
    """图片预览窗口"""
    
    def __init__(self, image_url, parent=None):
        super().__init__(parent)
        self.image_url = image_url
        self.init_ui()
        self.load_image()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("封面图片预览")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: none;
            }
        """)
        self.image_label.setScaledContents(False)
        layout.addWidget(self.image_label)
        
        # 底部按钮栏
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 12, 16, 12)
        button_layout.setSpacing(12)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setFixedHeight(36)
        close_button.setMinimumWidth(120)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 140, 0, 180);
                border: none;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 140, 0, 220);
            }
            QPushButton:pressed {
                background-color: rgba(255, 140, 0, 150);
            }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        button_container = QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 235, 230, 0.8);
                border-top: 1px solid rgba(200, 200, 200, 150);
            }
        """)
        button_container.setLayout(button_layout)
        layout.addWidget(button_container)
        
    def load_image(self):
        """加载图片"""
        try:
            import requests
            from PyQt6.QtGui import QPixmap
            
            response = requests.get(self.image_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                # 获取窗口可用大小
                window_size = self.size()
                available_size = window_size - QSize(0, 60)
                
                # 缩放图片以适应窗口，保持宽高比
                scaled_pixmap = pixmap.scaled(
                    available_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("无法加载图片")
        except Exception as e:
            print(f"加载图片失败: {e}")
            self.image_label.setText("图片加载失败")
    
    def resizeEvent(self, event):
        """窗口大小改变时重新调整图片大小"""
        super().resizeEvent(event)
        if hasattr(self, 'image_label') and self.image_label.pixmap():
            self.load_image()


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, download_dir, parent=None):
        super().__init__(parent)
        self.download_dir = download_dir
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 300)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("下载设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c2c2c;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # 下载路径设置
        path_group = QGroupBox("下载内容保存地址")
        path_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c2c2c;
                border: 2px solid rgba(100, 149, 237, 150);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(15)
        
        # 当前路径显示
        current_label = QLabel("当前下载路径：")
        current_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #2c2c2c;
            }
        """)
        path_layout.addWidget(current_label)
        
        self.path_display = QLineEdit(self.download_dir)
        self.path_display.setReadOnly(True)
        self.path_display.setStyleSheet("""
            QLineEdit {
                background-color: rgba(240, 240, 240, 0.8);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: #2c2c2c;
            }
        """)
        path_layout.addWidget(self.path_display)
        
        # 浏览按钮
        browse_layout = QHBoxLayout()
        browse_layout.addStretch()
        
        self.browse_button = ModernButton("浏览")
        self.browse_button.setFixedWidth(120)
        self.browse_button.clicked.connect(self.browse_directory)
        browse_layout.addWidget(self.browse_button)
        
        path_layout.addLayout(browse_layout)
        layout.addWidget(path_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = ModernButton("保存")
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        cancel_button = ModernButton("取消")
        cancel_button.setFixedWidth(100)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            self.download_dir
        )
        
        if directory:
            # 转换路径格式，确保使用正确的路径分隔符
            directory = os.path.normpath(directory)
            
            # 验证目录权限
            if not self.validate_directory_permission(directory):
                QMessageBox.warning(
                    self,
                    "权限警告",
                    f"所选目录可能没有写入权限:\n{directory}\n\n建议选择其他目录，如：\n• 用户文档目录\n• 专门的下载目录\n• 桌面子目录"
                )
                return
            
            self.path_display.setText(directory)
            self.download_dir = directory
    
    def validate_directory_permission(self, directory):
        """验证目录权限"""
        try:
            # 检查目录是否存在
            if not os.path.exists(directory):
                # 尝试创建目录
                os.makedirs(directory, exist_ok=True)
            
            # 检查是否可写
            test_file = os.path.join(directory, '.permission_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except Exception:
                return False
        except Exception:
            return False
    
    def get_download_dir(self):
        """获取下载目录"""
        return self.download_dir


class ModernTextEdit(QTextEdit):
    """现代化文本编辑框 - 新视觉风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: rgba(240, 235, 230, 0.6);
                border: none;
                color: #2c2c2c;
                padding: 14px 18px;
                border-radius: 16px;
                font-size: 15px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                selection-background-color: rgba(255, 140, 0, 100);
            }
            QTextEdit:focus {
                background-color: rgba(255, 250, 245, 0.8);
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
                "name": "抖音",
                "example": "https://v.douyin.com/3ir1Xw2ulGo/",
                "share_example": "4.33 复制打开抖音，看看【小鱼的作品】 https://v.douyin.com/3ir1Xw2ulGo/"
            },
            "快手": {
                "key": "kuaishou",
                "name": "快手",
                "example": "https://v.kuaishou.com/nigsINQH",
                "share_example": "https://v.kuaishou.com/nigsINQH 111 该作品在快手被播放过1次"
            },
            "小红书": {
                "key": "xiaohongshu",
                "name": "小红书",
                "example": "http://xhslink.com/o/8KJF6Dy0t6l",
                "share_example": "Biu～～ http://xhslink.com/o/8KJF6Dy0t6l 复制后打开【小红书】查看笔记！"
            }
        }
        
        self.process_thread = None
        self.current_result = None
        
        # 配置管理
        self.config_file = os.path.join(os.getcwd(), 'config.json')
        self.download_dir = self.load_config()
        
        self.init_ui()
        self.setup_connections()
        
        # 设置窗口拖动
        self.drag_pos = None
        
    def init_ui(self):
        """初始化UI界面 - 左右分栏结构"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建一个统一的容器，包含所有内容
        unified_container = QWidget()
        unified_container.setStyleSheet("""
            QWidget {
                background-color: rgba(250, 248, 245, 0.95);
                border: 2px solid rgba(200, 200, 200, 150);
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(unified_container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(12)
        
        # 标题栏 - 窗口右上角按钮
        title_layout = QHBoxLayout()
        
        # 标题
        title = QLabel("视频去水印工具")
        title.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 24px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                background-color: transparent;
                border: none;
            }
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 控制按钮
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(36, 36)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(240, 235, 230, 0.8);
                border: none;
                color: #2c2c2c;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 140, 0, 0.3);
                color: rgba(255, 140, 0, 255);
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 100, 100, 0.2);
                border: none;
                color: #ff6464;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 0.4);
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # 主内容区 - 左右分栏
        main_content = QWidget()
        main_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_content_layout = QHBoxLayout(main_content)
        main_content_layout.setSpacing(16)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        # 移除 AlignTop，让内容能够正常扩展
        main_content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # 左侧侧边导航栏（20%宽度）
        left_sidebar = self.create_left_sidebar()
        main_content_layout.addWidget(left_sidebar, stretch=2)
        
        # 右侧主内容区（80%宽度）
        right_content = self.create_right_content()
        main_content_layout.addWidget(right_content, stretch=8)
        
        container_layout.addWidget(main_content)
        
        # 底部状态提示区
        status_area = self.create_status_area()
        container_layout.addWidget(status_area)
        
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
    
    def setup_connections(self):
        """设置信号连接"""
        self.process_button.clicked.connect(self.start_processing)
        self.result_area.download_button.clicked.connect(self.download_video)
        self.result_area.open_cover_button.clicked.connect(self.open_cover_url)
        self.result_area.copy_link_button.clicked.connect(self.copy_video_link)
        self.platform_combo.currentTextChanged.connect(self.update_example)
        
    def update_example(self, platform_name):
        """更新示例链接"""
        if hasattr(self, 'example_label') and platform_name in self.platforms:
            example = self.platforms[platform_name]["example"]
            self.example_label.setText(f"示例链接: {example}")
    
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
                # 获取平台的中文名称
                detected_name = detected_platform
                selected_name = selected_platform
                for plat_name, plat_info in self.platforms.items():
                    if plat_info["key"] == detected_platform:
                        detected_name = plat_info["name"]
                    if plat_info["key"] == selected_platform:
                        selected_name = plat_name
                
                reply = QMessageBox.question(
                    self, 
                    "平台不匹配", 
                    f"检测到的平台是{detected_name}，但您选择的是{selected_name}。是否继续处理？",
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
        pass
    
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
        
        # 显示"处理完成"提示在底部状态区
        self.completion_label.setVisible(True)
        
        QMessageBox.information(self, "处理成功", "视频处理成功！")
    
    def handle_error(self, error_msg):
        """处理错误"""
        self.result_area.set_result(f"错误: {error_msg}")
        
        # 恢复处理按钮
        self.process_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "处理失败", error_msg)
    
    def download_video(self):
        """下载视频"""
        if not self.current_result:
            return
        
        video_url = self.current_result['video_url']
        title = self.current_result['title']
        
        try:
            # 使用配置的下载目录，并规范化路径
            download_dir = os.path.normpath(self.download_dir)
            
            # 检查目录是否存在，不存在则创建
            if not os.path.exists(download_dir):
                try:
                    os.makedirs(download_dir, exist_ok=True)
                    print(f"创建下载目录: {download_dir}")
                except Exception as e:
                    error_msg = f"无法创建下载目录:\n{download_dir}\n\n错误: {str(e)}\n\n建议：\n• 选择其他目录\n• 检查父目录权限\n• 避免选择系统目录"
                    QMessageBox.critical(self, "下载失败", error_msg)
                    return
            
            # 检查目录是否可写
            if not os.access(download_dir, os.W_OK):
                error_msg = f"目录没有写入权限:\n{download_dir}\n\n可能原因：\n• 系统桌面目录有特殊权限\n• 目录被设置为只读\n• 需要管理员权限\n\n建议：\n• 选择用户文档目录\n• 选择专门的下载目录\n• 避免选择系统目录"
                QMessageBox.critical(self, "下载失败", error_msg)
                return
            
            # 构建文件名（处理特殊字符）
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_title:
                safe_title = "video"
            filename = f"{safe_title}.mp4"
            filepath = os.path.join(download_dir, filename)
            
            # 如果文件已存在，添加序号
            counter = 1
            while os.path.exists(filepath):
                filename = f"{safe_title}_{counter}.mp4"
                filepath = os.path.join(download_dir, filename)
                counter += 1
            
            # 下载文件
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
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
        except PermissionError as e:
            error_msg = f"权限不足，请检查目录权限:\n{download_dir}\n\n错误详情: {str(e)}\n\n建议：\n• 在设置中选择其他目录\n• 避免选择系统目录\n• 选择用户文档目录"
            QMessageBox.critical(self, "下载失败", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "下载失败", f"未知错误: {str(e)}")
    
    def open_cover_url(self):
        """打开封面图片预览窗口"""
        if not self.current_result:
            return
        
        cover_url = self.current_result['cover_url']
        try:
            # 弹出图片预览窗口
            preview_dialog = ImagePreviewDialog(cover_url, self)
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"无法打开封面图片: {str(e)}")
    
    def copy_video_link(self):
        """复制视频链接"""
        if not self.current_result:
            return
        
        video_url = self.current_result['video_url']
        
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(video_url)
        
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
    
    def create_left_sidebar(self):
        """创建左侧侧边导航栏"""
        sidebar = QWidget()
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sidebar.setFixedWidth(150)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 255);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 12, 16, 16)
        sidebar_layout.setSpacing(12)
        
        # 卡片顶部标题
        sidebar_title = QLabel("选择平台")
        sidebar_title.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 17px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                background-color: transparent;
                border: none;
            }
        """)
        sidebar_layout.addWidget(sidebar_title)
        
        # 平台选择区
        platform_row = QVBoxLayout()
        platform_row.setSpacing(8)
        
        platform_label = QLabel("选择视频平台:")
        platform_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 15px;
                font-weight: 500;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                background-color: transparent;
                border: none;
            }
        """)
        platform_row.addWidget(platform_label)
        
        self.platform_combo = ModernComboBox()
        self.platform_combo.setFixedHeight(36)
        self.platform_combo.addItems(list(self.platforms.keys()))
        platform_row.addWidget(self.platform_combo)
        
        sidebar_layout.addLayout(platform_row)
        
        sidebar_layout.addStretch()
        
        # 导航选项
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(12)
        
        settings_btn = QPushButton("设置")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #2c2c2c;
                text-align: left;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(240, 235, 230, 0.6);
            }
        """)
        settings_btn.clicked.connect(lambda: self.show_settings())
        nav_layout.addWidget(settings_btn)
        
        about_btn = QPushButton("关于")
        about_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #2c2c2c;
                text-align: left;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(240, 235, 230, 0.6);
            }
        """)
        about_btn.clicked.connect(lambda: self.show_about())
        nav_layout.addWidget(about_btn)
        
        sidebar_layout.addLayout(nav_layout)
        
        return sidebar
    
    def create_right_content(self):
        """创建右侧主内容区"""
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 255);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 6, 16, 16)
        content_layout.setSpacing(10)
        
        # 内容链接输入
        link_title = QLabel("内容链接")
        link_title.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 17px;
                font-weight: 600;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                background-color: transparent;
                border: none;
            }
        """)
        content_layout.addWidget(link_title)
        
        self.url_input = ModernLineEdit("请粘贴视频分享链接或视频链接...")
        self.url_input.setFixedHeight(32)
        # 强制输入框水平扩展，占满剩余宽度
        self.url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(240, 235, 230, 0.6);
                border: none;
                color: #2c2c2c;
                padding: 0px 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                selection-background-color: rgba(255, 140, 0, 100);
            }
            QLineEdit:focus {
                background-color: rgba(255, 250, 245, 0.8);
            }
            QLineEdit::placeholder {
                color: rgba(100, 100, 100, 150);
            }
        """)
        content_layout.addWidget(self.url_input)
        
        # 核心操作按钮
        self.process_button = ModernButton("开始操作")
        self.process_button.setFixedHeight(40)
        # 按钮水平扩展，占满宽度
        self.process_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 140, 0, 180);
                border: none;
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 140, 0, 220);
            }
            QPushButton:pressed {
                background-color: rgba(255, 140, 0, 150);
            }
            QPushButton:disabled {
                background-color: rgba(200, 200, 200, 100);
                color: rgba(100, 100, 100, 150);
            }
        """)
        content_layout.addWidget(self.process_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        # 进度条水平扩展
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: rgba(240, 235, 230, 0.6);
                text-align: center;
                color: #2c2c2c;
                font-weight: 600;
                font-size: 11px;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }
            QProgressBar::chunk {
                background-color: rgba(255, 140, 0, 180);
                border-radius: 4px;
            }
        """)
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        
        # 处理结果展示
        self.result_area = ExpandableResultArea()
        self.result_area.setStyleSheet("""
            ExpandableResultArea {
                background-color: transparent;
            }
        """)
        # 结果区域优先填充空间，不被压缩
        self.result_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # 添加拉伸因子，确保结果区域占据剩余空间
        content_layout.addWidget(self.result_area, stretch=1)
        
        return content
    
    def create_status_area(self):
        """创建底部状态提示区"""
        status_area = QWidget()
        status_area.setFixedHeight(60)
        status_area.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        status_layout = QVBoxLayout(status_area)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        self.completion_label = QLabel("处理完成")
        self.completion_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-size: 14px;
                font-weight: 500;
                font-family: "Microsoft YaHei UI", "PingFang SC", sans-serif;
                background-color: transparent;
                border: none;
            }
        """)
        self.completion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.completion_label.setVisible(False)
        status_layout.addWidget(self.completion_label)
        
        status_layout.addStretch()
        
        return status_area
    
    def show_settings(self):
        """显示设置对话框"""
        settings_dialog = SettingsDialog(self.download_dir, self)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self.download_dir = settings_dialog.get_download_dir()
            self.save_config(self.download_dir)
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    download_dir = config.get('download_dir', '')
                    if download_dir:
                        # 规范化路径格式
                        normalized_dir = os.path.normpath(download_dir)
                        if os.path.exists(normalized_dir):
                            return normalized_dir
        except Exception as e:
            print(f"加载配置失败: {e}")
        return os.getcwd()
    
    def save_config(self, download_dir):
        """保存配置文件"""
        try:
            # 规范化路径格式
            normalized_dir = os.path.normpath(download_dir)
            config = {
                'download_dir': normalized_dir
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
            QMessageBox.warning(self, "保存失败", f"无法保存配置: {str(e)}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.information(self, "关于", "视频去水印工具 v2.0.1\n\n支持抖音、快手、小红书等平台\n\n开发者：厉温\nGitHub地址：https://github.com/qianyi888666/python-Short-Video-Download-Without-Watermark")


def main():
    """主函数 - 新视觉风格"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置全局样式 - 温暖米白色主题
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(250, 248, 245, 255))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(44, 44, 44))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 242, 238, 255))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 140, 0, 200))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(44, 44, 44))
    palette.setColor(QPalette.ColorRole.Text, QColor(44, 44, 44))
    palette.setColor(QPalette.ColorRole.Button, QColor(255, 140, 0, 180))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 100, 100))
    palette.setColor(QPalette.ColorRole.Link, QColor(255, 140, 0, 200))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 140, 0, 200))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    # 创建主窗口
    window = VideoWatermarkGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()