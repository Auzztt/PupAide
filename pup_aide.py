import re
import json
from datetime import datetime, date
import openpyxl
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import pdfplumber
import PyPDF2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QStackedWidget, QListWidget,
                             QListWidgetItem, QLabel, QFrame, QMessageBox, QFileDialog,
                             QTextEdit, QProgressBar, QGroupBox, QCheckBox,
                             QLineEdit, QSplitter, QTabWidget, QComboBox, QFormLayout,
                             QSlider, QColorDialog, QAbstractItemView, QSpinBox,
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QTableWidget, QTableWidgetItem, QStyle, QDialog)
from PyQt6.QtGui import QBrush, QIcon, QColor
import subprocess
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import sys
import os
import hashlib
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QAbstractItemView
import matplotlib
matplotlib.use('Qt5Agg')
try:
    from docx import Document as DocxDocument
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False

try:
    import win32com.client as win32
    from win32com.client import constants as wd_constants
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False


# 获取全局应用对象，用于后续强制刷新样式
qApp = None


class PupAideMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小狗助理 PupAide - 办公百宝箱")
        self.setMinimumSize(1200, 800)

        # 设置主窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            /* 为 QMessageBox 中的按钮单独设置样式 */
            QMessageBox QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                padding: 6px 12px;
                min-height: 28px;
            }
            QMessageBox QPushButton:hover {
                background-color: #e0e0e0;
            }

            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px 8px;
            }
            QListWidget::item:selected {
                background-color: #FFB347;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                font-family: monospace;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                min-height: 30px;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 6px;
                text-align: center;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #FFB347;
                border-radius: 5px;
            }
            QSplitter::handle {
                background-color: #ddd;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #FFB347;
            }
        """)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # ========== 使用QSplitter实现可拖拽调整大小 ==========
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== 左侧面板 ==========
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 20, 15, 20)

        # 标题
        title_label = QLabel("🐕 小狗助理")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #FFB347; margin-bottom: 20px;")
        title_label.setWordWrap(True)
        left_layout.addWidget(title_label)

        # 功能列表
        self.nav_list = QListWidget()
        list_font = QFont()
        list_font.setPointSize(15)
        self.nav_list.setFont(list_font)
        functions = [
            "📁 重复文件查找器",
            "🔄 文件夹同步/备份",
            "💾 磁盘空间分析器",
            "📄 PDF 批量处理",
            "📂 文件批量筛选",
            "🔍 OCR 文字识别工具",
            "✂️ 文件名称提取器",  # 0422新增功能
            "📑 文档拆分工具",
            "🔁 文本重复识别"
        ]
        for func in functions:
            item = QListWidgetItem(func)
            item.setSizeHint(QSize(0, 45))
            self.nav_list.addItem(item)
        left_layout.addWidget(self.nav_list)

        # 底部信息
        bottom_layout = QHBoxLayout()
        info_label = QLabel("版本 1.2.1")
        info_font = QFont()
        info_font.setPointSize(13)
        info_label.setFont(info_font)
        info_label.setStyleSheet("color: #999;")
        info_label.setWordWrap(True)
        bottom_layout.addWidget(info_label)

        btn_settings = QPushButton("···")
        btn_settings.setObjectName("settingsBtn")
        btn_settings.setFixedSize(36, 24)
        btn_settings.setToolTip("神秘按钮")
        btn_settings.clicked.connect(self._open_easter_egg_settings)
        btn_settings_font = QFont()
        btn_settings_font.setPointSize(12)
        btn_settings_font.setBold(True)
        btn_settings.setFont(btn_settings_font)
        btn_settings.setStyleSheet("""
            QPushButton#settingsBtn {
                background-color: #f0f0f0;
                color: #999;
                border: 1px solid #ddd;
                border-radius: 12px;
                padding: 0px;
                min-height: 0px;
                font-weight: bold;
            }
            QPushButton#settingsBtn:hover {
                color: #FFB347;
                background-color: #fff3e0;
                border-color: #FFB347;
            }
        """)
        bottom_layout.addWidget(btn_settings)
        bottom_layout.addStretch()
        left_layout.addLayout(bottom_layout)

        # tip_label = QLabel("拖动右侧边缘可调整菜单宽度")
        # tip_font = QFont()
        # tip_font.setPointSize(11)
        # tip_label.setFont(tip_font)
        # tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # tip_label.setStyleSheet("color: #bbb;")
        # tip_label.setWordWrap(True)
        # left_layout.addWidget(tip_label)
        left_layout.addStretch()

        # ========== 右侧内容区域 ==========
        self.right_panel = QStackedWidget()
        self.right_panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)

        # 创建各个功能页面
        self.page_duplicate = DuplicateFilePage()
        self.page_sync = SyncBackupPage()
        self.page_disk = DiskAnalyzerPage()
        self.page_pdf = PDFBatchPage()
        self.page_office = OfficeBatchPage()
        self.page_ocr = OCRPage()
        self.page_namecut = FileNameCut()  # 新增功能页面实例
        self.page_docsplit = DocSplitPage()  # 文档拆分页面实例
        self.page_textdup = TextDuplicatePage()  # 文本重复识别页面实例

        self.right_panel.addWidget(self.page_duplicate)
        self.right_panel.addWidget(self.page_sync)
        self.right_panel.addWidget(self.page_disk)
        self.right_panel.addWidget(self.page_pdf)
        self.right_panel.addWidget(self.page_office)
        self.right_panel.addWidget(self.page_ocr)
        self.right_panel.addWidget(self.page_namecut)  # 新增功能页面添加到右侧面板
        self.right_panel.addWidget(self.page_docsplit)  # 文档拆分页面添加到右侧面板
        self.right_panel.addWidget(self.page_textdup)  # 文本重复识别页面添加到右侧面板

        # 添加导航栏点击事件
        self.nav_list.currentRowChanged.connect(
            self.right_panel.setCurrentIndex)

        # 将左右面板添加到分割器
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.right_panel)

        # 设置初始大小比例
        self.splitter.setSizes([250, 800])

        # 添加到主布局
        main_layout.addWidget(self.splitter)

        # 设置窗口图标
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'dog.ico')
        else:
            icon_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), 'dog.ico')
        self.setWindowIcon(QIcon(icon_path))

        # 彩蛋系统
        self.easter_egg_manager = EasterEggManager(self)
        self.easter_egg_manager.on_app_start()

    def _open_easter_egg_settings(self):
        data = _load_easter_egg_data()
        dlg = EasterEggSettingsDialog(self, data)
        dlg.exec()


# ========== 功能1：重复文件查找器 ==========
class DuplicateFilePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("📁 重复文件查找器")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 文件夹选择区域
        folder_group = QGroupBox("选择要扫描的文件夹")
        group_font = QFont()
        group_font.setPointSize(15)
        folder_group.setFont(group_font)
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setSpacing(10)

        # 文件夹路径选择行
        path_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        path_font = QFont()
        path_font.setPointSize(13)
        self.folder_path.setFont(path_font)
        self.folder_path.setPlaceholderText("请选择文件夹...")
        self.folder_path.setReadOnly(True)

        # 选择文件夹按钮
        btn_select = QPushButton("📂 选择文件夹")
        btn_select.setMinimumWidth(130)
        btn_select.clicked.connect(self.select_folder)

        # 确保文本显示
        btn_select.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        path_layout.addWidget(self.folder_path)
        path_layout.addWidget(btn_select)
        folder_layout.addLayout(path_layout)

        layout.addWidget(folder_group)

        # 扫描选项
        option_group = QGroupBox("扫描选项")
        option_group.setFont(group_font)
        option_layout = QVBoxLayout(option_group)
        option_layout.setSpacing(10)

        # 勾选框：只调整大小，不改变勾选样式
        self.check_subfolders = QCheckBox("包含子文件夹")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_subfolders.setFont(check_font)
        self.check_subfolders.setChecked(True)

        option_layout.addWidget(self.check_subfolders)
        layout.addWidget(option_group)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # 扫描按钮
        self.btn_scan = QPushButton("🔍 开始扫描")
        self.btn_scan.setMinimumWidth(130)
        self.btn_scan.clicked.connect(self.scan_files)
        self.btn_scan.setEnabled(False)

        # 确保文本显示
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        # 清空按钮
        self.btn_clear = QPushButton("🗑️ 清空结果")
        self.btn_clear.setMinimumWidth(120)
        self.btn_clear.clicked.connect(self.clear_results)

        # 确保文本显示
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        button_layout.addWidget(self.btn_scan)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 结果显示区域
        result_group = QGroupBox("扫描结果")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        text_font = QFont()
        text_font.setPointSize(12)
        self.result_text.setFont(text_font)
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(350)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

        self.scan_folder = None

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.scan_folder = folder
            self.folder_path.setText(folder)
            self.btn_scan.setEnabled(True)
            self.result_text.clear()
            self.result_text.append(f"✅ 已选择文件夹: {folder}\n")
            self.result_text.append("点击「开始扫描」查找重复文件...\n")

    def clear_results(self):
        self.result_text.clear()
        if self.scan_folder:
            self.result_text.append(f"✅ 已选择文件夹: {self.scan_folder}\n")
            self.result_text.append("点击「开始扫描」查找重复文件...\n")

    def scan_files(self):
        if not self.scan_folder:
            QMessageBox.warning(self, "提示", "请先选择文件夹！")
            return

        self.btn_scan.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.result_text.clear()
        self.result_text.append(f"🔍 正在扫描文件夹: {self.scan_folder}\n")
        self.result_text.append("=" * 60 + "\n\n")

        try:
            self.progress.setValue(30)

            file_dict = {}
            total_files = 0

            # 遍历文件
            if self.check_subfolders.isChecked():
                for root, dirs, files in os.walk(self.scan_folder):
                    for file in files:
                        total_files += 1
            else:
                for file in os.listdir(self.scan_folder):
                    if os.path.isfile(os.path.join(self.scan_folder, file)):
                        total_files += 1

            if total_files == 0:
                self.result_text.append("❌ 没有找到任何文件\n")
                self.progress.setVisible(False)
                self.btn_scan.setEnabled(True)
                return

            self.progress.setValue(50)
            self.result_text.append(f"📊 找到 {total_files} 个文件，正在分析...\n\n")

            # 计算文件哈希
            scanned = 0
            if self.check_subfolders.isChecked():
                for root, dirs, files in os.walk(self.scan_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getsize(file_path) > 1024:
                                with open(file_path, 'rb') as f:
                                    file_hash = hashlib.md5(
                                        f.read(8192)).hexdigest()

                                key = (file, os.path.getsize(file_path))
                                if key not in file_dict:
                                    file_dict[key] = []
                                file_dict[key].append(file_path)
                        except Exception:
                            pass
                        scanned += 1
                        if scanned % 10 == 0:
                            self.progress.setValue(
                                50 + int(scanned / total_files * 40))
                            QApplication.processEvents()
            else:
                for file in os.listdir(self.scan_folder):
                    file_path = os.path.join(self.scan_folder, file)
                    if os.path.isfile(file_path):
                        try:
                            if os.path.getsize(file_path) > 1024:
                                with open(file_path, 'rb') as f:
                                    file_hash = hashlib.md5(
                                        f.read(8192)).hexdigest()

                                key = (file, os.path.getsize(file_path))
                                if key not in file_dict:
                                    file_dict[key] = []
                                file_dict[key].append(file_path)
                        except Exception:
                            pass
                        scanned += 1
                        if scanned % 10 == 0:
                            self.progress.setValue(
                                50 + int(scanned / total_files * 40))
                            QApplication.processEvents()

            self.progress.setValue(100)

            # 显示结果
            duplicates_found = False
            for (filename, size), paths in file_dict.items():
                if len(paths) > 1:
                    duplicates_found = True
                    size_kb = size / 1024
                    if size_kb > 1024:
                        size_str = f"{size_kb/1024:.2f} MB"
                    else:
                        size_str = f"{size_kb:.2f} KB"

                    self.result_text.append(f"📄 {filename} ({size_str})\n")
                    for path in paths:
                        self.result_text.append(f"   └─ {path}\n")
                    self.result_text.append("\n")

            if not duplicates_found:
                self.result_text.append("✅ 扫描完成！没有找到重复文件！\n")
            else:
                self.result_text.append(
                    f"\n✅ 扫描完成！共找到 {len([k for k,v in file_dict.items() if len(v)>1])} 组重复文件\n")

        except Exception as e:
            self.result_text.append(f"❌ 扫描过程中发生错误：{str(e)}\n")

        self.progress.setVisible(False)
        self.btn_scan.setEnabled(True)


# ========== 功能2：文件夹同步/备份工具 ==========
class SyncBackupPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔄 文件夹同步/备份工具")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 源文件夹选择
        source_group = QGroupBox("源文件夹（要备份的文件夹）")
        group_font = QFont()
        group_font.setPointSize(15)
        source_group.setFont(group_font)
        source_layout = QVBoxLayout(source_group)
        source_layout.setSpacing(10)

        source_path_layout = QHBoxLayout()
        self.source_path = QLineEdit()
        self.source_path.setPlaceholderText("请选择要备份的源文件夹...")
        self.source_path.setReadOnly(True)

        self.btn_source = QPushButton("📂 选择源文件夹")
        self.btn_source.setMinimumWidth(130)
        self.btn_source.clicked.connect(self.select_source_folder)
        self.btn_source.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        source_path_layout.addWidget(self.source_path)
        source_path_layout.addWidget(self.btn_source)
        source_layout.addLayout(source_path_layout)
        layout.addWidget(source_group)

        # 目标文件夹选择
        target_group = QGroupBox("目标文件夹（备份保存位置）")
        target_group.setFont(group_font)
        target_layout = QVBoxLayout(target_group)
        target_layout.setSpacing(10)

        target_path_layout = QHBoxLayout()
        self.target_path = QLineEdit()
        self.target_path.setPlaceholderText("请选择备份保存的目标文件夹...")
        self.target_path.setReadOnly(True)

        self.btn_target = QPushButton("📂 选择目标文件夹")
        self.btn_target.setMinimumWidth(130)
        self.btn_target.clicked.connect(self.select_target_folder)
        self.btn_target.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        target_path_layout.addWidget(self.target_path)
        target_path_layout.addWidget(self.btn_target)
        target_layout.addLayout(target_path_layout)
        layout.addWidget(target_group)

        # 同步选项
        option_group = QGroupBox("同步选项")
        option_group.setFont(group_font)
        option_layout = QVBoxLayout(option_group)

        self.check_subfolders = QCheckBox("包含子文件夹")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_subfolders.setFont(check_font)
        self.check_subfolders.setChecked(True)

        self.check_overwrite = QCheckBox("覆盖已存在的文件")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_overwrite.setFont(check_font)
        self.check_overwrite.setChecked(True)

        self.check_delete = QCheckBox("删除目标文件夹中多余的文件（保持完全一致）")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_delete.setFont(check_font)
        self.check_delete.setChecked(False)

        option_layout.addWidget(self.check_subfolders)
        option_layout.addWidget(self.check_overwrite)
        option_layout.addWidget(self.check_delete)
        layout.addWidget(option_group)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.btn_sync = QPushButton("🔄 开始同步")
        self.btn_sync.setMinimumWidth(130)
        self.btn_sync.clicked.connect(self.start_sync)
        self.btn_sync.setEnabled(False)
        self.btn_sync.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        self.btn_preview = QPushButton("👁️ 预览同步")
        self.btn_preview.setMinimumWidth(120)
        self.btn_preview.clicked.connect(self.preview_sync)
        self.btn_preview.setEnabled(False)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        button_layout.addWidget(self.btn_sync)
        button_layout.addWidget(self.btn_preview)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 结果显示区域
        result_group = QGroupBox("同步日志")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        text_font = QFont()
        text_font.setPointSize(12)
        self.result_text.setFont(text_font)
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(350)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

        self.source_folder = None
        self.target_folder = None

    def select_source_folder(self):
        try:
            # 使用文件对话框选择文件夹
            folder = QFileDialog.getExistingDirectory(
                self,
                "选择源文件夹"
            )
            if folder and os.path.exists(folder):
                self.source_folder = folder
                self.source_path.setText(folder)
                self.check_buttons_enabled()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"选择文件夹失败：{str(e)}")

    def select_target_folder(self):
        try:
            folder = QFileDialog.getExistingDirectory(
                self,
                "选择目标文件夹"
            )
            if folder and os.path.exists(folder):
                self.target_folder = folder
                self.target_path.setText(folder)
                self.check_buttons_enabled()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"选择文件夹失败：{str(e)}")

    def check_buttons_enabled(self):
        enabled = bool(self.source_folder and self.target_folder)
        self.btn_sync.setEnabled(enabled)
        self.btn_preview.setEnabled(enabled)

    def preview_sync(self):
        if not self.source_folder or not self.target_folder:
            QMessageBox.warning(self, "提示", "请先选择源文件夹和目标文件夹！")
            return

        self.result_text.clear()
        self.result_text.append("🔍 正在分析同步内容...\n")
        self.result_text.append("=" * 60 + "\n\n")

        # 获取需要同步的文件列表
        files_to_copy = []
        files_to_delete = []

        # 收集源文件夹中的所有文件
        source_files = {}
        try:
            if self.check_subfolders.isChecked():
                for root, dirs, files in os.walk(self.source_folder):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(
                            full_path, self.source_folder)
                        source_files[rel_path] = full_path
            else:
                for item in os.listdir(self.source_folder):
                    full_path = os.path.join(self.source_folder, item)
                    if os.path.isfile(full_path):
                        source_files[item] = full_path
        except Exception as e:
            self.result_text.append(f"❌ 扫描源文件夹失败：{str(e)}\n")
            return

        # 检查哪些文件需要复制
        for rel_path, src_path in source_files.items():
            target_path = os.path.join(self.target_folder, rel_path)
            if not os.path.exists(target_path):
                files_to_copy.append(rel_path)
            elif self.check_overwrite.isChecked():
                src_size = os.path.getsize(src_path)
                dst_size = os.path.getsize(target_path)
                if src_size != dst_size:
                    files_to_copy.append(rel_path)

        # 检查需要删除的文件
        if self.check_delete.isChecked():
            try:
                if self.check_subfolders.isChecked():
                    for root, dirs, files in os.walk(self.target_folder):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(
                                full_path, self.target_folder)
                            if rel_path not in source_files:
                                files_to_delete.append(rel_path)
                else:
                    for item in os.listdir(self.target_folder):
                        full_path = os.path.join(self.target_folder, item)
                        if os.path.isfile(full_path) and item not in source_files:
                            files_to_delete.append(item)
            except Exception as e:
                self.result_text.append(f"❌ 扫描目标文件夹失败：{str(e)}\n")

        # 显示预览结果
        self.result_text.append(f"📊 同步预览结果：\n")
        self.result_text.append(f"源文件夹: {self.source_folder}\n")
        self.result_text.append(f"目标文件夹: {self.target_folder}\n\n")

        if files_to_copy:
            self.result_text.append(
                f"📁 需要复制/更新的文件 ({len(files_to_copy)} 个):\n")
            for f in files_to_copy[:20]:
                self.result_text.append(f"   └─ {f}\n")
            if len(files_to_copy) > 20:
                self.result_text.append(
                    f"   ... 还有 {len(files_to_copy)-20} 个文件\n")
            self.result_text.append("\n")
        else:
            self.result_text.append("✅ 没有需要复制或更新的文件\n\n")

        if files_to_delete:
            self.result_text.append(
                f"🗑️ 需要删除的文件 ({len(files_to_delete)} 个):\n")
            for f in files_to_delete[:20]:
                self.result_text.append(f"   └─ {f}\n")
            if len(files_to_delete) > 20:
                self.result_text.append(
                    f"   ... 还有 {len(files_to_delete)-20} 个文件\n")
            self.result_text.append("\n")
        elif self.check_delete.isChecked():
            self.result_text.append("✅ 没有需要删除的文件\n\n")

        if not files_to_copy and not files_to_delete:
            self.result_text.append("🎉 文件夹已经同步完成，无需任何操作！\n")

    def start_sync(self):
        if not self.source_folder or not self.target_folder:
            QMessageBox.warning(self, "提示", "请先选择源文件夹和目标文件夹！")
            return

        # 确认对话框
        reply = QMessageBox.question(self, "确认同步",
                                     f"确定要将\n{self.source_folder}\n同步到\n{self.target_folder}\n吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_sync.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.result_text.clear()
        self.result_text.append("🔄 开始同步...\n")
        self.result_text.append("=" * 60 + "\n\n")

        try:
            # 收集源文件夹中的所有文件
            source_files = {}
            try:
                if self.check_subfolders.isChecked():
                    for root, dirs, files in os.walk(self.source_folder):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(
                                full_path, self.source_folder)
                            source_files[rel_path] = full_path
                else:
                    for item in os.listdir(self.source_folder):
                        full_path = os.path.join(self.source_folder, item)
                        if os.path.isfile(full_path):
                            source_files[item] = full_path
            except Exception as e:
                self.result_text.append(f"❌ 扫描源文件夹失败：{str(e)}\n")
                self.progress.setVisible(False)
                self.btn_sync.setEnabled(True)
                self.btn_preview.setEnabled(True)
                return

            total_files = len(source_files)
            if total_files == 0:
                self.result_text.append("❌ 源文件夹中没有找到文件\n")
                self.progress.setVisible(False)
                self.btn_sync.setEnabled(True)
                self.btn_preview.setEnabled(True)
                return

            copied = 0
            failed = 0

            # 创建目标文件夹结构并复制文件
            import shutil

            for rel_path, src_path in source_files.items():
                target_path = os.path.join(self.target_folder, rel_path)
                target_dir = os.path.dirname(target_path)

                # 创建目标文件夹
                if not os.path.exists(target_dir):
                    try:
                        os.makedirs(target_dir)
                    except Exception as e:
                        self.result_text.append(
                            f"❌ 创建文件夹失败: {target_dir} - {str(e)}\n")
                        failed += 1
                        continue

                # 检查是否需要复制
                need_copy = False
                if not os.path.exists(target_path):
                    need_copy = True
                elif self.check_overwrite.isChecked():
                    try:
                        src_size = os.path.getsize(src_path)
                        dst_size = os.path.getsize(target_path)
                        if src_size != dst_size:
                            need_copy = True
                    except Exception:
                        need_copy = True

                if need_copy:
                    try:
                        shutil.copy2(src_path, target_path)
                        copied += 1
                        self.result_text.append(f"✅ 复制: {rel_path}\n")
                    except Exception as e:
                        failed += 1
                        self.result_text.append(f"❌ 复制失败: {rel_path} - {str(e)}\n")

                # 更新进度
                progress_value = int((copied + failed) / total_files * 80)
                self.progress.setValue(progress_value)
                QApplication.processEvents()

            # 删除多余的文件
            deleted = 0
            if self.check_delete.isChecked():
                self.result_text.append("\n🗑️ 正在删除多余文件...\n")

                try:
                    if self.check_subfolders.isChecked():
                        for root, dirs, files in os.walk(self.target_folder):
                            for file in files:
                                full_path = os.path.join(root, file)
                                rel_path = os.path.relpath(
                                    full_path, self.target_folder)
                                if rel_path not in source_files:
                                    try:
                                        os.remove(full_path)
                                        deleted += 1
                                        self.result_text.append(
                                            f"🗑️ 删除: {rel_path}\n")
                                    except Exception as e:
                                        self.result_text.append(
                                            f"❌ 删除失败: {rel_path} - {str(e)}\n")
                    else:
                        for item in os.listdir(self.target_folder):
                            full_path = os.path.join(self.target_folder, item)
                            if os.path.isfile(full_path) and item not in source_files:
                                try:
                                    os.remove(full_path)
                                    deleted += 1
                                    self.result_text.append(f"🗑️ 删除: {item}\n")
                                except Exception as e:
                                    self.result_text.append(
                                        f"❌ 删除失败: {item} - {str(e)}\n")
                except Exception as e:
                    self.result_text.append(f"❌ 删除过程出错：{str(e)}\n")

                self.progress.setValue(90)

            self.progress.setValue(100)

            # 显示完成信息
            self.result_text.append("\n" + "=" * 60 + "\n")
            self.result_text.append(f"✅ 同步完成！\n")
            self.result_text.append(f"📁 复制/更新文件: {copied} 个\n")
            if self.check_delete.isChecked():
                self.result_text.append(f"🗑️ 删除文件: {deleted} 个\n")
            if failed > 0:
                self.result_text.append(f"❌ 失败: {failed} 个\n")

            QMessageBox.information(self, "完成", "文件夹同步完成！")

        except Exception as e:
            self.result_text.append(f"❌ 同步过程中发生错误：{str(e)}\n")
            QMessageBox.critical(self, "错误", f"同步失败：{str(e)}")

        self.progress.setVisible(False)
        self.btn_sync.setEnabled(True)
        self.btn_preview.setEnabled(True)


# ========== 功能3：磁盘空间分析器 ==========
class DiskAnalyzerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_path = None
        self.scan_thread = None
        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei',
                                           'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        self.setup_ui()

    def setup_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("💾 磁盘空间分析器")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 统一的 QGroupBox 字体
        group_font = QFont()
        group_font.setPointSize(15)

        # 路径选择区域
        path_group = QGroupBox("选择要分析的路径")
        path_group.setFont(group_font)  # 添加字体设置
        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择要分析的文件夹或磁盘...")
        self.path_edit.setReadOnly(True)

        self.btn_browse = QPushButton("📂 选择文件夹")
        self.btn_browse.clicked.connect(self.select_path)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.btn_browse)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # 扫描选项
        option_group = QGroupBox("扫描选项")
        option_group.setFont(group_font)  # 添加字体设置
        option_layout = QVBoxLayout()

        self.check_subfolders = QCheckBox("包含子文件夹")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_subfolders.setFont(check_font)
        self.check_subfolders.setChecked(True)

        self.check_large_files = QCheckBox("显示大文件列表 (大于100MB)")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_large_files.setFont(check_font)
        self.check_large_files.setChecked(True)

        option_layout.addWidget(self.check_subfolders)
        option_layout.addWidget(self.check_large_files)
        option_group.setLayout(option_layout)
        layout.addWidget(option_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.btn_scan = QPushButton("🔍 开始扫描")
        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_scan.setEnabled(False)
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        self.btn_stop = QPushButton("⏹ 停止扫描")
        self.btn_stop.clicked.connect(self.stop_scan)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
        """)

        button_layout.addWidget(self.btn_scan)
        button_layout.addWidget(self.btn_stop)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 结果显示区域
        result_layout = QHBoxLayout()

        # 左侧：饼图
        self.figure = plt.figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        chart_group = QGroupBox("空间分布")
        chart_group.setFont(group_font)  # 添加字体设置
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(self.canvas)
        chart_group.setLayout(chart_layout)

        # 右侧：文件列表
        list_group = QGroupBox("大文件列表")
        list_group.setFont(group_font)  # 添加字体设置
        list_layout = QVBoxLayout()

        self.file_list = QTreeWidget()
        self.file_list.itemDoubleClicked.connect(self.open_file_location)
        self.file_list.setHeaderLabels(["文件名", "大小", "路径", "删除建议"])
        self.file_list.setColumnWidth(0, 200)
        self.file_list.setColumnWidth(1, 100)
        self.file_list.setColumnWidth(2, 300)
        self.file_list.setColumnWidth(3, 100)

        list_layout.addWidget(self.file_list)
        list_group.setLayout(list_layout)

        result_layout.addWidget(chart_group, 1)
        result_layout.addWidget(list_group, 2)

        layout.addLayout(result_layout)

        # 状态栏
        self.status_label = QLabel("请选择要分析的路径")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

    def select_path(self):
        """选择要分析的路径"""
        path = QFileDialog.getExistingDirectory(self, "选择要分析的文件夹")
        if path:
            self.current_path = path
            self.path_edit.setText(path)
            self.btn_scan.setEnabled(True)
            self.status_label.setText(f"已选择路径: {path}")

    def start_scan(self):
        """开始扫描"""
        if not self.current_path:
            QMessageBox.warning(self, "提示", "请先选择要分析的路径！")
            return

        # 清空之前的结果
        self.file_list.clear()
        self.ax.clear()
        self.canvas.draw()

        # 禁用扫描按钮，启用停止按钮
        self.btn_scan.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        # 创建并启动扫描线程
        self.scan_thread = ScanThread(
            self.current_path,
            self.check_subfolders.isChecked(),
            self.check_large_files.isChecked()
        )
        self.scan_thread.progress_updated.connect(self.update_progress)
        self.scan_thread.scan_completed.connect(self.display_results)
        self.scan_thread.start()

    def stop_scan(self):
        """停止扫描"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.status_label.setText("扫描已停止")
            self.btn_scan.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.progress.setVisible(False)

    def update_progress(self, value, message):
        """更新进度"""
        self.progress.setValue(value)
        self.status_label.setText(message)

    def display_results(self, folder_sizes, large_files):
        """显示扫描结果"""
        # 绘制饼图
        if folder_sizes:
            self.plot_pie_chart(folder_sizes)

        # 显示大文件列表
        if large_files:
            self.display_large_files(large_files)

        # 更新状态
        self.status_label.setText("扫描完成！")
        self.btn_scan.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)

    def plot_pie_chart(self, folder_sizes):
        """绘制饼图"""
        # 获取前10个最大的文件夹
        top_folders = sorted(folder_sizes.items(),
                             key=lambda x: x[1], reverse=True)[:10]

        if not top_folders:
            return

        labels = [os.path.basename(path) for path, _ in top_folders]
        sizes = [size for _, size in top_folders]

        # 计算其他文件夹的总大小
        total_size = sum(folder_sizes.values())
        top_size = sum(sizes)
        if total_size > top_size:
            labels.append("其他")
            sizes.append(total_size - top_size)

        # 绘制饼图
        self.ax.clear()
        colors = plt.cm.Set3(range(len(labels)))
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )

        # 设置文本样式
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')

        self.ax.set_title("文件夹空间分布", fontsize=12, pad=20)
        self.canvas.draw()

    # def display_large_files(self, large_files):
    #     """显示大文件列表"""
    #     self.file_list.clear()

    #     for file_path, file_size in large_files:
    #         # 格式化文件大小
    #         if file_size >= 1024 * 1024 * 1024:
    #             size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
    #         elif file_size >= 1024 * 1024:
    #             size_str = f"{file_size / (1024 * 1024):.2f} MB"
    #         else:
    #             size_str = f"{file_size / 1024:.2f} KB"

    #         # 创建树形项
    #         item = QTreeWidgetItem([
    #             os.path.basename(file_path),
    #             size_str,
    #             os.path.dirname(file_path)
    #         ])

    #         # 设置图标
    #         if os.path.isdir(file_path):
    #             item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
    #         else:
    #             item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))

    #         self.file_list.addTopLevelItem(item)

    #     # 调整列宽
    #     self.file_list.resizeColumnToContents(0)
    #     self.file_list.resizeColumnToContents(1)
    def display_large_files(self, large_files):
        """显示大文件列表"""
        self.file_list.clear()

        for file_path, file_size, is_system in large_files:  # 解包时包含is_system标志
            # 格式化文件大小
            if file_size >= 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
            elif file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{file_size / 1024:.2f} KB"

            # 判断是否为系统文件（使用扫描线程中已经判断好的标志）
            status = "不建议删除" if is_system else "可以考虑删除"

            # 创建树形项（包含4列：文件名、大小、路径、删除建议）
            item = QTreeWidgetItem([
                os.path.basename(file_path),
                size_str,
                os.path.dirname(file_path),
                status
            ])

            # 设置图标
            if os.path.isdir(file_path):
                item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            else:
                item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

            # 设置状态颜色
            if is_system:
                item.setForeground(3, QBrush(QColor('red')))
            else:
                item.setForeground(3, QBrush(QColor('green')))

            self.file_list.addTopLevelItem(item)

        # 调整列宽
        self.file_list.resizeColumnToContents(0)
        self.file_list.resizeColumnToContents(1)
        self.file_list.resizeColumnToContents(3)

    # def is_system_file(self, file_path):
    #     """判断是否为系统文件"""
    #     # 获取文件名
    #     filename = os.path.basename(file_path).lower()

    #     # 系统文件扩展名列表
    #     system_extensions = [
    #         '.sys', '.dll', '.exe', '.com', '.bat', '.cmd',
    #         '.msi', '.msm', '.msp', '.mst', '.idb', '.pdb',
    #         '.lib', '.obj', '.res', '.manifest', '.config'
    #     ]

    #     # 系统文件夹列表
    #     system_folders = [
    #         'windows', 'program files', 'program files (x86)',
    #         'programdata', 'system32', 'syswow64'
    #     ]

    #     # 检查文件扩展名
    #     if any(filename.endswith(ext) for ext in system_extensions):
    #         return True

    #     # 检查文件路径是否包含系统文件夹
    #     path_lower = file_path.lower()
    #     if any(folder in path_lower for folder in system_folders):
    #         return True

    #     # 检查隐藏文件
    #     if os.name == 'nt':  # Windows系统
    #         try:
    #             import win32api
    #             import win32con
    #             attrs = win32api.GetFileAttributes(file_path)
    #             if attrs & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM):
    #                 return True
    #         except:
    #             pass

    #     return False

    def open_file_location(self, item):
        """打开文件所在位置"""
        # 获取完整文件路径
        file_name = item.text(0)  # 文件名
        file_dir = item.text(2)   # 文件所在目录

        # 确保路径格式正确
        if not file_dir:
            QMessageBox.warning(self, "错误", "无法获取文件路径")
            return

        # 拼接完整路径
        file_path = os.path.normpath(os.path.join(file_dir, file_name))

        # 验证文件是否存在
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", f"文件不存在：{file_path}")
            return

        try:
            if os.name == 'nt':  # Windows系统
                # 使用explorer的/select参数打开文件所在位置并选中文件
                subprocess.Popen(['explorer', '/select,', file_path])
            elif os.name == 'posix':  # Linux/Mac系统
                # 打开文件所在目录
                subprocess.Popen(['xdg-open', os.path.dirname(file_path)])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件位置：{str(e)}")


class ScanThread(QThread):
    """扫描文件夹的线程"""
    progress_updated = pyqtSignal(int, str)
    scan_completed = pyqtSignal(dict, list)

    def __init__(self, path, include_subfolders, show_large_files):
        super().__init__()
        self.path = path
        self.include_subfolders = include_subfolders
        self.show_large_files = show_large_files
        self._is_running = True

    def run(self):
        """执行扫描"""
        folder_sizes = {}
        large_files = []
        total_size = 0
        scanned_files = 0
        total_files = 0

        # 系统文件扩展名和文件夹列表（移到类成员变量）
        system_extensions = ['.sys', '.dll', '.exe', '.com', '.bat', '.cmd',
                             '.msi', '.msm', '.msp', '.mst', '.idb', '.pdb',
                             '.lib', '.obj', '.res', '.manifest', '.config']
        system_folders = ['windows', 'program files', 'program files (x86)',
                          'programdata', 'system32', 'syswow64']

        # 首先计算总文件数
        self.progress_updated.emit(5, "正在统计文件数量...")
        if self.include_subfolders:
            for root, dirs, files in os.walk(self.path):
                total_files += len(files)
        else:
            total_files = len([f for f in os.listdir(self.path)
                              if os.path.isfile(os.path.join(self.path, f))])

        if total_files == 0:
            self.progress_updated.emit(100, "没有找到文件")
            self.scan_completed.emit({}, [])
            return

        # 扫描文件
        self.progress_updated.emit(10, "正在扫描文件...")
        if self.include_subfolders:
            for root, dirs, files in os.walk(self.path):
                if not self._is_running:
                    break

                # 统计当前文件夹大小
                folder_size = 0
                for file in files:
                    if not self._is_running:
                        break

                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        folder_size += file_size
                        total_size += file_size

                        # 检查是否为大文件
                        if self.show_large_files and file_size > 100 * 1024 * 1024:
                            # 在扫描线程中判断是否为系统文件
                            is_system = self._is_system_file(
                                file_path, system_extensions, system_folders)
                            large_files.append(
                                (file_path, file_size, is_system))

                        scanned_files += 1
                        if scanned_files % 10 == 0:
                            progress = 10 + \
                                int(scanned_files / total_files * 80)
                            self.progress_updated.emit(
                                progress,
                                f"已扫描 {scanned_files}/{total_files} 个文件..."
                            )
                    except (OSError, PermissionError):
                        pass

                # 记录文件夹大小
                if folder_size > 0:
                    folder_sizes[root] = folder_size
        else:
            for item in os.listdir(self.path):
                if not self._is_running:
                    break

                item_path = os.path.join(self.path, item)
                try:
                    if os.path.isfile(item_path):
                        file_size = os.path.getsize(item_path)
                        total_size += file_size

                        # 检查是否为大文件
                        if self.show_large_files and file_size > 100 * 1024 * 1024:
                            # large_files.append((item_path, file_size))
                            is_system = self._is_system_file(
                                item_path, system_extensions, system_folders)
                            large_files.append(
                                (item_path, file_size, is_system))

                        scanned_files += 1
                        if scanned_files % 10 == 0:
                            progress = 10 + \
                                int(scanned_files / total_files * 80)
                            self.progress_updated.emit(
                                progress,
                                f"已扫描 {scanned_files}/{total_files} 个文件..."
                            )
                    elif os.path.isdir(item_path):
                        # 统计子文件夹大小
                        folder_size = 0
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                if not self._is_running:
                                    break

                                file_path = os.path.join(root, file)
                                try:
                                    file_size = os.path.getsize(file_path)
                                    folder_size += file_size
                                    total_size += file_size

                                    # 检查是否为大文件
                                    if self.show_large_files and file_size > 100 * 1024 * 1024:
                                        large_files.append(
                                            (file_path, file_size))

                                    scanned_files += 1
                                    if scanned_files % 10 == 0:
                                        progress = 10 + \
                                            int(scanned_files /
                                                total_files * 80)
                                        self.progress_updated.emit(
                                            progress,
                                            f"已扫描 {scanned_files}/{total_files} 个文件..."
                                        )
                                except (OSError, PermissionError):
                                    pass

                        if folder_size > 0:
                            folder_sizes[item_path] = folder_size
                except (OSError, PermissionError):
                    pass

        # 按大小排序大文件
        large_files.sort(key=lambda x: x[1], reverse=True)

        # 完成扫描
        self.progress_updated.emit(
            100, f"扫描完成！总大小: {self.format_size(total_size)}")
        self.scan_completed.emit(folder_sizes, large_files)

    def _is_system_file(self, file_path, system_extensions, system_folders):
        """判断是否为系统文件（辅助方法）"""
        filename = os.path.basename(file_path).lower()

        # 检查文件扩展名
        if any(filename.endswith(ext) for ext in system_extensions):
            return True

        # 检查文件路径是否包含系统文件夹
        path_lower = file_path.lower()
        if any(folder in path_lower for folder in system_folders):
            return True

        return False

    def stop(self):
        """停止扫描"""
        self._is_running = False
        self.wait()

    @staticmethod
    def format_size(size):
        """格式化文件大小"""
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        elif size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        elif size >= 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size} B"


# ========== 功能4：PDF批量处理工具 ==========
class PDFBatchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_files = []  # 存储选中的PDF文件列表
        self.setup_ui()

    def setup_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("📄 PDF 批量处理工具（该功能暂未测试）")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # # 添加注释文本
        # subtitle = QLabel("该功能暂未测试")
        # subtitle.setFont(QFont("Arial", 12))  # 使用较小的字体
        # subtitle.setStyleSheet("color: #888888;")  # 设置为灰色
        # layout.addWidget(subtitle)

        # 统一的 QGroupBox 字体
        group_font = QFont()
        group_font.setPointSize(15)

        # 文件选择区域
        file_group = QGroupBox("选择PDF文件")
        file_group.setFont(group_font)
        file_layout = QVBoxLayout(file_group)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove)  # 允许拖拽排序
        file_layout.addWidget(self.file_list)

        # 文件操作按钮
        file_btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ 添加文件")
        self.btn_add.clicked.connect(self.add_files)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        self.btn_remove = QPushButton("➖ 移除选中")
        self.btn_remove.clicked.connect(self.remove_files)
        self.btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
        """)

        self.btn_clear = QPushButton("🗑️ 清空列表")
        self.btn_clear.clicked.connect(self.clear_files)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #999;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)

        file_btn_layout.addWidget(self.btn_add)
        file_btn_layout.addWidget(self.btn_remove)
        file_btn_layout.addWidget(self.btn_clear)
        file_layout.addLayout(file_btn_layout)

        layout.addWidget(file_group)

        # 功能选项卡
        self.tab_widget = QTabWidget()

        # 合并PDF标签页
        self.merge_tab = QWidget()
        self.setup_merge_tab()
        self.tab_widget.addTab(self.merge_tab, "📑 合并PDF")

        # 拆分PDF标签页
        self.split_tab = QWidget()
        self.setup_split_tab()
        self.tab_widget.addTab(self.split_tab, "✂️ 拆分PDF")

        # 添加水印标签页
        self.watermark_tab = QWidget()
        self.setup_watermark_tab()
        self.tab_widget.addTab(self.watermark_tab, "💧 添加水印")

        # 提取文字标签页
        self.extract_tab = QWidget()
        self.setup_extract_tab()
        self.tab_widget.addTab(self.extract_tab, "📝 提取文字")

        # 加密/解密标签页
        self.encrypt_tab = QWidget()
        self.setup_encrypt_tab()
        self.tab_widget.addTab(self.encrypt_tab, "🔐 加密/解密")

        layout.addWidget(self.tab_widget)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 结果显示区域
        result_group = QGroupBox("处理结果")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        text_font = QFont()
        text_font.setPointSize(12)
        self.result_text.setFont(text_font)
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

    def setup_merge_tab(self):
        """设置合并PDF标签页"""
        layout = QVBoxLayout(self.merge_tab)
        layout.setSpacing(15)

        # 说明
        info = QLabel("将多个PDF文件合并为一个文件，支持拖拽调整合并顺序")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # 输出文件设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件名:"))

        self.merge_output = QLineEdit()
        self.merge_output.setPlaceholderText("合并后的文件名.pdf")
        output_layout.addWidget(self.merge_output)

        self.btn_merge_browse = QPushButton("📂 选择保存位置")
        self.btn_merge_browse.clicked.connect(self.browse_output_file)
        self.btn_merge_browse.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        output_layout.addWidget(self.btn_merge_browse)

        layout.addLayout(output_layout)

        # 合并按钮
        self.btn_merge = QPushButton("🔗 开始合并")
        self.btn_merge.clicked.connect(self.merge_pdfs)
        self.btn_merge.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                min-height: 35px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_merge)

        layout.addStretch()

    def setup_split_tab(self):
        """设置拆分PDF标签页"""
        layout = QVBoxLayout(self.split_tab)
        layout.setSpacing(15)

        # 说明
        info = QLabel("从PDF文件中提取指定页面，生成新的PDF文件")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # 页面范围设置
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("页面范围:"))

        self.split_range = QLineEdit()
        self.split_range.setPlaceholderText("例如: 1,3,5-10,15")
        range_layout.addWidget(self.split_range)

        layout.addLayout(range_layout)

        # 输出文件设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件名:"))

        self.split_output = QLineEdit()
        self.split_output.setPlaceholderText("拆分后的文件名.pdf")
        output_layout.addWidget(self.split_output)

        self.btn_split_browse = QPushButton("📂 选择保存位置")
        self.btn_split_browse.clicked.connect(self.browse_output_file)
        self.btn_split_browse.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        output_layout.addWidget(self.btn_split_browse)

        layout.addLayout(output_layout)

        # 拆分按钮
        self.btn_split = QPushButton("✂️ 开始拆分")
        self.btn_split.clicked.connect(self.split_pdf)
        self.btn_split.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                min-height: 35px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_split)

        layout.addStretch()

    def setup_watermark_tab(self):
        """设置添加水印标签页"""
        layout = QVBoxLayout(self.watermark_tab)
        layout.setSpacing(15)

        # 说明
        info = QLabel("为PDF文件添加文本水印")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # 水印文本设置
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("水印文本:"))

        self.watermark_text = QLineEdit()
        self.watermark_text.setPlaceholderText("例如: 机密文档")
        text_layout.addWidget(self.watermark_text)

        layout.addLayout(text_layout)

        # 水印设置
        settings_layout = QFormLayout()

        self.watermark_opacity = QSlider(Qt.Orientation.Horizontal)
        self.watermark_opacity.setRange(10, 100)
        self.watermark_opacity.setValue(30)
        self.watermark_opacity.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.watermark_opacity.setTickInterval(10)
        settings_layout.addRow("透明度:", self.watermark_opacity)

        self.watermark_rotation = QSlider(Qt.Orientation.Horizontal)
        self.watermark_rotation.setRange(0, 360)
        self.watermark_rotation.setValue(45)
        self.watermark_rotation.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.watermark_rotation.setTickInterval(45)
        settings_layout.addRow("旋转角度:", self.watermark_rotation)

        self.watermark_color = QPushButton("选择颜色")
        self.watermark_color.clicked.connect(self.choose_watermark_color)
        self.watermark_color.setStyleSheet(
            "background-color: #999999; color: white;")
        settings_layout.addRow("水印颜色:", self.watermark_color)

        layout.addLayout(settings_layout)

        # 输出文件设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件名:"))

        self.watermark_output = QLineEdit()
        self.watermark_output.setPlaceholderText("添加水印后的文件名.pdf")
        output_layout.addWidget(self.watermark_output)

        self.btn_watermark_browse = QPushButton("📂 选择保存位置")
        self.btn_watermark_browse.clicked.connect(self.browse_output_file)
        self.btn_watermark_browse.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        output_layout.addWidget(self.btn_watermark_browse)

        layout.addLayout(output_layout)

        # 添加水印按钮
        self.btn_watermark = QPushButton("💧 添加水印")
        self.btn_watermark.clicked.connect(self.add_watermark)
        self.btn_watermark.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                min-height: 35px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_watermark)

        layout.addStretch()

        # 水印颜色
        self.watermark_rgb = (153, 153, 153)  # 默认灰色

    def setup_extract_tab(self):
        """设置提取文字标签页"""
        layout = QVBoxLayout(self.extract_tab)
        layout.setSpacing(15)

        # 说明
        info = QLabel("从PDF文件中提取文字内容")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # 提取选项
        options_layout = QVBoxLayout()

        self.extract_all = QCheckBox("提取所有页面")
        self.extract_all.setChecked(True)
        options_layout.addWidget(self.extract_all)

        page_range_layout = QHBoxLayout()
        page_range_layout.addWidget(QLabel("指定页面范围:"))

        self.extract_range = QLineEdit()
        self.extract_range.setPlaceholderText("例如: 1,3,5-10,15")
        self.extract_range.setEnabled(False)
        page_range_layout.addWidget(self.extract_range)

        options_layout.addLayout(page_range_layout)

        self.extract_all.toggled.connect(self.extract_range.setEnabled)

        layout.addLayout(options_layout)

        # 输出文件设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件名:"))

        self.extract_output = QLineEdit()
        self.extract_output.setPlaceholderText("提取的文字保存为.txt文件")
        output_layout.addWidget(self.extract_output)

        self.btn_extract_browse = QPushButton("📂 选择保存位置")
        self.btn_extract_browse.clicked.connect(self.browse_output_file)
        self.btn_extract_browse.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        output_layout.addWidget(self.btn_extract_browse)

        layout.addLayout(output_layout)

        # 提取文字按钮
        self.btn_extract = QPushButton("📝 提取文字")
        self.btn_extract.clicked.connect(self.extract_text)
        self.btn_extract.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                min-height: 35px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_extract)

        layout.addStretch()

    def setup_encrypt_tab(self):
        """设置加密/解密标签页"""
        layout = QVBoxLayout(self.encrypt_tab)
        layout.setSpacing(15)

        # 说明
        info = QLabel("为PDF文件添加密码保护或移除密码")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # 操作选择
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel("操作类型:"))

        self.encrypt_operation = QComboBox()
        self.encrypt_operation.addItems(["加密PDF", "解密PDF"])
        operation_layout.addWidget(self.encrypt_operation)

        layout.addLayout(operation_layout)

        # 密码设置
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码:"))

        self.encrypt_password = QLineEdit()
        self.encrypt_password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.encrypt_password)

        layout.addLayout(password_layout)

        # 输出文件设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件名:"))

        self.encrypt_output = QLineEdit()
        self.encrypt_output.setPlaceholderText("处理后的文件名.pdf")
        output_layout.addWidget(self.encrypt_output)

        self.btn_encrypt_browse = QPushButton("📂 选择保存位置")
        self.btn_encrypt_browse.clicked.connect(self.browse_output_file)
        self.btn_encrypt_browse.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        output_layout.addWidget(self.btn_encrypt_browse)

        layout.addLayout(output_layout)

        # 加密/解密按钮
        self.btn_encrypt = QPushButton("🔐 开始处理")
        self.btn_encrypt.clicked.connect(self.encrypt_pdf)
        self.btn_encrypt.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                min-height: 35px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_encrypt)

        layout.addStretch()

    def add_files(self):
        """添加PDF文件到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)")

        if files:
            for file in files:
                if file not in self.pdf_files:
                    self.pdf_files.append(file)
                    self.file_list.addItem(os.path.basename(file))

    def remove_files(self):
        """从列表中移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要移除的文件！")
            return

        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            self.pdf_files.pop(row)

    def clear_files(self):
        """清空文件列表"""
        if not self.pdf_files:
            return

        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.pdf_files.clear()
            self.file_list.clear()

    def browse_output_file(self):
        """浏览并选择输出文件位置"""
        sender = self.sender()
        if sender == self.btn_merge_browse:
            output = self.merge_output
            default_name = "合并后的文件.pdf"
        elif sender == self.btn_split_browse:
            output = self.split_output
            default_name = "拆分后的文件.pdf"
        elif sender == self.btn_watermark_browse:
            output = self.watermark_output
            default_name = "添加水印后的文件.pdf"
        elif sender == self.btn_extract_browse:
            output = self.extract_output
            default_name = "提取的文字.txt"
        elif sender == self.btn_encrypt_browse:
            output = self.encrypt_output
            default_name = "处理后的文件.pdf"
        else:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择保存位置", default_name,
            "PDF文件 (*.pdf);;文本文件 (*.txt)")

        if file_path:
            output.setText(file_path)

    def choose_watermark_color(self):
        """选择水印颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.watermark_rgb = (color.red(), color.green(), color.blue())
            self.watermark_color.setStyleSheet(
                f"background-color: {color.name()}; color: white;")

    def merge_pdfs(self):
        """合并多个PDF文件"""
        if len(self.pdf_files) < 2:
            QMessageBox.warning(self, "提示", "请至少选择两个PDF文件进行合并！")
            return

        output_path = self.merge_output.text()
        if not output_path:
            QMessageBox.warning(self, "提示", "请指定输出文件名！")
            return

        self.result_text.clear()
        self.result_text.append("🔗 开始合并PDF文件...\n")
        self.result_text.append("=" * 60 + "\n\n")

        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            merger = PyPDF2.PdfMerger()

            for i, pdf_file in enumerate(self.pdf_files):
                self.result_text.append(
                    f"正在处理: {os.path.basename(pdf_file)}\n")
                merger.append(pdf_file)

                # 更新进度
                progress = int((i + 1) / len(self.pdf_files) * 90)
                self.progress.setValue(progress)
                QApplication.processEvents()

            # 保存合并后的PDF
            merger.write(output_path)
            merger.close()

            self.progress.setValue(100)
            self.result_text.append(f"\n✅ 合并完成！文件已保存到: {output_path}\n")

            # 询问是否打开文件
            reply = QMessageBox.question(
                self, "完成", "PDF合并完成！是否打开文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                if os.name == 'nt':  # Windows系统
                    os.startfile(output_path)
                elif os.name == 'posix':  # Linux/Mac系统
                    subprocess.Popen(['xdg-open', output_path])

        except Exception as e:
            self.result_text.append(f"\n❌ 合并失败: {str(e)}\n")
            QMessageBox.critical(self, "错误", f"合并PDF失败: {str(e)}")

        self.progress.setVisible(False)

    def split_pdf(self):
        """拆分PDF文件"""
        if len(self.pdf_files) != 1:
            QMessageBox.warning(self, "提示", "请选择一个PDF文件进行拆分！")
            return

        output_path = self.split_output.text()
        if not output_path:
            QMessageBox.warning(self, "提示", "请指定输出文件名！")
            return

        page_range = self.split_range.text()
        if not page_range:
            QMessageBox.warning(self, "提示", "请指定要提取的页面范围！")
            return

        self.result_text.clear()
        self.result_text.append("✂️ 开始拆分PDF文件...\n")
        self.result_text.append("=" * 60 + "\n\n")

        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            # 解析页面范围
            pages_to_extract = self.parse_page_range(page_range)
            if not pages_to_extract:
                QMessageBox.warning(self, "提示", "无效的页面范围！")
                self.progress.setVisible(False)
                return

            # 打开PDF文件
            pdf_reader = PyPDF2.PdfReader(self.pdf_files[0])
            total_pages = len(pdf_reader.pages)

            self.result_text.append(f"文件总页数: {total_pages}\n")
            self.result_text.append(
                f"提取页面: {', '.join(map(str, pages_to_extract))}\n\n")

            # 创建新的PDF
            pdf_writer = PyPDF2.PdfWriter()

            # 添加指定页面
            for page_num in pages_to_extract:
                if page_num < 1 or page_num > total_pages:
                    self.result_text.append(f"⚠️ 页面 {page_num} 超出范围，已跳过\n")
                    continue

                pdf_writer.add_page(pdf_reader.pages[page_num - 1])
                self.result_text.append(f"✅ 已添加页面 {page_num}\n")

                # 更新进度
                progress = int(pages_to_extract.index(
                    page_num) / len(pages_to_extract) * 90)
                self.progress.setValue(progress)
                QApplication.processEvents()

            # 保存拆分后的PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)

            self.progress.setValue(100)
            self.result_text.append(f"\n✅ 拆分完成！文件已保存到: {output_path}\n")

            # 询问是否打开文件
            reply = QMessageBox.question(
                self, "完成", "PDF拆分完成！是否打开文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                if os.name == 'nt':  # Windows系统
                    os.startfile(output_path)
                elif os.name == 'posix':  # Linux/Mac系统
                    subprocess.Popen(['xdg-open', output_path])

        except Exception as e:
            self.result_text.append(f"\n❌ 拆分失败: {str(e)}\n")
            QMessageBox.critical(self, "错误", f"拆分PDF失败: {str(e)}")

        self.progress.setVisible(False)

    def add_watermark(self):
        """为PDF添加水印"""
        if len(self.pdf_files) != 1:
            QMessageBox.warning(self, "提示", "请选择一个PDF文件添加水印！")
            return

        output_path = self.watermark_output.text()
        if not output_path:
            QMessageBox.warning(self, "提示", "请指定输出文件名！")
            return

        watermark_text = self.watermark_text.text()
        if not watermark_text:
            QMessageBox.warning(self, "提示", "请输入水印文本！")
            return

        self.result_text.clear()
        self.result_text.append("💧 开始添加水印...\n")
        self.result_text.append("=" * 60 + "\n\n")

        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            # 创建水印PDF
            watermark_pdf = self.create_watermark_pdf(
                watermark_text,
                self.watermark_opacity.value() / 100,
                self.watermark_rotation.value(),
                self.watermark_rgb
            )

            # 打开原始PDF
            pdf_reader = PyPDF2.PdfReader(self.pdf_files[0])
            pdf_writer = PyPDF2.PdfWriter()

            # 为每一页添加水印
            total_pages = len(pdf_reader.pages)
            for i in range(total_pages):
                page = pdf_reader.pages[i]
                page.merge_page(watermark_pdf.pages[0])
                pdf_writer.add_page(page)

                # 更新进度
                progress = int((i + 1) / total_pages * 90)
                self.progress.setValue(progress)
                QApplication.processEvents()

            # 保存添加水印后的PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)

            self.progress.setValue(100)
            self.result_text.append(f"\n✅ 水印添加完成！文件已保存到: {output_path}\n")

            # 询问是否打开文件
            reply = QMessageBox.question(
                self, "完成", "水印添加完成！是否打开文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                if os.name == 'nt':  # Windows系统
                    os.startfile(output_path)
                elif os.name == 'posix':  # Linux/Mac系统
                    subprocess.Popen(['xdg-open', output_path])

        except Exception as e:
            self.result_text.append(f"\n❌ 添加水印失败: {str(e)}\n")
            QMessageBox.critical(self, "错误", f"添加水印失败: {str(e)}")

        self.progress.setVisible(False)

    def create_watermark_pdf(self, text, opacity, rotation, color):
        """创建水印PDF"""
        # 创建一个A4大小的PDF页面
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # 设置水印样式
        can.setFillColorRGB(color[0]/255, color[1] /
                            255, color[2]/255, alpha=opacity)
        can.setFont("Helvetica", 60)

        # 保存当前状态
        can.saveState()

        # 旋转画布
        can.translate(A4[0] / 2, A4[1] / 2)
        can.rotate(rotation)

        # 绘制水印文本
        can.drawCentredString(0, 0, text)

        # 恢复状态
        can.restoreState()

        # 保存画布
        can.save()

        # 将BytesIO转换为PdfReader对象
        packet.seek(0)
        watermark_pdf = PyPDF2.PdfReader(packet)

        return watermark_pdf

    def extract_text(self):
        """从PDF中提取文字"""
        if len(self.pdf_files) != 1:
            QMessageBox.warning(self, "提示", "请选择一个PDF文件提取文字！")
            return

        output_path = self.extract_output.text()
        if not output_path:
            QMessageBox.warning(self, "提示", "请指定输出文件名！")
            return

        self.result_text.clear()
        self.result_text.append("📝 开始提取文字...\n")
        self.result_text.append("=" * 60 + "\n\n")

        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            # 打开PDF文件
            with pdfplumber.open(self.pdf_files[0]) as pdf:
                total_pages = len(pdf.pages)

                # 确定要提取的页面
                if self.extract_all.isChecked():
                    pages_to_extract = range(1, total_pages + 1)
                else:
                    page_range = self.extract_range.text()
                    pages_to_extract = self.parse_page_range(page_range)
                    if not pages_to_extract:
                        QMessageBox.warning(self, "提示", "无效的页面范围！")
                        self.progress.setVisible(False)
                        return

                # 提取文字
                extracted_text = ""
                for i, page_num in enumerate(pages_to_extract):
                    if page_num < 1 or page_num > total_pages:
                        self.result_text.append(f"⚠️ 页面 {page_num} 超出范围，已跳过\n")
                        continue

                    page = pdf.pages[page_num - 1]
                    text = page.extract_text()
                    if text:
                        extracted_text += f"--- 第 {page_num} 页 ---\n\n{text}\n\n"

                    # 更新进度
                    progress = int((i + 1) / len(pages_to_extract) * 90)
                    self.progress.setValue(progress)
                    QApplication.processEvents()

                # 保存提取的文字
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(extracted_text)

                self.progress.setValue(100)
                self.result_text.append(f"\n✅ 文字提取完成！已保存到: {output_path}\n")

                # 询问是否打开文件
                reply = QMessageBox.question(
                    self, "完成", "文字提取完成！是否打开文件？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                if reply == QMessageBox.StandardButton.Yes:
                    if os.name == 'nt':  # Windows系统
                        os.startfile(output_path)
                    elif os.name == 'posix':  # Linux/Mac系统
                        subprocess.Popen(['xdg-open', output_path])

        except Exception as e:
            self.result_text.append(f"\n❌ 提取文字失败: {str(e)}\n")
            QMessageBox.critical(self, "错误", f"提取文字失败: {str(e)}")

        self.progress.setVisible(False)

    def encrypt_pdf(self):
        """加密或解密PDF文件"""
        if len(self.pdf_files) != 1:
            QMessageBox.warning(self, "提示", "请选择一个PDF文件进行处理！")
            return

        output_path = self.encrypt_output.text()
        if not output_path:
            QMessageBox.warning(self, "提示", "请指定输出文件名！")
            return

        password = self.encrypt_password.text()
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码！")
            return

        operation = self.encrypt_operation.currentText()

        self.result_text.clear()
        self.result_text.append(f"🔐 开始{operation}...\n")
        self.result_text.append("=" * 60 + "\n\n")

        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            if operation == "加密PDF":
                # 加密PDF
                pdf_reader = PyPDF2.PdfReader(self.pdf_files[0])
                pdf_writer = PyPDF2.PdfWriter()

                # 复制所有页面
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

                # 添加密码保护
                pdf_writer.encrypt(password)

                # 保存加密后的PDF
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)

                self.result_text.append(f"✅ PDF加密完成！密码已设置为: {password}\n")

            else:  # 解密PDF
                # 解密PDF
                pdf_reader = PyPDF2.PdfReader(self.pdf_files[0])

                # 检查PDF是否加密
                if not pdf_reader.is_encrypted:
                    QMessageBox.warning(self, "提示", "该PDF文件未加密！")
                    self.progress.setVisible(False)
                    return

                # 尝试解密
                try:
                    pdf_reader.decrypt(password)
                except:
                    QMessageBox.warning(self, "提示", "密码错误，无法解密PDF！")
                    self.progress.setVisible(False)
                    return

                pdf_writer = PyPDF2.PdfWriter()

                # 复制所有页面
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

                # 保存解密后的PDF
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)

                self.result_text.append(f"✅ PDF解密完成！\n")

            self.progress.setValue(100)
            self.result_text.append(f"文件已保存到: {output_path}\n")

            # 询问是否打开文件
            reply = QMessageBox.question(
                self, "完成", f"{operation}完成！是否打开文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                if os.name == 'nt':  # Windows系统
                    os.startfile(output_path)
                elif os.name == 'posix':  # Linux/Mac系统
                    subprocess.Popen(['xdg-open', output_path])

        except Exception as e:
            self.result_text.append(f"\n❌ {operation}失败: {str(e)}\n")
            QMessageBox.critical(self, "错误", f"{operation}失败: {str(e)}")

        self.progress.setVisible(False)

    def parse_page_range(self, page_range):
        """解析页面范围字符串，返回页面列表"""
        pages = []
        parts = page_range.split(',')

        for part in parts:
            part = part.strip()
            if '-' in part:
                # 处理范围，如 "5-10"
                start, end = part.split('-')
                try:
                    start = int(start)
                    end = int(end)
                    pages.extend(range(start, end + 1))
                except ValueError:
                    continue
            else:
                # 处理单个页面，如 "5"
                try:
                    pages.append(int(part))
                except ValueError:
                    continue

        # 去重并排序
        pages = sorted(list(set(pages)))
        return pages


# ========== 功能5：文件批量筛选 ==========
class OfficeBatchPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("📂 文件批量筛选")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addSpacing(10)

        self.setup_filter_content(layout)

    def setup_filter_content(self, parent_layout):
        group_font = QFont()
        group_font.setPointSize(15)

        file_group = QGroupBox("待筛选文件")
        file_group.setFont(group_font)
        file_layout = QVBoxLayout(file_group)

        self.file_list = DropFileListWidget()
        self.file_list.files_added.connect(self.on_files_added)
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QListWidget::item:selected {
                background-color: #FFE4B5;
                color: #333;
            }
        """)
        file_layout.addWidget(self.file_list, stretch=1)

        file_btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ 添加")
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_remove_files = QPushButton("🗑️ 移除")
        self.btn_remove_files.clicked.connect(self.remove_selected_files)
        self.btn_clear_files = QPushButton("🧹 清空")
        self.btn_clear_files.clicked.connect(self.clear_files)
        for btn in [self.btn_add_files, self.btn_remove_files, self.btn_clear_files]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB347;
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 4px;
                    min-height: 26px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #FF9500;
                }
            """)
        file_btn_layout.addWidget(self.btn_add_files)
        file_btn_layout.addWidget(self.btn_remove_files)
        file_btn_layout.addWidget(self.btn_clear_files)
        file_btn_layout.addStretch()
        self.file_count_label = QLabel("共 0 个文件")
        self.file_count_label.setStyleSheet("color: #666; font-weight: bold; font-size: 10pt;")
        file_btn_layout.addWidget(self.file_count_label)
        file_layout.addLayout(file_btn_layout)

        parent_layout.addWidget(file_group, stretch=3)

        name_group = QGroupBox("筛选名单")
        name_group.setFont(group_font)
        name_layout = QVBoxLayout(name_group)

        self.name_text = QTextEdit()
        self.name_text.setPlaceholderText("输入需要筛选的人名（每行一个），支持从 Excel 导入\n例如：\n张三\n王五\n赵六")
        self.name_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-size: 10pt;
            }
        """)
        name_layout.addWidget(self.name_text, stretch=1)

        name_btn_layout = QHBoxLayout()
        self.btn_load_names = QPushButton("📄 导入名单")
        self.btn_load_names.clicked.connect(self.load_names_from_file)
        self.btn_clear_names = QPushButton("🧹 清空")
        self.btn_clear_names.clicked.connect(lambda: self.name_text.clear())
        for btn in [self.btn_load_names, self.btn_clear_names]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB347;
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 4px;
                    min-height: 26px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #FF9500;
                }
            """)
        name_btn_layout.addWidget(self.btn_load_names)
        name_btn_layout.addWidget(self.btn_clear_names)
        name_btn_layout.addStretch()
        self.name_count_label = QLabel("共 0 个名称")
        self.name_count_label.setStyleSheet("color: #666; font-weight: bold; font-size: 10pt;")
        name_btn_layout.addWidget(self.name_count_label)
        name_layout.addLayout(name_btn_layout)

        self.name_text.textChanged.connect(self.update_name_count)

        parent_layout.addWidget(name_group, stretch=1)

        option_group = QGroupBox("筛选选项")
        option_group.setFont(group_font)
        option_layout = QHBoxLayout(option_group)

        self.check_case_sensitive = QCheckBox("区分大小写")
        self.check_case_sensitive.setChecked(False)
        option_layout.addWidget(self.check_case_sensitive)

        self.check_match_name_only = QCheckBox("仅匹配文件名（不含扩展名）")
        self.check_match_name_only.setChecked(False)
        option_layout.addWidget(self.check_match_name_only)

        option_layout.addStretch()
        parent_layout.addWidget(option_group)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(0)
        self.btn_filter = QPushButton("🔍 开始筛选")
        self.btn_filter.setMinimumWidth(110)
        self.btn_filter.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                min-height: 26px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #FF9500; }
        """)
        self.btn_filter.clicked.connect(self.filter_files)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_filter)
        action_layout.addStretch()
        parent_layout.addLayout(action_layout)

        result_group = QGroupBox("筛选结果")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_info = QLabel("请先添加文件和筛选名单，然后点击「开始筛选」")
        self.result_info.setStyleSheet("color: #666; font-size: 10pt; padding: 4px;")
        result_layout.addWidget(self.result_info)

        self.result_list = QListWidget()
        self.result_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.result_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QListWidget::item:selected {
                background-color: #C8E6C9;
                color: #333;
            }
        """)
        result_layout.addWidget(self.result_list, stretch=1)

        result_btn_layout = QHBoxLayout()
        self.btn_copy_selected = QPushButton("📋 复制选中到...")
        self.btn_copy_selected.clicked.connect(self.copy_selected_files)
        self.btn_copy_selected.setMinimumWidth(110)
        self.btn_copy_all = QPushButton("📁 复制全部到...")
        self.btn_copy_all.clicked.connect(self.copy_all_filtered)
        self.btn_copy_all.setMinimumWidth(110)
        for btn in [self.btn_copy_selected, self.btn_copy_all]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB347;
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 4px;
                    min-height: 26px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #FF9500;
                }
            """)
        result_btn_layout.addWidget(self.btn_copy_selected)
        result_btn_layout.addWidget(self.btn_copy_all)
        result_btn_layout.addStretch()
        result_layout.addLayout(result_btn_layout)

        parent_layout.addWidget(result_group, stretch=3)

        self.filtered_files = []

    def on_files_added(self, file_paths):
        for fp in file_paths:
            if os.path.isfile(fp):
                name = os.path.basename(fp)
                exists = False
                for i in range(self.file_list.count()):
                    if self.file_list.item(i).data(Qt.ItemDataRole.UserRole) == fp:
                        exists = True
                        break
                if not exists:
                    item = QListWidgetItem(f"📄 {name}")
                    item.setData(Qt.ItemDataRole.UserRole, fp)
                    item.setToolTip(fp)
                    self.file_list.addItem(item)
        self.update_file_count()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*.*)")
        if files:
            self.on_files_added(files)

    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        self.update_file_count()

    def clear_files(self):
        self.file_list.clear()
        self.update_file_count()

    def update_file_count(self):
        self.file_count_label.setText(f"共 {self.file_list.count()} 个文件")

    def update_name_count(self):
        text = self.name_text.toPlainText().strip()
        if not text:
            self.name_count_label.setText("共 0 个名称")
            return
        names = [line.strip() for line in text.split('\n') if line.strip()]
        self.name_count_label.setText(f"共 {len(names)} 个名称")

    def load_names_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择名单文件", "", "Excel文件 (*.xlsx *.xls);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            try:
                if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(file_path)
                        ws = wb.active
                        names = []
                        for row in ws.iter_rows(values_only=True):
                            for cell in row:
                                if cell and str(cell).strip():
                                    names.append(str(cell).strip())
                        self.name_text.setPlainText('\n'.join(names))
                    except ImportError:
                        QMessageBox.warning(self, "提示", "请先安装 openpyxl 库：pip install openpyxl")
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.name_text.setPlainText(content)
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                self.name_text.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"无法读取文件：{str(e)}")

    def filter_files(self):
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "提示", "请先添加待筛选的文件！")
            return

        name_text = self.name_text.toPlainText().strip()
        if not name_text:
            QMessageBox.warning(self, "提示", "请先输入筛选名单！")
            return

        case_sensitive = self.check_case_sensitive.isChecked()
        match_name_only = self.check_match_name_only.isChecked()

        names = [line.strip() for line in name_text.split('\n') if line.strip()]
        if not case_sensitive:
            names = [n.lower() for n in names]

        self.filtered_files = []
        self.result_list.clear()

        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            file_name = os.path.basename(file_path)

            if match_name_only:
                compare_name = os.path.splitext(file_name)[0]
            else:
                compare_name = file_name

            if not case_sensitive:
                compare_name = compare_name.lower()

            for name in names:
                if name in compare_name:
                    self.filtered_files.append(file_path)
                    result_item = QListWidgetItem(f"✅ {file_name}")
                    result_item.setData(Qt.ItemDataRole.UserRole, file_path)
                    result_item.setToolTip(file_path)
                    self.result_list.addItem(result_item)
                    break

        if self.filtered_files:
            self.result_info.setText(
                f"找到 <span style='color:#4CAF50;font-weight:bold;'>{len(self.filtered_files)}</span> 个匹配文件"
            )
        else:
            self.result_info.setText(
                "<span style='color:#f44336;font-weight:bold;'>未找到任何匹配文件</span>"
            )

    def copy_selected_files(self):
        selected = self.result_list.selectedItems()
        files_to_copy = []
        for item in selected:
            fp = item.data(Qt.ItemDataRole.UserRole)
            if fp and os.path.isfile(fp):
                files_to_copy.append(fp)

        if not files_to_copy:
            QMessageBox.warning(self, "提示", "请先在筛选结果中选择要复制的文件！")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if not dest_dir:
            return

        success = 0
        errors = []
        for fp in files_to_copy:
            try:
                shutil.copy2(fp, os.path.join(dest_dir, os.path.basename(fp)))
                success += 1
            except Exception as e:
                errors.append(f"{os.path.basename(fp)}: {str(e)}")

        msg = f"成功复制 {success} 个文件"
        if errors:
            msg += f"\n失败 {len(errors)} 个：\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... 还有 {len(errors)-5} 个"
            QMessageBox.warning(self, "部分文件复制失败", msg)
        else:
            QMessageBox.information(self, "完成", msg)

    def copy_all_filtered(self):
        if not self.filtered_files:
            QMessageBox.warning(self, "提示", "没有可复制的筛选结果！")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if not dest_dir:
            return

        success = 0
        errors = []
        for fp in self.filtered_files:
            try:
                shutil.copy2(fp, os.path.join(dest_dir, os.path.basename(fp)))
                success += 1
            except Exception as e:
                errors.append(f"{os.path.basename(fp)}: {str(e)}")

        msg = f"成功复制 {success} 个文件"
        if errors:
            msg += f"\n失败 {len(errors)} 个：\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... 还有 {len(errors)-5} 个"
            QMessageBox.warning(self, "部分文件复制失败", msg)
        else:
            QMessageBox.information(self, "完成", msg)


class DropFileListWidget(QListWidget):
    files_added = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            if file_paths:
                self.files_added.emit(file_paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ========== 功能6：文件名称提取器 ==========
# 新增功能: 文件名称提取器，批量提取文件名中的关键信息
class FileNameCut(QWidget):
    def __init__(self):
        super().__init__()
        self.folder_path = None
        self.extracted_data = []
        self.setup_ui()

    def setup_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("✂️ 文件名称提取器")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 文件夹选择区域
        folder_group = QGroupBox("选择文件夹")
        group_font = QFont()
        group_font.setPointSize(15)
        folder_group.setFont(group_font)
        folder_layout = QVBoxLayout(folder_group)

        # 文件夹路径选择行
        path_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("请选择包含要处理文件的文件夹...")
        self.folder_path_edit.setReadOnly(True)

        # 选择文件夹按钮
        btn_select = QPushButton("📂 选择文件夹")
        btn_select.setMinimumWidth(130)
        btn_select.clicked.connect(self.select_folder)
        btn_select.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        path_layout.addWidget(self.folder_path_edit)
        path_layout.addWidget(btn_select)
        folder_layout.addLayout(path_layout)

        # 包含子文件夹选项
        self.check_subfolders = QCheckBox("包含子文件夹")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_subfolders.setFont(check_font)
        self.check_subfolders.setChecked(False)
        folder_layout.addWidget(self.check_subfolders)

        # 排除文件后缀选项
        self.check_no_ext = QCheckBox("提取时排除文件后缀")
        check_font2 = QFont()
        check_font2.setPointSize(12)
        self.check_no_ext.setFont(check_font2)
        self.check_no_ext.setChecked(True)
        folder_layout.addWidget(self.check_no_ext)

        layout.addWidget(folder_group)

        # 提取规则设置
        rule_group = QGroupBox("提取规则")
        rule_group.setFont(group_font)
        rule_layout = QVBoxLayout(rule_group)

        # 创建统一的水平布局
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(20)  # 增加间距

        # 分隔符设置
        separator_layout = QHBoxLayout()
        separator_label = QLabel("分隔符:")
        separator_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-weight: bold;
                background-color: #f0f0f0;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 70px;
            }
        """)
        self.separator_edit = QLineEdit()
        # self.separator_edit.setPlaceholderText("_ 或 - 或 .")
        self.separator_edit.setText("_")
        self.separator_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 28px;
            }
        """)
        separator_layout.addWidget(separator_label)
        separator_layout.addWidget(self.separator_edit)
        settings_layout.addLayout(separator_layout)

        # 提取部分选择
        extract_layout = QHBoxLayout()
        extract_label = QLabel("提取部分:")
        extract_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-weight: bold;
                background-color: #f0f0f0;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 70px;
            }
        """)
        self.extract_part = QSpinBox()
        self.extract_part.setMinimum(1)
        self.extract_part.setMaximum(10)
        self.extract_part.setValue(1)
        self.extract_part.setStyleSheet("""
            QSpinBox {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 28px;
            }
        """)
        extract_layout.addWidget(extract_label)
        extract_layout.addWidget(self.extract_part)
        settings_layout.addLayout(extract_layout)

        # 文件扩展名过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("文件扩展名:")
        filter_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-weight: bold;
                background-color: #f0f0f0;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 70px;
            }
        """)
        self.extension_edit = QLineEdit()
        self.extension_edit.setPlaceholderText(".pdf或.docx 不填默认所有文件类型")
        self.extension_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 28px;
            }
        """)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.extension_edit)
        settings_layout.addLayout(filter_layout)

        # 添加弹性空间，使控件靠左对齐
        settings_layout.addStretch()

        rule_layout.addLayout(settings_layout)
        layout.addWidget(rule_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.btn_preview = QPushButton("👁️ 预览结果")
        self.btn_preview.clicked.connect(self.preview_extraction)
        self.btn_preview.setEnabled(False)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        self.btn_export = QPushButton("📊 导出到Excel")
        self.btn_export.clicked.connect(self.export_to_excel)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        button_layout.addWidget(self.btn_preview)
        button_layout.addWidget(self.btn_export)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 结果显示区域
        result_group = QGroupBox("提取结果")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["文件名", "提取内容"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setMinimumHeight(300)
        # 确保表格行为正确
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        result_layout.addWidget(self.result_table)

        layout.addWidget(result_group)

        # 状态栏
        self.status_label = QLabel("请选择文件夹")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_path = folder
            self.folder_path_edit.setText(folder)
            self.btn_preview.setEnabled(True)
            self.status_label.setText(f"已选择文件夹: {folder}")

    def get_files(self):
        """获取要处理的文件列表"""
        files = []
        separator = self.separator_edit.text()
        extension = self.extension_edit.text().strip().lower()

        try:
            if self.check_subfolders.isChecked():
                # 包含子文件夹
                for root, dirs, filenames in os.walk(self.folder_path):
                    for filename in filenames:
                        # 检查文件扩展名
                        if not extension or filename.lower().endswith(extension):
                            files.append(os.path.join(root, filename))
                            # 限制文件数量
                            if len(files) >= 1000:
                                QMessageBox.warning(
                                    self, "提示", "文件数量过多，仅处理前1000个文件")
                                return files
            else:
                # 不包含子文件夹
                for filename in os.listdir(self.folder_path):
                    filepath = os.path.join(self.folder_path, filename)
                    if os.path.isfile(filepath):
                        # 检查文件扩展名
                        if not extension or filename.lower().endswith(extension):
                            files.append(filepath)
                            # 限制文件数量
                            if len(files) >= 1000:
                                QMessageBox.warning(
                                    self, "提示", "文件数量过多，仅处理前1000个文件")
                                return files
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件列表失败: {str(e)}")
            return []

        return files

    def preview_extraction(self):
        """预览提取结果"""
        try:
            if not self.folder_path:
                QMessageBox.warning(self, "提示", "请先选择文件夹！")
                return

            separator = self.separator_edit.text()
            if not separator:
                QMessageBox.warning(self, "提示", "请输入分隔符！")
                return

            part_index = self.extract_part.value() - 1  # 转换为0-based索引

            # 获取文件列表
            files = self.get_files()
            if not files:
                QMessageBox.warning(self, "提示", "没有找到符合条件的文件！")
                return

            # 清空之前的结果并确保列数正确
            self.result_table.clearContents()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(2)
            self.extracted_data = []

            # 处理每个文件
            for filepath in files:
                filename = os.path.basename(filepath)

                # 如果勾选排除后缀，先去掉扩展名再分割
                if self.check_no_ext.isChecked():
                    name_without_ext = os.path.splitext(filename)[0]
                    parts = name_without_ext.split(separator)
                else:
                    parts = filename.split(separator)

                # 提取指定部分
                if part_index < len(parts):
                    extracted = parts[part_index]
                else:
                    extracted = ""

                # 添加到表格
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)
                self.result_table.setItem(row, 0, QTableWidgetItem(filename))
                self.result_table.setItem(row, 1, QTableWidgetItem(extracted))

                # 保存数据以便导出
                self.extracted_data.append((filename, extracted))

            # 更新状态
            self.status_label.setText(f"已处理 {len(files)} 个文件")
            self.btn_export.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览失败: {str(e)}")
            self.status_label.setText("预览失败")

    def export_to_excel(self):
        """导出结果到Excel"""
        if not self.extracted_data:
            QMessageBox.warning(self, "提示", "没有可导出的数据！")
            return

        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "提取结果.xlsx", "Excel文件 (*.xlsx)")

        if not file_path:
            return

        try:
            # 使用openpyxl创建Excel文件
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill

            # 创建工作簿
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "文件名提取结果"

            # 设置表头
            headers = ["文件名", "提取内容"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(
                    start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")

            # 填充数据
            for row, (filename, extracted) in enumerate(self.extracted_data, 2):
                ws.cell(row=row, column=1, value=filename)
                ws.cell(row=row, column=2, value=extracted)

            # 调整列宽
            ws.column_dimensions['A'].width = 50
            ws.column_dimensions['B'].width = 30

            # 保存文件
            wb.save(file_path)

            # 更新状态
            self.status_label.setText(f"结果已导出到: {file_path}")

            # 询问是否打开文件
            reply = QMessageBox.question(
                self, "完成", "导出成功！是否打开文件？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                if os.name == 'nt':  # Windows系统
                    os.startfile(file_path)
                elif os.name == 'posix':  # Linux/Mac系统
                    subprocess.Popen(['xdg-open', file_path])

        except ImportError:
            QMessageBox.critical(
                self, "错误", "缺少openpyxl库，请先安装: pip install openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出Excel失败: {str(e)}")


# ========== 功能7：OCR 文字识别 ==========
class OCRPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        label = QLabel("🔍 OCR 文字识别工具")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        label.setFont(title_font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #666;")
        layout.addWidget(label)

        info = QLabel("此功能正在开发中，敬请期待...")
        info_font = QFont()
        info_font.setPointSize(14)
        info.setFont(info_font)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #999; margin-top: 20px;")
        layout.addWidget(info)


# ========== 功能8：文档拆分工具 ==========
class SplitWorker(QThread):
    """后台拆分工作线程"""
    progress_updated = pyqtSignal(int, str)
    split_completed = pyqtSignal(list)
    split_error = pyqtSignal(str)
    needs_input_count = pyqtSignal(int)

    def __init__(self, file_list, rule, params, output_dir, naming_template, output_format, input_names=None):
        super().__init__()
        self.file_list = file_list
        self.rule = rule
        self.params = params
        self.output_dir = output_dir
        self.naming_template = naming_template
        self.output_format = output_format
        self.input_names = input_names or []
        self._is_running = True

    def run(self):
        all_output_files = []
        total_files = len(self.file_list)

        # 如果使用了{输入}变量，先预计算拆分组数并校验
        if "{输入}" in self.naming_template and self.input_names:
            total_groups = self._count_total_groups()
            if total_groups != len(self.input_names):
                self.needs_input_count.emit(total_groups)
                return

        for i, file_path in enumerate(self.file_list):
            if not self._is_running:
                break

            self.progress_updated.emit(
                int(i / total_files * 100),
                f"正在处理: {os.path.basename(file_path)}"
            )

            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.pdf':
                    output_files = self.split_pdf(file_path)
                elif ext == '.docx':
                    output_files = self.split_word(file_path)
                elif ext == '.xlsx':
                    output_files = self.split_excel(file_path)
                else:
                    self.split_error.emit(f"不支持的文件格式: {ext}")
                    continue

                all_output_files.extend(output_files)
            except Exception as e:
                self.split_error.emit(
                    f"拆分 {os.path.basename(file_path)} 失败: {str(e)}")

        self.progress_updated.emit(100, "拆分完成！")
        self.split_completed.emit(all_output_files)

    def stop(self):
        self._is_running = False
        self.wait()

    def _count_total_groups(self):
        """预计算拆分后的总文件数"""
        total = 0
        for file_path in self.file_list:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.pdf':
                    total += self._count_pdf_groups(file_path)
                elif ext == '.docx':
                    total += self._count_word_groups(file_path)
                elif ext == '.xlsx':
                    total += self._count_excel_groups(file_path)
            except Exception:
                pass
        return total

    def _count_pdf_groups(self, file_path):
        reader = PyPDF2.PdfReader(file_path)
        total_pages = len(reader.pages)
        if self.rule == "by_page_count":
            n = self.params.get('pages_per_split', 5)
            return (total_pages + n - 1) // n
        elif self.rule == "by_custom_pages":
            groups = self.parse_custom_ranges(self.params.get('page_ranges', ''))
            return len(groups)
        elif self.rule == "by_bookmark":
            outlines = reader.outline
            if outlines:
                count = 0
                def walk(items):
                    nonlocal count
                    for item in items:
                        if isinstance(item, list):
                            walk(item)
                        else:
                            count += 1
                walk(outlines)
                return max(count, 1)
            else:
                n = self.params.get('pages_per_split', 5)
                return (total_pages + n - 1) // n
        elif self.rule == "by_size":
            target_size = self.params.get('target_size_mb', 5) * 1024 * 1024
            file_size = os.path.getsize(file_path)
            avg_page_size = file_size / max(total_pages, 1)
            pages_per = max(1, int(target_size / max(avg_page_size, 1)))
            return (total_pages + pages_per - 1) // pages_per
        return 0

    def _count_word_groups(self, file_path):
        if not HAS_PYTHON_DOCX:
            return 0

        if self.rule == "by_heading":
            doc = DocxDocument(file_path)
            count = 0
            for para in doc.paragraphs:
                if para.style.name.startswith('Heading'):
                    count += 1
            return max(count, 1)

        if self.rule in ("by_page_count", "by_custom_pages"):
            # 优先使用 Word COM 获取精确页数
            if HAS_WIN32COM:
                try:
                    word_app = win32.Dispatch("Word.Application")
                    word_app.Visible = False
                    word_app.DisplayAlerts = 0
                    doc = word_app.Documents.Open(os.path.abspath(file_path))
                    total_pages = doc.ComputeStatistics(2)  # wdStatisticPages
                    doc.Close()
                    word_app.Quit()

                    if self.rule == "by_page_count":
                        n = self.params.get('pages_per_split', 5)
                        return (total_pages + n - 1) // n
                    elif self.rule == "by_custom_pages":
                        range_groups = self.parse_custom_ranges(
                            self.params.get('page_ranges', ''))
                        valid_count = 0
                        for grp in range_groups:
                            if any(1 <= p <= total_pages for p in grp):
                                valid_count += 1
                        return max(valid_count, 1)
                except Exception:
                    pass

            # 回退：python-docx 段落估算
            doc = DocxDocument(file_path)
            total_paras = len(doc.paragraphs)
            if self.rule == "by_page_count":
                n = self.params.get('pages_per_split', 5)
                paras_per = n * 15
                return (total_paras + paras_per - 1) // paras_per if paras_per > 0 else 1
            elif self.rule == "by_custom_pages":
                range_groups = self.parse_custom_ranges(
                    self.params.get('page_ranges', ''))
                est_total_pages = max(1, total_paras // 15)
                valid_count = 0
                for grp in range_groups:
                    if any(1 <= p <= est_total_pages for p in grp):
                        valid_count += 1
                return max(valid_count, 1)

        return 1

    def _count_excel_groups(self, file_path):
        wb = openpyxl.load_workbook(file_path, read_only=True)
        if self.rule == "by_row_count":
            rows_per = self.params.get('rows_per_split', 100)
            count = 0
            for sn in wb.sheetnames:
                ws = wb[sn]
                data_rows = max(0, (ws.max_row or 1) - 1)
                if data_rows > 0:
                    count += (data_rows + rows_per - 1) // rows_per
            wb.close()
            return max(count, 1)
        elif self.rule == "by_sheet":
            sheets_per = self.params.get('sheets_per_split', 1)
            count = (len(wb.sheetnames) + sheets_per - 1) // sheets_per
            wb.close()
            return max(count, 1)
        wb.close()
        return 1

    # ===== 命名模板 =====
    def format_name(self, template, source_path, index, page_group=None, title=""):
        name_without_ext = os.path.splitext(os.path.basename(source_path))[0]
        now = datetime.now()

        page_range_str = ""
        if page_group:
            pages = list(page_group)
            if pages:
                page_range_str = f"{pages[0]}-{pages[-1]}"

        result = template
        result = result.replace("{原名}", name_without_ext)
        result = result.replace("{序号}", str(index))
        result = result.replace("{日期}", now.strftime("%Y%m%d"))
        result = result.replace("{页码范围}", page_range_str)
        result = result.replace("{标题}", title if title else f"第{index}部分")

        # 替换{输入}变量
        if "{输入}" in result and self.input_names:
            if index <= len(self.input_names):
                result = result.replace("{输入}", self.input_names[index - 1])
            else:
                result = result.replace("{输入}", f"未知{index}")

        fmt_matches = re.findall(r'\{序号:(\w+)\}', result)
        for fmt in fmt_matches:
            formatted = format(index, fmt)
            result = result.replace(f"{{序号:{fmt}}}", formatted)

        # 处理文件名冲突
        base = result
        counter = 1
        while os.path.exists(os.path.join(self.output_dir, result + '.pdf')) or \
                os.path.exists(os.path.join(self.output_dir, result + '.docx')) or \
                os.path.exists(os.path.join(self.output_dir, result + '.xlsx')):
            result = f"{base}({counter})"
            counter += 1

        return result

    # ===== 页码范围解析 =====
    def parse_custom_ranges(self, range_str):
        """解析自定义页码范围，如 '1-3,4-6,7-10' → [[1,2,3],[4,5,6],[7,8,9,10]]"""
        groups = []
        parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                try:
                    groups.append(list(range(int(start), int(end) + 1)))
                except ValueError:
                    continue
            else:
                try:
                    groups.append([int(part)])
                except ValueError:
                    continue
        return groups

    # ===== PDF 拆分 =====
    def split_pdf(self, file_path):
        reader = PyPDF2.PdfReader(file_path)
        total_pages = len(reader.pages)
        groups = []  # 每个元素是 (页码列表, 标题)

        if self.rule == "by_page_count":
            pages_per_split = self.params.get('pages_per_split', 5)
            for start in range(0, total_pages, pages_per_split):
                end = min(start + pages_per_split, total_pages)
                groups.append((list(range(start + 1, end + 1)), ""))

        elif self.rule == "by_custom_pages":
            range_groups = self.parse_custom_ranges(
                self.params.get('page_ranges', ''))
            for grp in range_groups:
                valid = [p for p in grp if 1 <= p <= total_pages]
                if valid:
                    groups.append((valid, ""))

        elif self.rule == "by_bookmark":
            bookmark_groups = self._get_pdf_bookmark_ranges(
                reader, total_pages)
            if bookmark_groups:
                groups = bookmark_groups
            else:
                # 无书签时回退为按页数拆分
                pages_per_split = self.params.get('pages_per_split', 5)
                for start in range(0, total_pages, pages_per_split):
                    end = min(start + pages_per_split, total_pages)
                    groups.append((list(range(start + 1, end + 1)), ""))

        elif self.rule == "by_size":
            target_size = self.params.get('target_size_mb', 5) * 1024 * 1024
            file_size = os.path.getsize(file_path)
            avg_page_size = file_size / max(total_pages, 1)
            pages_per_group = max(1, int(target_size / max(avg_page_size, 1)))
            for start in range(0, total_pages, pages_per_group):
                end = min(start + pages_per_group, total_pages)
                groups.append((list(range(start + 1, end + 1)), ""))

        if not groups:
            return []

        output_files = []
        for i, (page_group, title) in enumerate(groups):
            writer = PyPDF2.PdfWriter()
            for page_num in page_group:
                if 1 <= page_num <= total_pages:
                    writer.add_page(reader.pages[page_num - 1])

            output_name = self.format_name(
                self.naming_template, file_path, i + 1, page_group, title)
            output_path = os.path.join(self.output_dir, output_name + '.pdf')
            with open(output_path, 'wb') as f:
                writer.write(f)
            output_files.append(output_path)

            progress = int((i + 1) / len(groups) * 100)
            self.progress_updated.emit(progress, f"已拆分: {output_name}.pdf")

        return output_files

    def _get_pdf_bookmark_ranges(self, reader, total_pages):
        """从PDF书签中提取页码范围"""
        outlines = reader.outline
        if not outlines:
            return []

        bookmark_pages = []

        def walk_outlines(items):
            for item in items:
                if isinstance(item, list):
                    walk_outlines(item)
                else:
                    try:
                        page_num = reader.get_destination_page_number(item) + 1
                        bookmark_pages.append(
                            (page_num, item.title if hasattr(item, 'title') else ""))
                    except Exception:
                        pass

        walk_outlines(outlines)
        if not bookmark_pages:
            return []

        bookmark_pages.sort(key=lambda x: x[0])

        groups = []
        for i, (start_page, title) in enumerate(bookmark_pages):
            if i + 1 < len(bookmark_pages):
                end_page = bookmark_pages[i + 1][0] - 1
            else:
                end_page = total_pages
            groups.append((list(range(start_page, end_page + 1)), title))

        return groups

    # ===== Word 拆分 =====
    def split_word(self, file_path):
        if not HAS_PYTHON_DOCX:
            self.split_error.emit(
                "缺少 python-docx 库，请先安装: pip install python-docx")
            return []

        # 按标题样式拆分直接用python-docx（不依赖COM分页）
        if self.rule == "by_heading":
            return self._split_word_by_heading(file_path)

        # 按页数拆分：优先使用 Word COM 自动化获取精确分页
        if HAS_WIN32COM and self.rule in ("by_page_count", "by_custom_pages"):
            return self._split_word_by_pages_com(file_path)

        # 回退：python-docx 按段落近似拆分
        return self._split_word_by_paragraphs_fallback(file_path)

    def _split_word_by_pages_com(self, file_path):
        """使用 Word COM 自动化按精确页码拆分，保留所有格式"""
        abs_path = os.path.abspath(file_path)
        word_app = None
        output_files = []

        try:
            word_app = win32.Dispatch("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = 0  # wdAlertsNone

            doc = word_app.Documents.Open(abs_path)
            total_pages = doc.ComputeStatistics(2)  # wdStatisticPages = 2

            # 计算页码范围
            page_ranges = []  # [(start_page, end_page), ...]
            if self.rule == "by_page_count":
                pages_per_split = self.params.get('pages_per_split', 5)
                for start in range(1, total_pages + 1, pages_per_split):
                    end = min(start + pages_per_split - 1, total_pages)
                    page_ranges.append((start, end))
            elif self.rule == "by_custom_pages":
                range_groups = self.parse_custom_ranges(
                    self.params.get('page_ranges', ''))
                for grp in range_groups:
                    valid = [p for p in grp if 1 <= p <= total_pages]
                    if valid:
                        page_ranges.append((valid[0], valid[-1]))

            if not page_ranges:
                doc.Close()
                return []

            for i, (start_page, end_page) in enumerate(page_ranges):
                if not self._is_running:
                    break

                # 复制页码范围到新文档
                # 使用 GoTo 跳转到起始页
                start_range = doc.GoTo(1, 1, start_page)  # wdGoToPage=1, wdGoToAbsolute=1
                start_pos = start_range.Start

                # 跳转到结束页的末尾
                if end_page < total_pages:
                    # 跳到下一页开头，然后回退
                    end_range = doc.GoTo(1, 1, end_page + 1)
                    end_pos = end_range.Start - 1
                else:
                    end_pos = doc.Range().End

                # 选中页码范围并复制
                page_range = doc.Range(start_pos, end_pos)

                # 修复：确保包含最后一段的段落标记（¶），否则缩进等格式会丢失
                if page_range.Paragraphs.Count > 0:
                    last_para = page_range.Paragraphs.Last
                    para_end = last_para.Range.End
                    # 如果段落末尾仅差1个字符（段落标记本身），则扩展包含它
                    if para_end - end_pos <= 1 and para_end <= doc.Range().End:
                        page_range.End = para_end

                page_range.Copy()

                # 创建新文档并粘贴
                new_doc = word_app.Documents.Add()
                new_range = new_doc.Range()
                new_range.Paste()

                output_name = self.format_name(
                    self.naming_template, file_path, i + 1,
                    range(start_page, end_page + 1), "")
                output_path = os.path.join(self.output_dir, output_name + '.docx')
                new_doc.SaveAs(output_path, 16)  # wdFormatDocumentDefault=16
                new_doc.Close()
                output_files.append(output_path)

                progress = int((i + 1) / len(page_ranges) * 100)
                self.progress_updated.emit(progress, f"已拆分: {output_name}.docx")

            doc.Close()

        except Exception as e:
            self.split_error.emit(f"Word COM 拆分失败: {str(e)}")
        finally:
            if word_app is not None:
                try:
                    word_app.Quit()
                except Exception:
                    pass

        return output_files

    def _split_word_by_heading(self, file_path):
        """按标题样式拆分（基于python-docx）"""
        doc = DocxDocument(file_path)
        heading_groups = self._get_word_heading_ranges(doc)

        if not heading_groups:
            # 无标题时回退到段落均分
            total_paras = len(doc.paragraphs)
            paras_per_split = 75
            heading_groups = []
            for start in range(0, total_paras, paras_per_split):
                end = min(start + paras_per_split, total_paras)
                heading_groups.append((list(range(start, end)), ""))

        output_files = []
        for i, (para_indices, title) in enumerate(heading_groups):
            new_doc = DocxDocument()

            # 复制页面设置
            if doc.sections:
                source_section = doc.sections[0]
                new_section = new_doc.sections[0]
                try:
                    new_section.page_width = source_section.page_width
                    new_section.page_height = source_section.page_height
                    new_section.left_margin = source_section.left_margin
                    new_section.right_margin = source_section.right_margin
                    new_section.top_margin = source_section.top_margin
                    new_section.bottom_margin = source_section.bottom_margin
                except Exception:
                    pass

            # 复制段落（保留格式）
            for idx in para_indices:
                if idx < len(doc.paragraphs):
                    source_para = doc.paragraphs[idx]
                    new_para = new_doc.add_paragraph()
                    try:
                        if source_para.style.name in [s.name for s in new_doc.styles]:
                            new_para.style = new_doc.styles[source_para.style.name]
                    except Exception:
                        pass
                    for run in source_para.runs:
                        new_run = new_para.add_run(run.text)
                        new_run.bold = run.bold
                        new_run.italic = run.italic
                        new_run.underline = run.underline
                        try:
                            if run.font.size:
                                new_run.font.size = run.font.size
                            if run.font.color and run.font.color.rgb:
                                new_run.font.color.rgb = run.font.color.rgb
                            if run.font.name:
                                new_run.font.name = run.font.name
                        except Exception:
                            pass

            page_group = None
            if para_indices:
                page_group = range(para_indices[0] // 15 + 1, para_indices[-1] // 15 + 2)

            output_name = self.format_name(
                self.naming_template, file_path, i + 1, page_group, title)
            output_path = os.path.join(self.output_dir, output_name + '.docx')
            new_doc.save(output_path)
            output_files.append(output_path)

            progress = int((i + 1) / len(heading_groups) * 100)
            self.progress_updated.emit(progress, f"已拆分: {output_name}.docx")

        return output_files

    def _split_word_by_paragraphs_fallback(self, file_path):
        """回退方案：python-docx 按段落近似拆分（不精确，但跨平台可用）"""
        doc = DocxDocument(file_path)
        groups = []

        if self.rule == "by_page_count":
            pages_per_split = self.params.get('pages_per_split', 5)
            total_paras = len(doc.paragraphs)
            paras_per_split = pages_per_split * 15
            for start in range(0, total_paras, paras_per_split):
                end = min(start + paras_per_split, total_paras)
                groups.append((list(range(start, end)), ""))

        elif self.rule == "by_custom_pages":
            range_groups = self.parse_custom_ranges(
                self.params.get('page_ranges', ''))
            total_paras = len(doc.paragraphs)
            est_total_pages = max(1, total_paras // 15)
            for grp in range_groups:
                valid = [p for p in grp if 1 <= p <= est_total_pages]
                if valid:
                    start_para = (valid[0] - 1) * 15
                    end_para = min(valid[-1] * 15, total_paras)
                    groups.append((list(range(start_para, end_para)), ""))

        if not groups:
            return []

        output_files = []
        for i, (para_indices, title) in enumerate(groups):
            new_doc = DocxDocument()

            if doc.sections:
                source_section = doc.sections[0]
                new_section = new_doc.sections[0]
                try:
                    new_section.page_width = source_section.page_width
                    new_section.page_height = source_section.page_height
                    new_section.left_margin = source_section.left_margin
                    new_section.right_margin = source_section.right_margin
                    new_section.top_margin = source_section.top_margin
                    new_section.bottom_margin = source_section.bottom_margin
                except Exception:
                    pass

            for idx in para_indices:
                if idx < len(doc.paragraphs):
                    source_para = doc.paragraphs[idx]
                    new_para = new_doc.add_paragraph()
                    try:
                        if source_para.style.name in [s.name for s in new_doc.styles]:
                            new_para.style = new_doc.styles[source_para.style.name]
                    except Exception:
                        pass
                    for run in source_para.runs:
                        new_run = new_para.add_run(run.text)
                        new_run.bold = run.bold
                        new_run.italic = run.italic
                        new_run.underline = run.underline
                        try:
                            if run.font.size:
                                new_run.font.size = run.font.size
                            if run.font.color and run.font.color.rgb:
                                new_run.font.color.rgb = run.font.color.rgb
                            if run.font.name:
                                new_run.font.name = run.font.name
                        except Exception:
                            pass

            page_group = None
            if para_indices:
                page_group = range(para_indices[0] // 15 + 1, para_indices[-1] // 15 + 2)

            output_name = self.format_name(
                self.naming_template, file_path, i + 1, page_group, title)
            output_path = os.path.join(self.output_dir, output_name + '.docx')
            new_doc.save(output_path)
            output_files.append(output_path)

            progress = int((i + 1) / len(groups) * 100)
            self.progress_updated.emit(progress, f"已拆分: {output_name}.docx")

        return output_files

    def _get_word_heading_ranges(self, doc):
        """按Word标题样式拆分"""
        groups = []
        current_indices = []
        current_title = ""

        for idx, para in enumerate(doc.paragraphs):
            if para.style.name.startswith('Heading'):
                if current_indices:
                    groups.append((current_indices, current_title))
                current_title = para.text.strip() or f"章节{len(groups) + 1}"
                current_indices = [idx]
            else:
                current_indices.append(idx)

        if current_indices:
            groups.append((current_indices, current_title))
        return groups

    # ===== Excel 拆分 =====
    def split_excel(self, file_path):
        wb = openpyxl.load_workbook(file_path)
        output_files = []

        if self.rule == "by_row_count":
            rows_per_split = self.params.get('rows_per_split', 100)
            sheets_per_split = self.params.get('sheets_per_split', 1)

            sheet_names = wb.sheetnames
            for sheet_group_start in range(0, len(sheet_names), sheets_per_split):
                sheet_group = sheet_names[sheet_group_start:
                                          sheet_group_start + sheets_per_split]

                for sheet_name in sheet_group:
                    ws = wb[sheet_name]
                    all_rows = list(ws.iter_rows(values_only=True))
                    if not all_rows:
                        continue

                    header = all_rows[0]
                    data_rows = all_rows[1:]

                    for chunk_start in range(0, len(data_rows), rows_per_split):
                        chunk = data_rows[chunk_start:chunk_start +
                                          rows_per_split]
                        new_wb = openpyxl.Workbook()
                        new_ws = new_wb.active
                        new_ws.title = sheet_name[:31]  # Excel sheet名最长31字符
                        new_ws.append(header)
                        for row in chunk:
                            new_ws.append(row)
                        # 复制列宽
                        for col_letter in ws.column_dimensions:
                            if col_letter in new_ws.column_dimensions:
                                new_ws.column_dimensions[col_letter].width = ws.column_dimensions[col_letter].width

                        seq = len(output_files) + 1
                        output_name = self.format_name(
                            self.naming_template, file_path, seq)
                        output_path = os.path.join(
                            self.output_dir, output_name + '.xlsx')
                        new_wb.save(output_path)
                        output_files.append(output_path)

                        progress = int(len(
                            output_files) / max(1, (len(data_rows) // rows_per_split + 1) * len(sheet_group)) * 100)
                        self.progress_updated.emit(
                            progress, f"已拆分: {output_name}.xlsx")

        elif self.rule == "by_sheet":
            sheets_per_split = self.params.get('sheets_per_split', 1)
            sheet_names = wb.sheetnames

            for group_start in range(0, len(sheet_names), sheets_per_split):
                group_sheets = sheet_names[group_start:group_start +
                                           sheets_per_split]

                new_wb = openpyxl.Workbook()
                first_sheet = True

                for sheet_name in group_sheets:
                    ws = wb[sheet_name]
                    if first_sheet:
                        new_ws = new_wb.active
                        new_ws.title = sheet_name[:31]
                        first_sheet = False
                    else:
                        new_ws = new_wb.create_sheet(title=sheet_name[:31])

                    for row in ws.iter_rows(values_only=True):
                        new_ws.append(row)
                    # 复制列宽
                    for col_letter in ws.column_dimensions:
                        new_ws.column_dimensions[col_letter].width = ws.column_dimensions[col_letter].width

                seq = len(output_files) + 1
                output_name = self.format_name(
                    self.naming_template, file_path, seq)
                output_path = os.path.join(
                    self.output_dir, output_name + '.xlsx')
                new_wb.save(output_path)
                output_files.append(output_path)

                progress = int(
                    len(output_files) / max(1, (len(sheet_names) // sheets_per_split + 1)) * 100)
                self.progress_updated.emit(
                    progress, f"已拆分: {output_name}.xlsx")

        return output_files


# ========== 文本重复识别 ==========
class TextDuplicatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔁 文本重复识别")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        group_font = QFont()
        group_font.setPointSize(15)

        # ===== 输入区域 =====
        input_group = QGroupBox("输入文本")
        input_group.setFont(group_font)
        input_layout = QVBoxLayout(input_group)

        self.input_text = QTextEdit()
        input_font = QFont()
        input_font.setPointSize(12)
        self.input_text.setFont(input_font)
        self.input_text.setPlaceholderText("请粘贴或输入需要识别重复项的文本...\n\n示例：\n【北京市海淀区人民法院】被告人张三欠李四10000元【北京市海淀区人民法院】被告人李四欠王五30000【北京市海淀区人民法院】被告人张三欠李四10000元")
        self.input_text.setMinimumHeight(150)
        input_layout.addWidget(self.input_text)

        layout.addWidget(input_group)

        # ===== 选项区域 =====
        option_group = QGroupBox("识别选项")
        option_group.setFont(group_font)
        option_layout = QVBoxLayout(option_group)

        # 最小重复长度
        len_layout = QHBoxLayout()
        len_label = QLabel("最小重复长度：")
        len_label_font = QFont()
        len_label_font.setPointSize(12)
        len_label.setFont(len_label_font)
        self.min_len_spin = QSpinBox()
        self.min_len_spin.setRange(2, 500)
        self.min_len_spin.setValue(6)
        self.min_len_spin.setSuffix(" 个字符")
        self.min_len_spin.setToolTip("短于此长度的重复片段将被忽略")
        len_layout.addWidget(len_label)
        len_layout.addWidget(self.min_len_spin)
        len_layout.addStretch()
        option_layout.addLayout(len_layout)

        layout.addWidget(option_group)

        # ===== 按钮区域 =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.btn_analyze = QPushButton("🔍 识别重复项")
        self.btn_analyze.setMinimumWidth(130)
        self.btn_analyze.clicked.connect(self.analyze_duplicates)
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        self.btn_extract_unique = QPushButton("📋 提取非重复部分")
        self.btn_extract_unique.setMinimumWidth(140)
        self.btn_extract_unique.clicked.connect(self.extract_unique)
        self.btn_extract_unique.setEnabled(False)
        self.btn_extract_unique.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """)

        self.btn_extract_dup = QPushButton("📋 提取重复部分")
        self.btn_extract_dup.setMinimumWidth(130)
        self.btn_extract_dup.clicked.connect(self.extract_duplicate)
        self.btn_extract_dup.setEnabled(False)
        self.btn_extract_dup.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """)

        self.btn_extract_dedup = QPushButton("📋 提取去重后文本")
        self.btn_extract_dedup.setMinimumWidth(140)
        self.btn_extract_dedup.clicked.connect(self.extract_deduplicated)
        self.btn_extract_dedup.setEnabled(False)
        self.btn_extract_dedup.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """)

        self.btn_clear = QPushButton("🗑️ 清空")
        self.btn_clear.setMinimumWidth(90)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        button_layout.addWidget(self.btn_analyze)
        button_layout.addWidget(self.btn_extract_unique)
        button_layout.addWidget(self.btn_extract_dup)
        button_layout.addWidget(self.btn_extract_dedup)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # ===== 识别结果区域 =====
        result_group = QGroupBox("识别结果")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setFont(input_font)
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

        # ===== 输出区域 =====
        output_group = QGroupBox("输出结果")
        output_group.setFont(group_font)
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setFont(input_font)
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        output_layout.addWidget(self.output_text)

        # 复制按钮
        copy_layout = QHBoxLayout()
        self.btn_copy = QPushButton("📋 复制输出结果")
        self.btn_copy.clicked.connect(self.copy_output)
        self.btn_copy.setEnabled(False)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """)
        copy_layout.addStretch()
        copy_layout.addWidget(self.btn_copy)
        output_layout.addLayout(copy_layout)

        layout.addWidget(output_group)
        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # 存储分析结果
        self.duplicate_segments = []  # [(segment, count, positions)]
        self.unique_text = ""
        self.dup_only_text = ""
        self.dedup_text = ""

    def find_duplicate_segments(self, text, min_len):
        """使用后缀数组思想找出文本中所有重复出现的子串"""
        n = len(text)
        if n < min_len:
            return []

        # 构建后缀数组（对起始位置排序）
        suffixes = list(range(n))
        suffixes.sort(key=lambda i: text[i:])

        duplicates = {}  # segment -> [start_positions]

        # 比较相邻后缀，找最长公共前缀
        for i in range(len(suffixes) - 1):
            s1 = suffixes[i]
            s2 = suffixes[i + 1]
            # 计算最长公共前缀
            lcp_len = 0
            max_lcp = min(n - s1, n - s2)
            while lcp_len < max_lcp and text[s1 + lcp_len] == text[s2 + lcp_len]:
                lcp_len += 1

            if lcp_len >= min_len:
                # 找到所有长度 >= min_len 的公共子串
                for length in range(min_len, lcp_len + 1):
                    segment = text[s1:s1 + length]
                    # 过滤纯空白或纯标点的片段
                    stripped = segment.strip()
                    if not stripped or len(stripped) < min_len // 2:
                        continue
                    if segment not in duplicates:
                        duplicates[segment] = set()
                    duplicates[segment].add(s1)
                    duplicates[segment].add(s2)

        # 进一步收集：对于每个已发现的重复片段，在全文中搜索所有出现位置
        final_duplicates = {}
        for segment, positions in duplicates.items():
            # 在全文中搜索所有出现
            all_positions = set()
            start = 0
            while True:
                idx = text.find(segment, start)
                if idx == -1:
                    break
                all_positions.add(idx)
                start = idx + 1
            if len(all_positions) >= 2:
                if segment not in final_duplicates or len(segment) > len(final_duplicates.get(segment, '')):
                    final_duplicates[segment] = all_positions

        # 去除被更长片段完全包含的短片段
        segments = sorted(final_duplicates.keys(), key=len, reverse=True)
        result = []
        covered_positions = {}  # segment -> set of position ranges

        for seg in segments:
            positions = final_duplicates[seg]
            # 检查该片段是否已被更长的片段覆盖
            is_covered = False
            for longer_seg, _, longer_positions in result:
                for lp in longer_positions:
                    for sp in positions:
                        if lp <= sp and sp + len(seg) <= lp + len(longer_seg):
                            is_covered = True
                            break
                    if is_covered:
                        break
                if is_covered:
                    break
            if not is_covered:
                result.append((seg, len(positions), sorted(positions)))

        # 按首次出现位置排序
        result.sort(key=lambda x: x[2][0])
        return result

    def analyze_duplicates(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入文本！")
            return

        min_len = self.min_len_spin.value()

        self.result_text.clear()
        self.output_text.clear()
        self.result_text.append("🔍 正在分析文本中的重复片段...\n")
        QApplication.processEvents()

        self.duplicate_segments = self.find_duplicate_segments(text, min_len)

        if not self.duplicate_segments:
            self.result_text.append("✅ 未发现重复片段\n")
            self.btn_extract_unique.setEnabled(False)
            self.btn_extract_dup.setEnabled(False)
            self.btn_extract_dedup.setEnabled(False)
            self.btn_copy.setEnabled(False)
            return

        self.result_text.append(f"发现 {len(self.duplicate_segments)} 个重复片段：\n")
        self.result_text.append("=" * 50 + "\n\n")

        # 标记重复位置用于高亮
        dup_positions = set()  # (start, end) 所有重复片段的位置

        for i, (segment, count, positions) in enumerate(self.duplicate_segments, 1):
            display_seg = segment if len(segment) <= 80 else segment[:77] + "..."
            self.result_text.append(f"📌 重复片段 {i}：\n")
            self.result_text.append(f"   内容：{display_seg}\n")
            self.result_text.append(f"   出现次数：{count} 次\n")
            self.result_text.append(f"   位置：{', '.join(f'第{p+1}字符' for p in positions)}\n\n")

            for p in positions:
                dup_positions.add((p, p + len(segment)))

        # 计算非重复部分和重复部分
        # 标记所有被重复片段覆盖的字符位置
        covered = set()
        for start, end in dup_positions:
            for pos in range(start, end):
                covered.add(pos)

        # 非重复部分：未被任何重复片段覆盖的字符
        unique_chars = []
        for i, ch in enumerate(text):
            if i not in covered:
                unique_chars.append(ch)
        self.unique_text = ''.join(unique_chars)

        # 重复部分：所有重复片段（去重后）
        dup_segments_set = []
        seen = set()
        for segment, count, positions in self.duplicate_segments:
            if segment not in seen:
                seen.add(segment)
                dup_segments_set.append(segment)
        self.dup_only_text = '\n---\n'.join(dup_segments_set)

        # 去重后文本：保留每个重复片段的首次出现，移除后续重复
        # 收集所有需要移除的区间（第2次及之后的重复出现）
        remove_ranges = []
        for segment, count, positions in self.duplicate_segments:
            for p in positions[1:]:  # 跳过首次出现，移除后续出现
                remove_ranges.append((p, p + len(segment)))
        # 按起始位置排序
        remove_ranges.sort()
        # 合并重叠区间
        merged = []
        for start, end in remove_ranges:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        remove_set = set()
        for start, end in merged:
            for pos in range(start, end):
                remove_set.add(pos)
        dedup_chars = []
        for i, ch in enumerate(text):
            if i not in remove_set:
                dedup_chars.append(ch)
        self.dedup_text = ''.join(dedup_chars)

        self.btn_extract_unique.setEnabled(True)
        self.btn_extract_dup.setEnabled(True)
        self.btn_extract_dedup.setEnabled(True)

    def extract_unique(self):
        if not self.unique_text and not self.duplicate_segments:
            QMessageBox.warning(self, "提示", "请先进行识别！")
            return
        self.output_text.clear()
        self.output_text.setPlainText(self.unique_text)
        self.btn_copy.setEnabled(True)

    def extract_duplicate(self):
        if not self.dup_only_text and not self.duplicate_segments:
            QMessageBox.warning(self, "提示", "请先进行识别！")
            return
        self.output_text.clear()
        self.output_text.setPlainText(self.dup_only_text)
        self.btn_copy.setEnabled(True)

    def extract_deduplicated(self):
        if not self.dedup_text and not self.duplicate_segments:
            QMessageBox.warning(self, "提示", "请先进行识别！")
            return
        self.output_text.clear()
        self.output_text.setPlainText(self.dedup_text)
        self.btn_copy.setEnabled(True)

    def copy_output(self):
        text = self.output_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.btn_copy.setText("✅ 已复制")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.btn_copy.setText("📋 复制输出结果"))

    def clear_all(self):
        self.input_text.clear()
        self.result_text.clear()
        self.output_text.clear()
        self.duplicate_segments = []
        self.unique_text = ""
        self.dup_only_text = ""
        self.dedup_text = ""
        self.btn_extract_unique.setEnabled(False)
        self.btn_extract_dup.setEnabled(False)
        self.btn_extract_dedup.setEnabled(False)
        self.btn_copy.setEnabled(False)


class DocSplitPage(QWidget):
    def __init__(self):
        super().__init__()
        self.file_list_data = []
        self.split_worker = None
        self.input_names = []
        self.setup_ui()

    def setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("📑 文档拆分工具")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        group_font = QFont()
        group_font.setPointSize(15)

        # ===== 文件选择区域 =====
        file_group = QGroupBox("选择文件")
        file_group.setFont(group_font)
        file_layout = QVBoxLayout(file_group)

        # 文件路径选择行
        path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText(
            "支持 PDF、Word(.docx)、Excel(.xlsx) 文件")
        self.file_path_edit.setReadOnly(True)

        btn_add = QPushButton("📂 选择文件")
        btn_add.setMinimumWidth(110)
        btn_add.clicked.connect(self.add_files)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        btn_add_batch = QPushButton("➕ 批量添加")
        btn_add_batch.setMinimumWidth(110)
        btn_add_batch.clicked.connect(self.add_files_batch)
        btn_add_batch.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)

        path_layout.addWidget(self.file_path_edit)
        path_layout.addWidget(btn_add)
        path_layout.addWidget(btn_add_batch)
        file_layout.addLayout(path_layout)

        # 文件列表
        self.file_list_widget = QListWidget()
        self.file_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.file_list_widget.setMinimumHeight(80)
        file_layout.addWidget(self.file_list_widget)

        # 文件操作按钮
        file_btn_layout = QHBoxLayout()
        btn_remove = QPushButton("➖ 移除选中")
        btn_remove.clicked.connect(self.remove_files)
        btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
        """)
        btn_clear = QPushButton("🗑️ 清空列表")
        btn_clear.clicked.connect(self.clear_files)
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #999;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        file_btn_layout.addWidget(btn_remove)
        file_btn_layout.addWidget(btn_clear)
        file_btn_layout.addStretch()
        file_layout.addLayout(file_btn_layout)

        layout.addWidget(file_group)

        # ===== 拆分规则 =====
        rule_group = QGroupBox("拆分规则")
        rule_group.setFont(group_font)
        rule_layout = QVBoxLayout(rule_group)

        # 拆分方式选择
        rule_select_layout = QHBoxLayout()
        rule_select_layout.addWidget(QLabel("拆分方式:"))
        self.rule_combo = QComboBox()
        self.rule_combo.addItems([
            "按页数拆分",
            "按自定义页码拆分",
            "按书签/标题拆分",
            "按行数拆分（Excel）",
            "按工作表拆分（Excel）",
            "按文件大小拆分（PDF）"
        ])
        self.rule_combo.currentIndexChanged.connect(self.on_rule_changed)
        rule_select_layout.addWidget(self.rule_combo)
        rule_select_layout.addStretch()
        rule_layout.addLayout(rule_select_layout)

        # 动态参数区域
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        self.params_layout.setContentsMargins(0, 0, 0, 0)

        # 按页数拆分参数
        self.param_page_count = QWidget()
        pcl = QHBoxLayout(self.param_page_count)
        pcl.setContentsMargins(0, 0, 0, 0)
        pcl.addWidget(QLabel("每N页拆分:"))
        self.spin_pages = QSpinBox()
        self.spin_pages.setRange(1, 9999)
        self.spin_pages.setValue(5)
        pcl.addWidget(self.spin_pages)
        pcl.addWidget(QLabel("页"))
        pcl.addStretch()

        # 按自定义页码参数
        self.param_custom_pages = QWidget()
        cpl = QHBoxLayout(self.param_custom_pages)
        cpl.setContentsMargins(0, 0, 0, 0)
        cpl.addWidget(QLabel("页码范围:"))
        self.edit_custom_pages = QLineEdit()
        self.edit_custom_pages.setPlaceholderText("例如: 1-3,4-6,7-10")
        cpl.addWidget(self.edit_custom_pages)
        cpl.addWidget(QLabel("每段生成一个文件"))
        cpl.addStretch()

        # 按书签/标题参数（无额外参数）
        self.param_bookmark = QWidget()
        bml = QHBoxLayout(self.param_bookmark)
        bml.setContentsMargins(0, 0, 0, 0)
        bml.addWidget(QLabel("自动按PDF书签或Word标题样式拆分"))
        bml.addStretch()

        # 按行数拆分参数
        self.param_row_count = QWidget()
        rcl = QHBoxLayout(self.param_row_count)
        rcl.setContentsMargins(0, 0, 0, 0)
        rcl.addWidget(QLabel("每N行拆分:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 999999)
        self.spin_rows.setValue(100)
        rcl.addWidget(self.spin_rows)
        rcl.addWidget(QLabel("行（每个文件保留表头）"))
        rcl.addStretch()

        # 按工作表拆分参数
        self.param_sheet = QWidget()
        sl = QHBoxLayout(self.param_sheet)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(QLabel("每N个工作表拆为一个文件:"))
        self.spin_sheets = QSpinBox()
        self.spin_sheets.setRange(1, 999)
        self.spin_sheets.setValue(1)
        sl.addWidget(self.spin_sheets)
        sl.addWidget(QLabel("个工作表"))
        sl.addStretch()

        # 按文件大小参数
        self.param_size = QWidget()
        szl = QHBoxLayout(self.param_size)
        szl.setContentsMargins(0, 0, 0, 0)
        szl.addWidget(QLabel("目标大小:"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(1, 9999)
        self.spin_size.setValue(5)
        szl.addWidget(self.spin_size)
        szl.addWidget(QLabel("MB"))
        szl.addStretch()

        # 添加所有参数widget
        self.params_layout.addWidget(self.param_page_count)
        self.params_layout.addWidget(self.param_custom_pages)
        self.params_layout.addWidget(self.param_bookmark)
        self.params_layout.addWidget(self.param_row_count)
        self.params_layout.addWidget(self.param_sheet)
        self.params_layout.addWidget(self.param_size)

        rule_layout.addWidget(self.params_widget)
        layout.addWidget(rule_group)

        # 初始显示
        self.on_rule_changed(0)

        # ===== 命名设置 =====
        naming_group = QGroupBox("命名设置")
        naming_group.setFont(group_font)
        naming_layout = QVBoxLayout(naming_group)

        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("命名模板:"))
        self.edit_naming = QLineEdit()
        self.edit_naming.setText("{原名}_第{序号}部分")
        self.edit_naming.setPlaceholderText("{原名}_第{序号}部分")
        template_layout.addWidget(self.edit_naming)
        naming_layout.addLayout(template_layout)

        hint_label = QLabel("可用变量: {原名}  {序号}  {序号:02d}  {日期}  {页码范围}  {标题}  {输入}")
        hint_label.setStyleSheet("color: #999; font-size: 11px;")
        naming_layout.addWidget(hint_label)

        # 导入命名变量
        import_layout = QHBoxLayout()
        self.btn_import_names = QPushButton("📋 导入命名变量")
        self.btn_import_names.clicked.connect(self.import_names)
        self.btn_import_names.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        import_layout.addWidget(self.btn_import_names)

        self.label_import_info = QLabel("未导入")
        self.label_import_info.setStyleSheet("color: #999;")
        import_layout.addWidget(self.label_import_info)
        import_layout.addStretch()
        naming_layout.addLayout(import_layout)

        # 已导入的变量预览
        self.import_names_list = QListWidget()
        self.import_names_list.setMaximumHeight(80)
        self.import_names_list.setVisible(False)
        naming_layout.addWidget(self.import_names_list)

        layout.addWidget(naming_group)

        # ===== 输出设置 =====
        output_group = QGroupBox("输出设置")
        output_group.setFont(group_font)
        output_layout = QVBoxLayout(output_group)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("输出目录:"))
        self.edit_output_dir = QLineEdit()
        self.edit_output_dir.setPlaceholderText("请选择输出目录...")
        self.edit_output_dir.setReadOnly(True)
        dir_layout.addWidget(self.edit_output_dir)

        btn_output_dir = QPushButton("📂 选择目录")
        btn_output_dir.setMinimumWidth(110)
        btn_output_dir.clicked.connect(self.select_output_dir)
        btn_output_dir.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        dir_layout.addWidget(btn_output_dir)
        output_layout.addLayout(dir_layout)

        self.check_auto_open = QCheckBox("拆分后自动打开输出目录")
        check_font = QFont()
        check_font.setPointSize(12)
        self.check_auto_open.setFont(check_font)
        self.check_auto_open.setChecked(True)
        output_layout.addWidget(self.check_auto_open)

        layout.addWidget(output_group)

        # ===== 操作按钮 =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.btn_preview = QPushButton("👁️ 预览拆分")
        self.btn_preview.setMinimumWidth(120)
        self.btn_preview.clicked.connect(self.preview_split)
        self.btn_preview.setEnabled(False)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """)

        self.btn_split = QPushButton("✂️ 开始拆分")
        self.btn_split.setMinimumWidth(120)
        self.btn_split.clicked.connect(self.start_split)
        self.btn_split.setEnabled(False)
        self.btn_split.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #999;
            }
        """)

        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setMinimumWidth(100)
        self.btn_stop.clicked.connect(self.stop_split)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B; color: white; border: none;
                padding: 8px 15px; border-radius: 6px; min-height: 30px; font-weight: bold;
            }
            QPushButton:hover { background-color: #FF5252; }
        """)

        button_layout.addWidget(self.btn_preview)
        button_layout.addWidget(self.btn_split)
        button_layout.addWidget(self.btn_stop)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # ===== 结果显示 =====
        result_group = QGroupBox("拆分结果")
        result_group.setFont(group_font)
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        text_font = QFont()
        text_font.setPointSize(12)
        self.result_text.setFont(text_font)
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)
        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def import_names(self):
        """从Excel或TXT导入命名变量"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择命名变量文件", "",
            "Excel文件 (*.xlsx);;文本文件 (*.txt);;所有文件 (*)")

        if not file_path:
            return

        names = []
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xlsx':
                wb = openpyxl.load_workbook(file_path, read_only=True)
                ws = wb.active
                for row in ws.iter_rows(min_row=1, values_only=True):
                    if row and row[0] is not None:
                        names.append(str(row[0]).strip())
                wb.close()
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            names.append(line)
            else:
                QMessageBox.warning(self, "提示", "仅支持 .xlsx 和 .txt 文件！")
                return

            if not names:
                QMessageBox.warning(self, "提示", "文件中没有找到有效数据！")
                return

            self.input_names = names
            self.label_import_info.setText(f"已导入 {len(names)} 个变量")
            self.label_import_info.setStyleSheet("color: #4CAF50; font-weight: bold;")

            # 显示预览
            self.import_names_list.setVisible(True)
            self.import_names_list.clear()
            for name in names:
                self.import_names_list.addItem(name)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    # ===== 拆分方式切换 =====
    def on_rule_changed(self, index):
        self.param_page_count.setVisible(index == 0)
        self.param_custom_pages.setVisible(index == 1)
        self.param_bookmark.setVisible(index == 2)
        self.param_row_count.setVisible(index == 3)
        self.param_sheet.setVisible(index == 4)
        self.param_size.setVisible(index == 5)

    def _get_rule_key(self):
        mapping = {
            0: "by_page_count",
            1: "by_custom_pages",
            2: "by_bookmark",
            3: "by_row_count",
            4: "by_sheet",
            5: "by_size"
        }
        return mapping.get(self.rule_combo.currentIndex(), "by_page_count")

    def _get_params(self):
        rule = self._get_rule_key()
        params = {}
        if rule == "by_page_count":
            params['pages_per_split'] = self.spin_pages.value()
        elif rule == "by_custom_pages":
            params['page_ranges'] = self.edit_custom_pages.text()
        elif rule == "by_row_count":
            params['rows_per_split'] = self.spin_rows.value()
        elif rule == "by_sheet":
            params['sheets_per_split'] = self.spin_sheets.value()
        elif rule == "by_size":
            params['target_size_mb'] = self.spin_size.value()
        return params

    # ===== 文件操作 =====
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "文档文件 (*.pdf *.docx *.xlsx);;PDF文件 (*.pdf);;Word文件 (*.docx);;Excel文件 (*.xlsx)")
        self._add_files_to_list(files)

    def add_files_batch(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含文档的文件夹")
        if not folder:
            return
        files = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.pdf', '.docx', '.xlsx'):
                files.append(os.path.join(folder, f))
        self._add_files_to_list(files)

    def _add_files_to_list(self, files):
        if not files:
            return
        for f in files:
            if f not in self.file_list_data:
                self.file_list_data.append(f)
                self.file_list_widget.addItem(os.path.basename(f))
        self._update_buttons()

    def remove_files(self):
        selected = self.file_list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要移除的文件！")
            return
        for item in selected:
            row = self.file_list_widget.row(item)
            self.file_list_widget.takeItem(row)
            self.file_list_data.pop(row)
        self._update_buttons()

    def clear_files(self):
        if not self.file_list_data:
            return
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有文件吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.file_list_data.clear()
            self.file_list_widget.clear()
            self._update_buttons()

    def _update_buttons(self):
        has_files = len(self.file_list_data) > 0
        has_output = bool(self.edit_output_dir.text())
        self.btn_preview.setEnabled(has_files)
        self.btn_split.setEnabled(has_files and has_output)

    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self.edit_output_dir.setText(folder)
            self._update_buttons()

    # ===== 预览 =====
    def preview_split(self):
        if not self.file_list_data:
            QMessageBox.warning(self, "提示", "请先选择文件！")
            return

        self.result_text.clear()
        self.result_text.append("👁️ 拆分预览\n")
        self.result_text.append("=" * 60 + "\n\n")

        rule = self._get_rule_key()
        params = self._get_params()
        rule_name = self.rule_combo.currentText()

        for file_path in self.file_list_data:
            ext = os.path.splitext(file_path)[1].lower()
            basename = os.path.basename(file_path)
            self.result_text.append(f"📄 {basename}\n")

            try:
                if ext == '.pdf':
                    reader = PyPDF2.PdfReader(file_path)
                    total_pages = len(reader.pages)
                    self.result_text.append(f"   总页数: {total_pages}\n")

                    if rule == "by_page_count":
                        n = params.get('pages_per_split', 5)
                        count = (total_pages + n - 1) // n
                        self.result_text.append(
                            f"   拆分方式: 每{n}页 → {count}个文件\n")
                        for i in range(count):
                            start = i * n + 1
                            end = min((i + 1) * n, total_pages)
                            self.result_text.append(
                                f"   文件{i+1}: 第{start}-{end}页\n")

                    elif rule == "by_custom_pages":
                        range_str = params.get('page_ranges', '')
                        groups = self._parse_preview_ranges(range_str)
                        self.result_text.append(
                            f"   拆分方式: 自定义页码 → {len(groups)}个文件\n")
                        for i, grp in enumerate(groups):
                            valid = [p for p in grp if 1 <= p <= total_pages]
                            if valid:
                                self.result_text.append(
                                    f"   文件{i+1}: 第{valid[0]}-{valid[-1]}页\n")

                    elif rule == "by_bookmark":
                        outlines = reader.outline
                        if outlines:
                            self.result_text.append(f"   拆分方式: 按书签拆分\n")
                            self._preview_pdf_bookmarks(
                                reader, outlines, total_pages)
                        else:
                            self.result_text.append(f"   ⚠️ 无书签，将回退为按页数拆分\n")

                    elif rule == "by_size":
                        target_mb = params.get('target_size_mb', 5)
                        file_size = os.path.getsize(file_path)
                        avg_size = file_size / max(total_pages, 1)
                        pages_per = max(
                            1, int(target_mb * 1024 * 1024 / max(avg_size, 1)))
                        count = (total_pages + pages_per - 1) // pages_per
                        self.result_text.append(
                            f"   拆分方式: 每~{target_mb}MB → 约{count}个文件\n")

                elif ext == '.docx':
                    if not HAS_PYTHON_DOCX:
                        self.result_text.append(f"   ❌ 缺少 python-docx 库\n")
                        continue

                    # 优先使用 Word COM 获取精确页数
                    real_pages = None
                    heading_count = 0
                    total_paras = 0
                    if HAS_WIN32COM and rule in ("by_page_count", "by_custom_pages"):
                        try:
                            word_app = win32.Dispatch("Word.Application")
                            word_app.Visible = False
                            word_app.DisplayAlerts = 0
                            wdoc = word_app.Documents.Open(os.path.abspath(file_path))
                            real_pages = wdoc.ComputeStatistics(2)  # wdStatisticPages
                            wdoc.Close()
                            word_app.Quit()
                        except Exception:
                            pass

                    doc = DocxDocument(file_path)
                    total_paras = len(doc.paragraphs)
                    est_pages = real_pages if real_pages else max(1, total_paras // 15)
                    self.result_text.append(
                        f"   段落数: {total_paras} (共{est_pages}页)\n")

                    if rule == "by_page_count":
                        n = params.get('pages_per_split', 5)
                        count = (est_pages + n - 1) // n
                        self.result_text.append(
                            f"   拆分方式: 每{n}页 → {count}个文件\n")
                        for i in range(count):
                            start = i * n + 1
                            end = min((i + 1) * n, est_pages)
                            self.result_text.append(
                                f"   文件{i+1}: 第{start}-{end}页\n")

                    elif rule == "by_custom_pages":
                        range_str = params.get('page_ranges', '')
                        groups = self._parse_preview_ranges(range_str)
                        self.result_text.append(
                            f"   拆分方式: 自定义页码 → {len(groups)}个文件\n")
                        for i, grp in enumerate(groups):
                            valid = [p for p in grp if 1 <= p <= est_pages]
                            if valid:
                                self.result_text.append(
                                    f"   文件{i+1}: 第{valid[0]}-{valid[-1]}页\n")

                    elif rule == "by_heading":
                        for para in doc.paragraphs:
                            if para.style.name.startswith('Heading'):
                                heading_count += 1
                        self.result_text.append(
                            f"   拆分方式: 按标题样式 → 约{heading_count}个文件\n")

                elif ext == '.xlsx':
                    wb = openpyxl.load_workbook(file_path, read_only=True)
                    sheet_names = wb.sheetnames
                    self.result_text.append(f"   工作表数: {len(sheet_names)}\n")

                    if rule == "by_row_count":
                        n = params.get('rows_per_split', 100)
                        for sn in sheet_names:
                            ws = wb[sn]
                            row_count = ws.max_row - 1  # 减去表头
                            if row_count > 0:
                                count = (row_count + n - 1) // n
                                self.result_text.append(
                                    f"   {sn}: {row_count}行数据 → {count}个文件\n")

                    elif rule == "by_sheet":
                        n = params.get('sheets_per_split', 1)
                        count = (len(sheet_names) + n - 1) // n
                        self.result_text.append(
                            f"   拆分方式: 每{n}个工作表 → {count}个文件\n")
                        for i in range(count):
                            start = i * n
                            end = min((i + 1) * n, len(sheet_names))
                            sheets = sheet_names[start:end]
                            self.result_text.append(
                                f"   文件{i+1}: {', '.join(sheets)}\n")

                    wb.close()

                else:
                    self.result_text.append(f"   ⚠️ 不支持的格式\n")

            except Exception as e:
                self.result_text.append(f"   ❌ 预览失败: {str(e)}\n")

            self.result_text.append("\n")

    def _preview_pdf_bookmarks(self, reader, outlines, total_pages, depth=0):
        for item in outlines:
            if isinstance(item, list):
                self._preview_pdf_bookmarks(
                    reader, item, total_pages, depth + 1)
            else:
                try:
                    page_num = reader.get_destination_page_number(item) + 1
                    title = item.title if hasattr(
                        item, 'title') else f"第{page_num}页"
                    self.result_text.append(
                        f"   {'  ' * depth}📑 {title} (第{page_num}页起)\n")
                except Exception:
                    pass

    def _parse_preview_ranges(self, range_str):
        groups = []
        for part in range_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                try:
                    groups.append(list(range(int(start), int(end) + 1)))
                except ValueError:
                    continue
            else:
                try:
                    groups.append([int(part)])
                except ValueError:
                    continue
        return groups

    # ===== 执行拆分 =====
    def start_split(self):
        if not self.file_list_data:
            QMessageBox.warning(self, "提示", "请先选择文件！")
            return

        output_dir = self.edit_output_dir.text()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请选择输出目录！")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        rule = self._get_rule_key()
        params = self._get_params()
        naming_template = self.edit_naming.text() or "{原名}_第{序号}部分"

        # 校验：按自定义页码时必须输入范围
        if rule == "by_custom_pages" and not params.get('page_ranges'):
            QMessageBox.warning(self, "提示", "请输入页码范围！")
            return

        # 校验：如果命名模板中使用了{输入}，检查变量个数
        uses_input_var = "{输入}" in naming_template
        if uses_input_var and not self.input_names:
            QMessageBox.warning(self, "提示", "命名模板中使用了{输入}变量，请先导入命名变量！")
            return

        self.btn_split.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.result_text.clear()
        self.result_text.append("✂️ 开始拆分...\n")
        self.result_text.append("=" * 60 + "\n\n")

        self.split_worker = SplitWorker(
            self.file_list_data, rule, params,
            output_dir, naming_template, "original",
            input_names=self.input_names if uses_input_var else []
        )
        self.split_worker.progress_updated.connect(self.on_progress)
        self.split_worker.split_completed.connect(self.on_split_completed)
        self.split_worker.split_error.connect(self.on_split_error)
        self.split_worker.needs_input_count.connect(self.on_needs_input_count)
        self.split_worker.start()

    def stop_split(self):
        if self.split_worker and self.split_worker.isRunning():
            self.split_worker.stop()
            self.result_text.append("\n⏹ 拆分已停止\n")
        self.btn_split.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)

    def on_progress(self, value, message):
        self.progress.setValue(value)
        self.result_text.append(f"{message}\n")
        QApplication.processEvents()

    def on_split_completed(self, output_files):
        self.result_text.append("\n" + "=" * 60 + "\n")
        self.result_text.append(f"✅ 拆分完成！共生成 {len(output_files)} 个文件：\n\n")
        for f in output_files:
            self.result_text.append(f"   📄 {os.path.basename(f)}\n")

        self.progress.setVisible(False)
        self.btn_split.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if self.check_auto_open.isChecked() and output_files:
            output_dir = os.path.dirname(output_files[0])
            if os.name == 'nt':
                os.startfile(output_dir)

        QMessageBox.information(
            self, "完成", f"文档拆分完成！共生成 {len(output_files)} 个文件。")

    def on_split_error(self, error_msg):
        self.result_text.append(f"\n❌ {error_msg}\n")
        self.btn_split.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)

    def on_needs_input_count(self, total_count):
        """拆分文件个数与输入变量个数不匹配时的回调"""
        self.btn_split.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)
        QMessageBox.warning(
            self, "命名变量不匹配",
            f"命名部分输入的变量个数与拆分后文件个数不匹配，请检查输入变量个数\n\n"
            f"拆分后文件数: {total_count}\n"
            f"已导入变量数: {len(self.input_names)}")


try:
    from lunarcalendar import Converter, Solar, Lunar
    HAS_LUNARCALENDAR = True
except ImportError:
    HAS_LUNARCALENDAR = False


# ========== 彩蛋系统 ==========
_EASTER_EGG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'PupAide')
EASTER_EGG_FILE = os.path.join(_EASTER_EGG_DIR, 'pup_aide_easter_eggs.json')

HOLIDAYS = {
    (1, 1): ("🎊 元旦快乐", "新的一年，会更爱你"),
    (2, 14): ("💝 情人节快乐", "小狗常伴你左右！"),
    (5, 1): ("🌻 劳动节到啦", "小宝辛苦了，记得好好休息！"),
    (10, 1): ("🇨🇳 国庆快乐", "长假去哪玩！"),
    (11, 11): ("😄 双十一买买买", "全场消费张总买单"),
    (12, 25): ("🎄 圣诞啦", "圣诞老人给你送了只小狗来~"),
    (12, 31): ("🎆 跨年快乐", "今年的最后一天，来张纪念照吧！"),
}

LUNAR_HOLIDAYS = {
    (1, 1): ("🧧 新春快乐", "什么时候和小狗一起吃春节的饺子呀"),
    (1, 15): ("🏮 元宵节快乐", "小狗给你买豆沙馅的元宵来啦~"),
    (5, 5): ("🐉 端午安康", "豆沙和蜜枣，今年谁更胜一筹呢！"),
    (7, 7): ("🌌 七夕快乐", "牛郎和织女见面了，我们也要见面啦！"),
    (8, 15): ("🌕 中秋快乐", "小狗苦恼：月饼这个东西什么时候才能做的好吃一点"),
}

MILESTONES = {
    1: ("🐕 欢迎使用小狗助理", "终于见面啦，希望小狗助理能成为你的好帮手！"),
    52: ("🌟 52 次", "恭喜你触发521美餐一顿，快去凭截图找小狗兑换吧！"),
    99: ("💖 99 次", "恭喜你触发长长久久套餐，凭截图可以找小狗兑换任意一个你喜欢的礼物！"),
    1314: ("💕 1314 次", "恭喜你触发一生一世任务，小狗将带你出去旅游哦~"),
    2000: ("🎯 2000 次", "恭喜你触发里程碑任务，需要带小狗吃一顿美食哦~"),
    3000: ("🏆 3000 次", "恭喜你触发里程碑任务，需要带小狗出去玩哦~"),
    5000: ("👑 5000 次", "恭喜你触发惊喜奖励，小狗将带你出去度！蜜！月！"),
    10000: ("🌈 10000 次", "不可思议！你触发了传奇奖励！"),
}


def _load_easter_egg_data():
    default = {
        'open_count': 0,
        'last_open_date': '',
        'nickname': '',
        'first_use_date': '',
        'anniversary_start': '2021-08-26',
        'birthday': '1997-08-26',
        'lunar_birthday': [7, 24],
        'shown_milestones': [],
        'shown_holidays': [],
        'shown_anniversary': [],
        'consecutive_days': 0,
        'last_consecutive_date': '',
        'shown_consecutive': [],
        'settings_discovered': False,
    }
    try:
        if os.path.exists(EASTER_EGG_FILE):
            with open(EASTER_EGG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k, v in default.items():
                data.setdefault(k, v)
            return data
    except Exception:
        pass
    return default


def _save_easter_egg_data(data):
    try:
        os.makedirs(_EASTER_EGG_DIR, exist_ok=True)
        with open(EASTER_EGG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _lunar_to_solar(year, month, day):
    if not HAS_LUNARCALENDAR:
        return None
    try:
        lunar = Lunar(year, month, day, leap=False)
        solar = Converter.lunar2solar(lunar)
        return (solar.year, solar.month, solar.day)
    except Exception:
        return None


class EasterEggDialog(QDialog):
    def __init__(self, parent, title, message, emoji="🐕"):
        super().__init__(parent)
        self.setWindowTitle("小狗助理彩蛋")
        self.setFixedSize(420, 280)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)

        emoji_label = QLabel(emoji)
        emoji_font = QFont()
        emoji_font.setPointSize(40)
        emoji_label.setFont(emoji_font)
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emoji_label)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #FF9500;")
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_font = QFont()
        msg_font.setPointSize(12)
        msg_label.setFont(msg_font)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #555;")
        layout.addWidget(msg_label)

        btn = QPushButton("好哦")
        btn.clicked.connect(self.accept)
        btn.setFixedWidth(120)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB347;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF9500;
            }
        """)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 12px;
            }
        """)


class EasterEggManager:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.data = _load_easter_egg_data()

    def on_app_start(self):
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')

        # 首次使用，弹出登录对话框
        if not self.data.get('nickname', ''):
            dlg = FirstLoginDialog(self.parent)
            if dlg.exec() == FirstLoginDialog.DialogCode.Accepted:
                self.data['nickname'] = dlg.nickname
                self.data['first_use_date'] = today_str
            else:
                self.data['nickname'] = '神秘人'
                self.data['first_use_date'] = today_str

        # 连续使用天数
        if self.data['last_consecutive_date']:
            last = date.fromisoformat(self.data['last_consecutive_date'])
            diff = (today - last).days
            if diff == 1:
                self.data['consecutive_days'] += 1
            elif diff > 1:
                self.data['consecutive_days'] = 1
        else:
            self.data['consecutive_days'] = 1

        self.data['open_count'] += 1
        self.data['last_open_date'] = today_str
        self.data['last_consecutive_date'] = today_str
        _save_easter_egg_data(self.data)

        # 延迟弹出，等窗口完全显示
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(800, self._check_all)

    def _check_all(self):
        self._check_anniversary()
        self._check_holidays()
        self._check_milestones()
        self._check_birthday()
        self._check_consecutive()

    def _show_dialog(self, title, message, emoji="🐕"):
        dlg = EasterEggDialog(self.parent, title, message, emoji)
        dlg.exec()

    def _check_anniversary(self):
        today = date.today()
        anni_str = self.data.get('anniversary_start', '')
        if not anni_str:
            return
        try:
            anni_date = date.fromisoformat(anni_str)
        except Exception:
            return

        anni_month = anni_date.month
        anni_day = anni_date.day
        anni_year = anni_date.year
        years_together = today.year - anni_year

        if years_together <= 0:
            return

        anni_this_year = date(today.year, anni_month, anni_day)
        shown = self.data.get('shown_anniversary', [])

        if today == anni_this_year:
            if str(years_together) not in shown:
                self._show_dialog(
                    "🎉 纪念日快乐",
                    f"今天是我们在一起 {years_together} 年的纪念日！\n小狗会一直爱你哦 🥰",
                    "💕"
                )
                shown.append(str(years_together))
                self.data['shown_anniversary'] = shown
                _save_easter_egg_data(self.data)
        elif today > anni_this_year:
            if str(years_together) not in shown:
                days_passed = (today - anni_this_year).days
                self._show_dialog(
                    "💕 纪念日过啦",
                    f"{days_passed} 天前是我们在一起 {years_together} 年的纪念日，\n"
                    f"当天你没有打开使用哦，\n我们一定已经度过了一个开心的纪念日 🌹",
                    "🌹"
                )
                shown.append(str(years_together))
                self.data['shown_anniversary'] = shown
                _save_easter_egg_data(self.data)

    def _check_holidays(self):
        today = date.today()
        today_key = today.strftime('%Y-%m-%d')
        shown = self.data.get('shown_holidays', [])

        if today_key in shown:
            return

        triggered = False

        # 公历节日
        solar_key = (today.month, today.day)
        if solar_key in HOLIDAYS:
            title, msg = HOLIDAYS[solar_key]
            self._show_dialog(title, msg, "🎉")
            triggered = True

        # 农历节日
        if HAS_LUNARCALENDAR and not triggered:
            for (lm, ld), (title, msg) in LUNAR_HOLIDAYS.items():
                result = _lunar_to_solar(today.year, lm, ld)
                if result:
                    sy, sm, sd = result
                    if (sm, sd) == (today.month, today.day):
                        self._show_dialog(title, msg, "🎉")
                        triggered = True
                        break

        if triggered:
            shown.append(today_key)
            self.data['shown_holidays'] = shown
            _save_easter_egg_data(self.data)

    def _check_milestones(self):
        count = self.data['open_count']
        shown = self.data.get('shown_milestones', [])

        if count in MILESTONES and count not in shown:
            title, msg = MILESTONES[count]
            self._show_dialog(title, f"你已经打开小狗助理 {count} 次了！\n{msg}", "🏆")
            shown.append(count)
            self.data['shown_milestones'] = shown
            _save_easter_egg_data(self.data)

    def _check_birthday(self):
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        shown = self.data.get('shown_holidays', [])

        # 阳历生日
        bday_str = self.data.get('birthday', '')
        if bday_str:
            try:
                bday = date.fromisoformat(bday_str)
                if today.month == bday.month and today.day == bday.day:
                    if today_str + '_bday' not in shown:
                        age = today.year - bday.year
                        self._show_dialog(
                            "🎂 生日快乐",
                            f"今天是小宝的 {age} 岁生日！\n新的一岁，小狗会继续陪你过好每一天！",
                            "🎂"
                        )
                        shown.append(today_str + '_bday')
                        self.data['shown_holidays'] = shown
                        _save_easter_egg_data(self.data)
                        return
            except Exception:
                pass

        # 农历生日
        lunar_bday = self.data.get('lunar_birthday', [])
        if lunar_bday and len(lunar_bday) == 2 and HAS_LUNARCALENDAR:
            lm, ld = lunar_bday
            result = _lunar_to_solar(today.year, lm, ld)
            if result:
                _, sm, sd = result
                if (sm, sd) == (today.month, today.day):
                    if today_str + '_lbday' not in shown:
                        self._show_dialog(
                            "🎂 农历生日快乐",
                            "今天是小宝的农历生日！\n生日快乐哦，小宝~",
                            "🎂"
                        )
                        shown.append(today_str + '_lbday')
                        self.data['shown_holidays'] = shown
                        _save_easter_egg_data(self.data)

    def _check_consecutive(self):
        days = self.data.get('consecutive_days', 0)
        shown = self.data.get('shown_consecutive', [])

        milestones = [7, 30, 100, 365]
        for m in milestones:
            if days == m and m not in shown:
                msgs = {
                    7: "已连续使用 7 天啦，有什么新需求就告诉小狗 💪",
                    30: "连续使用 30 天啦！看来你已经是个熟练工了 🌟",
                    100: "连续使用 100 天啦！你一定是个电脑高手了 🔥",
                    365: "连续使用 365 天啦！看来小狗助理很有用！太棒啦！",
                }
                self._show_dialog("🔥 连续使用", msgs[m], "💪")
                shown.append(m)
                self.data['shown_consecutive'] = shown
                _save_easter_egg_data(self.data)


class FirstLoginDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("欢迎来到小狗助理")
        self.setFixedSize(380, 240)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)

        title = QLabel("🐕 欢迎来到小狗助理！")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FF9500;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("给自己起个昵称吧")
        hint_font = QFont()
        hint_font.setPointSize(12)
        hint.setFont(hint_font)
        hint.setStyleSheet("color: #666;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self.nick_edit = QLineEdit()
        self.nick_edit.setPlaceholderText("输入你的昵称...")
        self.nick_edit.setMaxLength(20)
        nick_font = QFont()
        nick_font.setPointSize(14)
        self.nick_edit.setFont(nick_font)
        self.nick_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nick_edit.returnPressed.connect(self._confirm)
        layout.addWidget(self.nick_edit)

        btn = QPushButton("开始使用 🐾")
        btn.clicked.connect(self._confirm)
        btn.setFixedWidth(160)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog { background-color: white; border-radius: 8px; }
            QLineEdit { padding: 10px; border: 2px solid #FFB347; border-radius: 8px;
                        min-height: 30px; font-size: 14px; }
            QLineEdit:focus { border-color: #FF9500; }
            QPushButton { background-color: #FFB347; color: white; border: none;
                          padding: 8px 20px; border-radius: 6px; font-weight: bold;
                          min-height: 32px; }
            QPushButton:hover { background-color: #FF9500; }
        """)

    def _confirm(self):
        nick = self.nick_edit.text().strip()
        if not nick:
            self.nick_edit.setStyleSheet(
                self.nick_edit.styleSheet().replace(
                    "border: 2px solid #FFB347;",
                    "border: 2px solid red;"))
            return
        self.nickname = nick
        self.accept()


class EasterEggSettingsDialog(QDialog):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("神秘彩蛋")
        self.setFixedSize(340, 240)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(25, 20, 25, 20)

        title = QLabel("🐕 神秘彩蛋")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FF9500;")
        layout.addWidget(title)

        # 计算陪伴天数
        first_str = data.get('first_use_date', '')
        nickname = data.get('nickname', '')
        try:
            first_date = date.fromisoformat(first_str)
            days = (date.today() - first_date).days
        except Exception:
            days = 0

        info_font = QFont()
        info_font.setPointSize(13)

        name_text = f"{nickname}，" if nickname else ""
        self.days_label = QLabel(f"{name_text}小狗助理已经陪伴你 {days} 天了 🐾")
        self.days_label.setFont(info_font)
        self.days_label.setStyleSheet("color: #555;")
        layout.addWidget(self.days_label)

        hint_label = QLabel("多多使用会有惊喜彩蛋哦 ✨")
        hint_label.setFont(info_font)
        hint_label.setStyleSheet("color: #FF9500;")
        layout.addWidget(hint_label)

        # 修改昵称
        nick_layout = QHBoxLayout()
        nick_label = QLabel("昵称:")
        nick_label.setFont(info_font)
        nick_label.setStyleSheet("color: #999;")
        self.nick_edit = QLineEdit()
        self.nick_edit.setText(nickname)
        self.nick_edit.setMaxLength(20)
        self.nick_edit.setFixedWidth(150)
        nick_font = QFont()
        nick_font.setPointSize(12)
        self.nick_edit.setFont(nick_font)
        btn_change = QPushButton("修改")
        btn_change.setFixedWidth(60)
        btn_change.clicked.connect(self._change_nickname)
        nick_layout.addWidget(nick_label)
        nick_layout.addWidget(self.nick_edit)
        nick_layout.addWidget(btn_change)
        nick_layout.addStretch()
        layout.addLayout(nick_layout)

        btn = QPushButton("知道啦～")
        btn.clicked.connect(self.accept)
        btn.setFixedWidth(120)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog { background-color: white; border-radius: 8px; }
            QLineEdit { padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; min-height: 24px; }
            QPushButton { background-color: #FFB347; color: white; border: none;
                          padding: 6px 15px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #FF9500; }
        """)

    def _change_nickname(self):
        new_nick = self.nick_edit.text().strip()
        if not new_nick:
            return
        self.data['nickname'] = new_nick
        _save_easter_egg_data(self.data)
        # 更新陪伴天数标签
        first_str = self.data.get('first_use_date', '')
        try:
            first_date = date.fromisoformat(first_str)
            days = (date.today() - first_date).days
        except Exception:
            days = 0
        self.days_label.setText(f"{new_nick}，小狗助理已经陪伴你 {days} 天了 🐾")


def main():
    global qApp

    def exception_hook(exc_type, exc_value, exc_tb):
        import traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"未捕获的异常:\n{error_msg}")
        try:
            QMessageBox.critical(None, "错误", f"程序发生错误：\n{str(exc_value)}")
        except Exception:
            pass

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    qApp = app

    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'dog.ico')
    else:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dog.ico')
    app.setWindowIcon(QIcon(icon_path))

    if sys.platform == 'win32':
        try:
            import ctypes
            myappid = 'PupAide.App.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

    window = PupAideMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
