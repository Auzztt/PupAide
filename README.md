# PupAide 小狗助理

一个基于 PyQt6 的办公百宝箱桌面应用，集成文件管理、文档处理、文本分析等多种实用工具，采用橙色系现代 UI 设计。

> 注：该产品暂为私人使用创作，因此有专属彩蛋设定。


## 功能一览

| 功能 | 说明 |
|------|------|
| 重复文件查找器 | 基于 MD5 哈希快速扫描并清理重复文件，支持子文件夹递归 |
| 文件夹同步/备份 | 双向同步源文件夹与目标文件夹，支持覆盖、删除多余文件等策略 |
| 磁盘空间分析器 | 可视化分析磁盘/文件夹占用，大文件排行，支持图表展示 |
| 文件批量筛选 | 按人名名单批量筛选文件，支持从 Excel 导入名单，区分大小写等选项 |
| 文件名称提取器 | 按分隔符拆分文件名并提取指定部分，支持扩展名过滤，导出至 Excel |
| 文档拆分工具 | 支持 PDF / Word / Excel 智能拆分（按页数、自定义页码、书签、行数、工作表、文件大小），命名模板支持变量 |
| 文本重复识别 | 基于后缀数组算法检测文本中的重复片段，支持提取非重复/重复/去重内容 |

## 技术栈

- **Python 3.10+**
- **PyQt6** - GUI 框架
- **PyPDF2 / pdfplumber** - PDF 读写
- **python-docx** - Word 文档处理（可选）
- **openpyxl** - Excel 读写
- **reportlab** - PDF 生成
- **matplotlib** - 磁盘分析图表可视化
- **win32com** - Word COM 自动化（可选，仅 Windows）

## 安装与运行

```bash
# 克隆仓库
git clone https://github.com/Auzztt/PupAide.git
cd PupAide

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装依赖
pip install PyQt6 openpyxl reportlab pdfplumber PyPDF2 matplotlib python-docx pywin32

# 运行
python pup_aide.py
```

## 使用说明

1. 启动后通过左侧导航栏选择功能模块
2. 各功能页面独立操作，互不干扰
3. 首次启动会显示登录引导对话框
4. 右上角设置按钮可进入彩蛋设置页面

## 项目结构

```
PupAide/
├── pup_aide.py          # 主程序（全部功能代码）
├── paw-print.svg        # 应用图标素材
├── dog.ico              # 应用图标
├── README.md
└── LICENSE
```

## 版本

当前版本：v1.2.1

## 许可证

[MIT License](./LICENSE)
