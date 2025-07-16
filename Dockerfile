# 使用最新的 CUDA 镜像支持 50 系列显卡
FROM nvidia/cuda:12.3-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=all

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    wget \
    curl \
    git \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgoogle-perftools4 \
    libtcmalloc-minimal4 \
    && rm -rf /var/lib/apt/lists/*

# 创建 python3 软链接
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# 升级 pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# 复制 requirements 文件
COPY requirements.txt /app/

# 安装 PyTorch 和相关依赖（针对 CUDA 12.3）
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装其他依赖
RUN pip3 install -r requirements.txt

# 复制应用代码
COPY . /app/

# 设置权限
RUN chmod +x /app/main.py

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5566/health || exit 1

# 暴露端口
EXPOSE 5566

# 启动命令
CMD ["python3", "main.py"] 