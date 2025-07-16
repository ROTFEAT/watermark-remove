#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印去除服务快速测试脚本
适用于 CPU 环境下的基本功能验证
"""

import sys
import time
import requests
import base64
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from loguru import logger

# 配置日志
logger.add(sys.stdout, level="INFO")

def create_test_image_with_watermark(size=(800, 600), output_path="test_watermark.jpg"):
    """创建一个带水印的测试图片"""
    # 创建基础图片
    image = Image.new('RGB', size, color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    # 绘制一些内容
    draw.rectangle([50, 50, size[0]-50, size[1]-50], outline=(100, 100, 100), width=3)
    draw.text((100, 100), "这是一张测试图片", fill=(50, 50, 50))
    draw.text((100, 150), "用于验证水印去除功能", fill=(50, 50, 50))
    
    # 添加水印 - 半透明文本
    watermark = Image.new('RGBA', size, (255, 255, 255, 0))
    watermark_draw = ImageDraw.Draw(watermark)
    
    # 在多个位置添加水印文本
    positions = [(200, 200), (400, 300), (600, 400)]
    for pos in positions:
        watermark_draw.text(pos, "WATERMARK", fill=(255, 0, 0, 128))
    
    # 合并图片和水印
    image = Image.alpha_composite(image.convert('RGBA'), watermark).convert('RGB')
    
    # 保存测试图片
    image.save(output_path, quality=95)
    logger.info(f"创建测试图片: {output_path}")
    return output_path

def test_api_health(base_url="http://localhost:5566"):
    """测试 API 健康状态"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            logger.success("✅ API 服务健康检查通过")
            return True
        else:
            logger.error(f"❌ API 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 无法连接到 API 服务: {e}")
        return False

def test_watermark_detection(image_path, base_url="http://localhost:5566"):
    """测试水印检测功能"""
    try:
        logger.info("🔍 测试水印检测功能...")
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'text_prompt': 'watermark',
                'max_bbox_percent': 10.0
            }
            
            start_time = time.time()
            response = requests.post(
                f"{base_url}/detect_watermark",
                files=files,
                data=data,
                timeout=120
            )
            end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            logger.success(f"✅ 水印检测成功 (耗时: {end_time - start_time:.2f}秒)")
            logger.info(f"检测结果: {'发现水印' if result.get('has_watermark') else '未发现水印'}")
            logger.info(f"检测比例: {result.get('detection_ratio', 0):.4f}")
            
            # 保存掩膜图片
            if 'mask' in result:
                mask_data = base64.b64decode(result['mask'])
                with open('test_mask.png', 'wb') as f:
                    f.write(mask_data)
                logger.info("掩膜图片保存为: test_mask.png")
            
            return True
        else:
            logger.error(f"❌ 水印检测失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 水印检测异常: {e}")
        return False

def test_watermark_removal(image_path, method="lama", base_url="http://localhost:5566"):
    """测试水印去除功能"""
    try:
        logger.info(f"🛠️ 测试水印去除功能 (方法: {method})...")
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'method': method,
                'text_prompt': 'watermark',
                'max_bbox_percent': 10.0
            }
            
            start_time = time.time()
            response = requests.post(
                f"{base_url}/remove_watermark",
                files=files,
                data=data,
                timeout=300  # CPU 环境可能需要更多时间
            )
            end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            logger.success(f"✅ 水印去除成功 (耗时: {end_time - start_time:.2f}秒)")
            
            # 保存结果图片
            if 'result' in result:
                image_data = base64.b64decode(result['result'])
                output_format = result.get('format', 'JPEG').lower()
                output_path = f"test_result_{method}.{output_format.lower()}"
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"结果图片保存为: {output_path}")
            
            return True
        else:
            logger.error(f"❌ 水印去除失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 水印去除异常: {e}")
        return False

def run_comprehensive_test():
    """运行综合测试"""
    logger.info("🚀 开始水印去除服务综合测试")
    logger.info("=" * 60)
    
    # 创建测试图片
    test_image = create_test_image_with_watermark()
    
    # 等待服务启动
    logger.info("⏳ 等待服务启动...")
    max_retries = 12  # 等待最多 2 分钟
    for i in range(max_retries):
        if test_api_health():
            break
        if i < max_retries - 1:
            logger.info(f"等待服务启动... ({i+1}/{max_retries})")
            time.sleep(10)
        else:
            logger.error("❌ 服务启动超时，请检查服务状态")
            return False
    
    # 运行测试
    tests_passed = 0
    total_tests = 3
    
    # 测试 1: 水印检测
    if test_watermark_detection(test_image):
        tests_passed += 1
    
    # 测试 2: LaMa 修复
    if test_watermark_removal(test_image, "lama"):
        tests_passed += 1
    
    # 测试 3: 透明化处理
    if test_watermark_removal(test_image, "transparent"):
        tests_passed += 1
    
    # 测试结果
    logger.info("=" * 60)
    if tests_passed == total_tests:
        logger.success(f"🎉 所有测试通过! ({tests_passed}/{total_tests})")
        logger.info("服务运行正常，可以开始使用")
    else:
        logger.warning(f"⚠️ 部分测试失败 ({tests_passed}/{total_tests})")
        logger.info("请检查日志以了解具体问题")
    
    return tests_passed == total_tests

def quick_performance_test():
    """快速性能测试"""
    logger.info("⚡ 快速性能测试")
    
    # 创建小尺寸测试图片
    small_image = create_test_image_with_watermark((400, 300), "test_small.jpg")
    
    if not test_api_health():
        logger.error("服务不可用")
        return
    
    # 测试检测性能
    start_time = time.time()
    if test_watermark_detection(small_image):
        detection_time = time.time() - start_time
        logger.info(f"检测耗时: {detection_time:.2f}秒")
    
    # 清理测试文件
    Path(small_image).unlink(missing_ok=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="水印去除服务快速测试")
    parser.add_argument("--url", default="http://localhost:5566", help="API 服务地址")
    parser.add_argument("--quick", action="store_true", help="仅运行快速测试")
    parser.add_argument("--health", action="store_true", help="仅检查服务健康状态")
    
    args = parser.parse_args()
    
    if args.health:
        # 仅健康检查
        if test_api_health(args.url):
            logger.success("服务正常运行")
            sys.exit(0)
        else:
            logger.error("服务不可用")
            sys.exit(1)
    elif args.quick:
        # 快速测试
        quick_performance_test()
    else:
        # 综合测试
        success = run_comprehensive_test()
        sys.exit(0 if success else 1) 