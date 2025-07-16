# 水印去除服务 - 部署和使用指南

## 📋 项目概述

这是一个基于 Florence-2 和 LaMa 的智能水印检测与去除系统，提供完整的 REST API 接口，支持多卡 GPU 部署。

## 🚀 功能特性

- **智能检测**: 使用 Florence-2-large 进行 open-vocabulary 水印检测
- **专业修复**: 集成 IOPaint LaMa 模型进行高质量图像修复
- **双重去除**: 支持 LaMa 修复和透明化两种处理方式
- **REST API**: 完整的 FastAPI 接口，端口 5566
- **命令行工具**: 提供 CLI 版本用于批量处理
- **多卡支持**: 支持多 GPU 并行处理
- **50系列显卡**: 针对最新 NVIDIA 50 系列显卡优化
- **Docker 容器化**: 完整的 Docker 部署方案

## 🛠️ 系统要求

### 硬件要求
- NVIDIA GPU (推荐 50 系列或更高)
- GPU 显存 >= 8GB (推荐 16GB+)
- 系统内存 >= 16GB
- 存储空间 >= 20GB

### 软件要求
- Docker Desktop (最新版本)
- Docker Compose
- NVIDIA Docker 运行时
- CUDA 12.3+ 驱动

## 📦 快速部署

### Windows 部署

1. **克隆项目**
```bash
git clone <your-repo>
cd watermark-remove
```

2. **运行部署脚本**
```bash
deploy.bat
```

### Linux 部署

1. **克隆项目**
```bash
git clone <your-repo>
cd watermark-remove
```

2. **运行部署脚本**
```bash
chmod +x deploy.sh
./deploy.sh
```

### 手动部署

如果自动部署脚本失败，可以手动执行：

```bash
# 创建目录
mkdir -p models_cache logs

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 🔧 配置说明

### 环境变量

可以在 `docker-compose.yml` 中修改以下环境变量：

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=all          # GPU 设备
  - NVIDIA_VISIBLE_DEVICES=all        # NVIDIA 设备
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### 端口配置

默认端口为 5566，可以在 `docker-compose.yml` 中修改：

```yaml
ports:
  - "5566:5566"  # 修改左侧端口号
```

## 📚 API 使用

### 服务端点

- **基础地址**: `http://localhost:5566`
- **API 文档**: `http://localhost:5566/docs`
- **健康检查**: `http://localhost:5566/health`

### 主要接口

#### 1. 水印去除 `/remove_watermark`

```python
import requests

# 上传图片并去除水印
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5566/remove_watermark',
        files={'file': f},
        data={
            'method': 'lama',           # 或 'transparent'
            'text_prompt': 'watermark',
            'max_bbox_percent': 0.3
        }
    )

result = response.json()
```

#### 2. 水印检测 `/detect_watermark`

```python
# 仅检测水印，不去除
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5566/detect_watermark',
        files={'file': f},
        data={
            'text_prompt': 'watermark',
            'max_bbox_percent': 0.3
        }
    )

result = response.json()
```

### 参数说明

- `method`: 处理方法
  - `lama`: 使用 LaMa 模型修复
  - `transparent`: 透明化处理
- `text_prompt`: 检测提示词（默认: "watermark"）
- `max_bbox_percent`: 最大边界框百分比（默认: 10.0）

## 🧪 测试使用

### API 测试

运行 API 测试脚本：

```bash
python api_examples.py
```

该脚本包含：
- 健康检查
- 水印检测示例
- 水印去除示例
- 批量处理示例

### 命令行工具

除了 API 接口，还提供命令行工具用于本地处理：

```bash
# 单个文件处理 - LaMa 修复
python cli_tool.py input.jpg output.jpg

# 单个文件处理 - 透明化
python cli_tool.py input.jpg output.png --transparent

# 批量处理目录
python cli_tool.py input_dir/ output_dir/ --overwrite

# 调整检测参数
python cli_tool.py input.jpg output.jpg --max-bbox-percent 15.0

# 强制输出格式
python cli_tool.py input.jpg output.jpg --force-format PNG
```

命令行参数说明：
- `--transparent`: 透明化水印区域而不是修复
- `--overwrite`: 覆盖现有文件（批量模式）
- `--max-bbox-percent`: 边界框可覆盖图像的最大百分比（默认 10.0）
- `--force-format`: 强制输出格式（PNG/WEBP/JPG）

## 📊 性能优化

### GPU 优化

1. **多卡负载均衡**
```yaml
# 在 docker-compose.yml 中指定特定 GPU
environment:
  - CUDA_VISIBLE_DEVICES=0,1,2,3
```

2. **内存优化**
```python
# 在 main.py 中调整模型精度
torch_dtype=torch.float16  # 或 torch.bfloat16
```

### 并发处理

默认使用单进程，可以通过修改启动参数增加并发：

```python
# 在 main.py 中修改
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=5566,
    workers=4,  # 增加工作进程
)
```

## 🔍 故障排除

### 常见问题

1. **GPU 不可用**
```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.3-base-ubuntu22.04 nvidia-smi
```

2. **内存不足**
```bash
# 清理 Docker 缓存
docker system prune -a
```

3. **模型下载失败**
```bash
# 手动下载模型（在容器内）
docker exec -it watermark-remove_watermark-remover_1 bash
python -c "from transformers import AutoProcessor; AutoProcessor.from_pretrained('microsoft/Florence-2-large-ft')"
```

### 日志查看

```bash
# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f watermark-remover
```

## 🔒 安全配置

### 生产环境部署

1. **限制访问**
```yaml
# 在 docker-compose.yml 中
ports:
  - "127.0.0.1:5566:5566"  # 仅本地访问
```

2. **添加认证**
```python
# 在 main.py 中添加 API 密钥验证
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header()):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
```

## 📈 监控和维护

### 健康检查

```bash
# 检查服务状态
curl http://localhost:5566/health

# 检查 GPU 使用情况
docker exec watermark-remove_watermark-remover_1 nvidia-smi
```

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看 GPU 使用情况
watch -n 1 nvidia-smi
```

## 🆕 版本更新

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose build --no-cache
docker-compose up -d
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📝 许可证

[请根据实际情况添加许可证信息] 