#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印去除服务配置文件
"""

import torch
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelConfig:
    """模型配置"""
    florence_model_name: str = "microsoft/Florence-2-large"
    max_bbox_percent: float = 10.0
    torch_dtype: torch.dtype = torch.float32
    device_map: str = None
    num_threads: int = 4

@dataclass
class InferenceConfig:
    """推理配置"""
    max_new_tokens: int = 1024
    num_beams: int = 3
    early_stopping: bool = False
    do_sample: bool = False

@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 5566
    workers: int = 1
    log_level: str = "info"

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._setup_configs()
    
    def _setup_configs(self):
        """根据设备类型设置配置"""
        if self.device == "cuda":
            self.model_config = ModelConfig(
                torch_dtype=torch.float16,
                device_map="auto",
                num_threads=None
            )
            self.inference_config = InferenceConfig(
                max_new_tokens=1024,
                num_beams=3
            )
        else:
            # CPU 优化配置
            self.model_config = ModelConfig(
                torch_dtype=torch.float32,
                device_map=None,
                num_threads=4
            )
            self.inference_config = InferenceConfig(
                max_new_tokens=512,
                num_beams=1  # CPU 环境下减少束搜索
            )
        
        self.server_config = ServerConfig()
    
    def get_model_kwargs(self) -> Dict[str, Any]:
        """获取模型加载参数"""
        kwargs = {
            "trust_remote_code": True,
            "torch_dtype": self.model_config.torch_dtype,
        }
        
        if self.model_config.device_map:
            kwargs["device_map"] = self.model_config.device_map
            
        return kwargs
    
    def get_generation_kwargs(self, base_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取生成参数"""
        # 更新基础参数
        base_kwargs.update({
            "max_new_tokens": self.inference_config.max_new_tokens,
            "num_beams": self.inference_config.num_beams,
            "early_stopping": self.inference_config.early_stopping,
            "do_sample": self.inference_config.do_sample,
        })
        
        return base_kwargs
    
    def setup_cpu_optimization(self):
        """设置 CPU 优化"""
        if self.device == "cpu" and self.model_config.num_threads:
            torch.set_num_threads(self.model_config.num_threads)
            # 设置 CPU 优化标志
            torch.backends.mkldnn.enabled = True
            if hasattr(torch.backends, 'mkl') and hasattr(torch.backends.mkl, 'enabled'):
                torch.backends.mkl.enabled = True

# 全局配置实例
config = ConfigManager() 