@echo off
REM 水印去除服务部署脚本 (Windows 版本)

echo 🚀 开始部署水印去除服务...

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM 检查 Docker Compose 是否安装
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose 未安装，请先安装 Docker Compose
    pause
    exit /b 1
)

REM 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行，请启动 Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过

REM 创建必要的目录
echo 📁 创建必要目录...
if not exist "models_cache" mkdir models_cache
if not exist "logs" mkdir logs

REM 构建镜像
echo 🔧 构建 Docker 镜像...
docker-compose build
if %errorlevel% neq 0 (
    echo ❌ 镜像构建失败
    pause
    exit /b 1
)

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 30 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
curl -f http://localhost:5566/health >nul 2>&1
if %errorlevel% eq 0 (
    echo ✅ 服务启动成功！
    echo 🌐 API 地址: http://localhost:5566
    echo 📖 API 文档: http://localhost:5566/docs
    echo 🔧 健康检查: http://localhost:5566/health
) else (
    echo ❌ 服务启动失败，查看日志:
    docker-compose logs
    pause
    exit /b 1
)

echo 🎉 部署完成！
echo.
echo 💡 提示:
echo - 使用 docker-compose logs 查看日志
echo - 使用 docker-compose stop 停止服务
echo - 使用 docker-compose down 完全停止并删除容器
echo.
pause 