# 水印去除服务

基于 Florence-2 和 LaMa 的智能水印检测与去除系统，提供完整的 REST API 接口。

## ✨ 特性

- 🔍 **智能检测**: 使用 Florence-2 进行 open-vocabulary 水印检测
- 🛠️ **双重去除**: 支持 LaMa 修复和透明化两种处理方式  
- 🚀 **REST API**: 完整的 FastAPI 接口，暴露在 5566 端口
- 🖥️ **多卡支持**: 支持多 GPU 并行处理
- 💎 **50系列显卡**: 针对最新 NVIDIA 50 系列显卡优化
- 🐳 **Docker 容器化**: 开箱即用的 Docker 部署方案

## 🚀 快速开始

### Windows 用户
```bash
# 克隆项目
git clone <your-repo>
cd watermark-remove

# 一键部署
deploy.bat
```

### Linux 用户
```bash
# 克隆项目
git clone <your-repo>
cd watermark-remove

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

部署成功后访问：
- 🌐 API 服务: http://localhost:5566
- 📖 API 文档: http://localhost:5566/docs
- 🔧 健康检查: http://localhost:5566/health

## 📁 项目结构

```
watermark-remove/
├── main.py              # 主服务代码
├── cli_tool.py          # 命令行工具
├── config.py            # 配置管理
├── quick_test.py        # 快速测试脚本
├── requirements.txt     # Python 依赖
├── Dockerfile          # Docker 镜像配置
├── docker-compose.yml  # Docker Compose 配置
├── deploy.sh           # Linux 部署脚本
├── deploy.bat          # Windows 部署脚本
├── api_examples.py     # API 使用示例
├── README_DEPLOY.md    # 详细部署文档
├── CPU_TEST_GUIDE.md   # CPU 测试指南
└── .dockerignore       # Docker 忽略文件
```

## 🔧 核心功能

### 1. API 接口
```python
import requests

# 水印检测
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5566/detect_watermark',
        files={'file': f},
        data={'text_prompt': 'watermark'}
    )

# 水印去除
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5566/remove_watermark',
        files={'file': f},
        data={'method': 'lama'}  # 或 'transparent'
    )
```

### 2. 命令行工具
```bash
# 单个文件处理
python cli_tool.py input.jpg output.jpg

# 透明化处理
python cli_tool.py input.jpg output.png --transparent

# 批量处理
python cli_tool.py input_dir/ output_dir/ --overwrite
```

## 🛠️ 技术栈

- **检测模型**: Microsoft Florence-2-large
- **修复模型**: IOPaint LaMa (Large Mask Inpainting)
- **API 框架**: FastAPI
- **CLI 框架**: Click
- **图像处理**: OpenCV, PIL
- **深度学习**: PyTorch, Transformers
- **容器化**: Docker, Docker Compose

## 📚 详细文档

查看 [README_DEPLOY.md](README_DEPLOY.md) 获取：
- 详细部署指南
- API 使用说明
- 性能优化建议
- 故障排除方法

## 🧪 测试

### 快速测试（推荐）
```bash
# 健康检查
python quick_test.py --health

# 完整功能测试
python quick_test.py
```

### API 示例
```bash
python api_examples.py
```

### CPU 环境测试
如果您在 CPU 环境下测试，请查看：📖 [CPU 测试指南](CPU_TEST_GUIDE.md)

## 🎯 用例场景

- 📷 图片批量水印去除
- 🖼️ 产品图片清理
- 📱 社交媒体内容处理
- 🎨 图像编辑工具集成

## 💡 提示

- 首次启动会自动下载模型，需要一定时间
- 建议使用 16GB+ 显存的 GPU 获得最佳性能
- 支持批量处理和异步调用

---

🔗 **相关链接**: [详细文档](README_DEPLOY.md) | [API 示例](api_examples.py) | [CPU 测试指南](CPU_TEST_GUIDE.md)

