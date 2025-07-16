#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印去除服务 API 使用示例
"""

import requests
import base64
import json
from pathlib import Path

# 服务地址
API_BASE_URL = "http://localhost:5566"

def test_health():
    """测试服务健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print("🔍 健康检查结果:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def remove_watermark_example(image_path: str, method: str = "lama"):
    """
    水印去除示例
    
    Args:
        image_path: 图片路径
        method: 处理方法 ("lama" 或 "transparent")
    """
    try:
        # 读取图片文件
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'method': method,
                'text_prompt': 'watermark',
                'max_bbox_percent': 10.0
            }
            
            print(f"🔧 正在处理图片: {image_path}")
            print(f"📋 处理方法: {method}")
            
            response = requests.post(
                f"{API_BASE_URL}/remove_watermark",
                files=files,
                data=data,
                timeout=120
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 水印去除成功!")
            
            # 保存结果图片
            if 'result' in result:
                image_data = base64.b64decode(result['result'])
                output_format = result.get('format', 'JPEG').lower()
                output_path = f"result_{method}.{output_format.lower()}"
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                print(f"💾 结果保存到: {output_path}")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

def detect_watermark_example(image_path: str):
    """
    水印检测示例（仅检测，不去除）
    
    Args:
        image_path: 图片路径
    """
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'text_prompt': 'watermark',
                'max_bbox_percent': 10.0
            }
            
            print(f"🔍 正在检测水印: {image_path}")
            
            response = requests.post(
                f"{API_BASE_URL}/detect_watermark",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 水印检测完成!")
            print(f"🎯 检测结果: {'发现水印' if result.get('has_watermark') else '未发现水印'}")
            print(f"📊 检测比例: {result.get('detection_ratio', 0):.4f}")
            print(f"🔢 检测像素: {result.get('detected_pixels', 0)}")
            
            # 保存掩膜图片
            if 'mask' in result:
                mask_data = base64.b64decode(result['mask'])
                mask_path = "detected_mask.png"
                
                with open(mask_path, 'wb') as f:
                    f.write(mask_data)
                
                print(f"🎭 掩膜保存到: {mask_path}")
            
            return True
        else:
            print(f"❌ 检测失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 检测失败: {e}")
        return False

def batch_process_example(image_dir: str, method: str = "lama"):
    """
    批量处理示例
    
    Args:
        image_dir: 图片目录
        method: 处理方法
    """
    image_dir_path = Path(image_dir)
    if not image_dir_path.exists():
        print(f"❌ 目录不存在: {image_dir}")
        return
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    # 查找所有图片文件
    image_files = [
        f for f in image_dir_path.iterdir() 
        if f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        print(f"❌ 目录中没有找到图片文件: {image_dir}")
        return
    
    print(f"📁 找到 {len(image_files)} 个图片文件")
    
    success_count = 0
    for i, image_file in enumerate(image_files, 1):
        print(f"\n📸 处理第 {i}/{len(image_files)} 个文件: {image_file.name}")
        
        if remove_watermark_example(str(image_file), method):
            success_count += 1
    
    print(f"\n🎉 批量处理完成: {success_count}/{len(image_files)} 成功")

if __name__ == "__main__":
    print("🚀 水印去除服务 API 使用示例")
    print("=" * 50)
    
    # 1. 健康检查
    print("\n1. 健康检查")
    if not test_health():
        print("❌ 服务未启动或不可用")
        exit(1)
    
    # 2. 使用示例（需要提供实际的图片路径）
    print("\n2. API 使用示例")
    print("请修改以下示例中的图片路径:")
    print()
    print("# 水印去除 (LaMa 方法)")
    print('# remove_watermark_example("your_image.jpg", "lama")')
    print()
    print("# 水印去除 (透明化方法)")
    print('# remove_watermark_example("your_image.jpg", "transparent")')
    print()
    print("# 仅检测水印")
    print('# detect_watermark_example("your_image.jpg")')
    print()
    print("# 批量处理")
    print('# batch_process_example("./images/", "lama")')
    
    # 如果有测试图片，可以取消注释下面的代码
    # test_image = "test.jpg"  # 替换为实际的测试图片路径
    # if Path(test_image).exists():
    #     print(f"\n🧪 测试图片: {test_image}")
    #     detect_watermark_example(test_image)
    #     remove_watermark_example(test_image, "lama")
    #     remove_watermark_example(test_image, "transparent") 