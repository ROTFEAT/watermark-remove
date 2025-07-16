#!/bin/bash

# 水印去除服务部署脚本

set -e

echo "🚀 开始部署水印去除服务..."

# 检查 Docker 和 Docker Compose 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查 NVIDIA Docker 运行时
if ! docker run --rm --gpus all nvidia/cuda:12.3-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA Docker 运行时配置有问题，请检查 GPU 驱动和 nvidia-docker"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p models_cache
mkdir -p logs

# 构建镜像
echo "🔧 构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -f http://localhost:5566/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo "🌐 API 地址: http://localhost:5566"
    echo "📖 API 文档: http://localhost:5566/docs"
    echo "🔧 健康检查: http://localhost:5566/health"
else
    echo "❌ 服务启动失败，查看日志:"
    docker-compose logs
    exit 1
fi

echo "🎉 部署完成！" 