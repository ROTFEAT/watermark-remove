#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印去除命令行工具
基于 Florence-2 和 LaMa 的智能水印检测与去除系统
"""

import sys
import click
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from transformers import AutoProcessor, AutoModelForCausalLM
from iopaint.model_manager import ModelManager
from iopaint.schema import HDStrategy, LDMSampler, InpaintRequest as Config
import torch
from torch.nn import Module
import tqdm
from loguru import logger
from enum import Enum

try:
    from cv2.typing import MatLike
except ImportError:
    MatLike = np.ndarray

class TaskType(str, Enum):
    OPEN_VOCAB_DETECTION = "<OPEN_VOCABULARY_DETECTION>"
    """Detect bounding box for objects and OCR text"""

def identify(task_prompt: TaskType, image: Image.Image, text_input: str, model: AutoModelForCausalLM, processor: AutoProcessor, device: str):
    """使用 Florence-2 进行目标检测"""
    if not isinstance(task_prompt, TaskType):
        raise ValueError(f"task_prompt must be a TaskType, but {task_prompt} is of type {type(task_prompt)}")

    prompt = task_prompt.value if text_input is None else task_prompt.value + text_input
    inputs = processor(text=prompt, images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    return processor.post_process_generation(
        generated_text, task=task_prompt.value, image_size=(image.width, image.height)
    )

def get_watermark_mask(image: Image.Image, model: AutoModelForCausalLM, processor: AutoProcessor, device: str, max_bbox_percent: float):
    """检测水印并生成掩膜"""
    text_input = "watermark"
    task_prompt = TaskType.OPEN_VOCAB_DETECTION
    parsed_answer = identify(task_prompt, image, text_input, model, processor, device)

    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)

    detection_key = "<OPEN_VOCABULARY_DETECTION>"
    if detection_key in parsed_answer and "bboxes" in parsed_answer[detection_key]:
        image_area = image.width * image.height
        for bbox in parsed_answer[detection_key]["bboxes"]:
            x1, y1, x2, y2 = map(int, bbox)
            bbox_area = (x2 - x1) * (y2 - y1)
            if (bbox_area / image_area) * 100 <= max_bbox_percent:
                draw.rectangle([x1, y1, x2, y2], fill=255)
            else:
                logger.warning(f"跳过过大的边界框: {bbox} 覆盖了 {bbox_area / image_area:.2%} 的图像")

    return mask

def process_image_with_lama(image: Image.Image, mask: Image.Image, model_manager: ModelManager):
    """使用 LaMa 模型修复图像"""
    config = Config(
        ldm_steps=50,
        ldm_sampler=LDMSampler.ddim,
        hd_strategy=HDStrategy.CROP,
        hd_strategy_crop_margin=64,
        hd_strategy_crop_trigger_size=800,
        hd_strategy_resize_limit=1600,
    )
    
    # 转换为 numpy 数组
    image_array = np.array(image)
    mask_array = np.array(mask)
    
    result = model_manager(image_array, mask_array, config)

    if result.dtype in [np.float64, np.float32]:
        result = np.clip(result, 0, 255).astype(np.uint8)

    return result

def make_region_transparent(image: Image.Image, mask: Image.Image):
    """将检测到的水印区域设置为透明"""
    image = image.convert("RGBA")
    mask = mask.convert("L")
    transparent_image = Image.new("RGBA", image.size)
    
    for x in range(image.width):
        for y in range(image.height):
            if mask.getpixel((x, y)) > 0:
                transparent_image.putpixel((x, y), (0, 0, 0, 0))
            else:
                transparent_image.putpixel((x, y), image.getpixel((x, y)))
    
    return transparent_image

@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.argument("output_path", type=click.Path())
@click.option("--overwrite", is_flag=True, help="覆盖现有文件（批量模式）")
@click.option("--transparent", is_flag=True, help="透明化水印区域而不是修复")
@click.option("--max-bbox-percent", default=10.0, help="边界框可覆盖图像的最大百分比")
@click.option("--force-format", type=click.Choice(["PNG", "WEBP", "JPG"], case_sensitive=False), default=None, help="强制输出格式，默认使用输入格式")
def main(input_path: str, output_path: str, overwrite: bool, transparent: bool, max_bbox_percent: float, force_format: str):
    """
    水印去除命令行工具
    
    INPUT_PATH: 输入图片路径或目录
    OUTPUT_PATH: 输出图片路径或目录
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # 设置设备
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"使用设备: {device}")
    
    # 加载 Florence-2 模型
    logger.info("加载 Florence-2 模型...")
    florence_model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Florence-2-large", 
        trust_remote_code=True
    ).to(device).eval()
    florence_processor = AutoProcessor.from_pretrained(
        "microsoft/Florence-2-large", 
        trust_remote_code=True
    )
    logger.info("Florence-2 模型加载完成")

    # 加载 LaMa 模型（如果不是透明模式）
    model_manager = None
    if not transparent:
        logger.info("加载 LaMa 模型...")
        model_manager = ModelManager(name="lama", device=device)
        logger.info("LaMa 模型加载完成")

    def handle_one(image_path: Path, output_path: Path):
        """处理单个图像"""
        if output_path.exists() and not overwrite:
            logger.info(f"跳过已存在的文件: {output_path}")
            return

        logger.info(f"处理图像: {image_path}")
        
        # 读取图像
        image = Image.open(image_path).convert("RGB")
        
        # 检测水印
        mask_image = get_watermark_mask(image, florence_model, florence_processor, device, max_bbox_percent)
        
        # 检查是否检测到水印
        mask_array = np.array(mask_image)
        if np.sum(mask_array) == 0:
            logger.warning(f"未在 {image_path} 中检测到水印")
            # 直接复制原图
            image.save(output_path)
            return

        # 处理图像
        if transparent:
            logger.info("透明化水印区域...")
            result_image = make_region_transparent(image, mask_image)
        else:
            logger.info("使用 LaMa 修复水印...")
            lama_result = process_image_with_lama(image, mask_image, model_manager)
            result_image = Image.fromarray(cv2.cvtColor(lama_result, cv2.COLOR_BGR2RGB))

        # 确定输出格式
        if force_format:
            output_format = force_format.upper()
        elif transparent:
            output_format = "PNG"
        else:
            output_format = image_path.suffix[1:].upper()
            if output_format not in ["PNG", "WEBP", "JPG"]:
                output_format = "PNG"
        
        # 映射 JPG 到 JPEG 以兼容 PIL
        if output_format == "JPG":
            output_format = "JPEG"

        # 透明图像需要使用 PNG 格式
        if transparent and output_format == "JPEG":
            logger.warning("检测到透明处理，改用 PNG 格式以支持透明度")
            output_format = "PNG"

        # 保存结果
        new_output_path = output_path.with_suffix(f".{output_format.lower()}")
        result_image.save(new_output_path, format=output_format)
        logger.info(f"输出保存到: {new_output_path}")

    # 处理输入
    if input_path.is_dir():
        # 批量处理
        if not output_path.exists():
            output_path.mkdir(parents=True)

        # 查找图像文件
        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp", "*.tiff"]
        images = []
        for ext in image_extensions:
            images.extend(input_path.glob(ext))
            images.extend(input_path.glob(ext.upper()))
        
        total_images = len(images)
        logger.info(f"找到 {total_images} 个图像文件")

        if total_images == 0:
            logger.error("在输入目录中未找到图像文件")
            sys.exit(1)

        # 处理每个图像
        for idx, image_path in enumerate(tqdm.tqdm(images, desc="处理图像")):
            output_file = output_path / image_path.name
            handle_one(image_path, output_file)
            progress = int((idx + 1) / total_images * 100)
            logger.info(f"进度: {progress}% ({idx + 1}/{total_images})")
    else:
        # 单个文件处理
        if transparent:
            output_file = output_path.with_suffix(".png")
        else:
            output_file = output_path
        handle_one(input_path, output_file)
        logger.info("处理完成: 100%")

if __name__ == "__main__":
    main() 