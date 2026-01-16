#!/usr/bin/env python3
"""
工具模块 - 提供通用的工具函数
"""

import asyncio
import re
import logging
from functools import wraps, partial
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Utils:
    """通用工具类"""
    
    # HTML转义映射表
    HTML_ESCAPE_TABLE = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
    }
    
    # Twitter URL正则表达式模式
    TWITTER_URL_PATTERNS = [
        r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
        r'https?://(?:www\.)?x\.com/\w+/status/\d+',
        r'twitter\.com/\w+/status/\d+',
        r'x\.com/\w+/status/\d+'
    ]
    
    TWEET_ID_PATTERNS = [
        r'(?:twitter|x)\.com/\w+/status/(\d+)',
        r'/status/(\d+)'
    ]
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        转义HTML特殊字符
        
        Args:
            text: 要转义的文本
            
        Returns:
            转义后的文本
        """
        if not text:
            return ""
        
        return "".join(Utils.HTML_ESCAPE_TABLE.get(c, c) for c in text)
    
    @staticmethod
    def is_twitter_url(text: str) -> bool:
        """
        检查文本是否包含Twitter URL
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否包含Twitter URL
        """
        if not text:
            return False
            
        for pattern in Utils.TWITTER_URL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def extract_tweet_id(url: str) -> Optional[str]:
        """
        从Twitter URL中提取推文ID
        
        Args:
            url: Twitter URL
            
        Returns:
            推文ID，如果无法提取则返回None
        """
        if not url:
            return None
            
        for pattern in Utils.TWEET_ID_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def format_datetime(dt) -> str:
        """
        格式化日期时间为字符串
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化后的字符串
        """
        if not dt:
            return ""
        
        try:
            if hasattr(dt, 'strftime'):
                return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            else:
                return str(dt)
        except Exception as e:
            logger.error(f"格式化日期时间失败: {e}")
            return str(dt)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
        """
        截断文本到指定长度
        
        Args:
            text: 原文本
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            截断后的文本
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length] + suffix
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """
        安全地将值转换为整数
        
        Args:
            value: 要转换的值
            default: 默认值
            
        Returns:
            转换后的整数或默认值
        """
        try:
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_str(value: Any, default: str = "") -> str:
        """
        安全地将值转换为字符串
        
        Args:
            value: 要转换的值
            default: 默认值
            
        Returns:
            转换后的字符串或默认值
        """
        try:
            if value is None:
                return default
            return str(value)
        except Exception:
            return default


def error_handler(func):
    """
    错误处理装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        包装后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}")
            return None
    return wrapper


def async_error_handler(func):
    """
    异步错误处理装饰器
    
    Args:
        func: 要装饰的异步函数
        
    Returns:
        包装后的异步函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"异步函数 {func.__name__} 执行失败: {e}")
            return None
    return wrapper


async def run_in_thread(func, *args, **kwargs):
    to_thread = getattr(asyncio, 'to_thread', None)
    if callable(to_thread):
        return await to_thread(func, *args, **kwargs)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


class MemoryManager:
    """内存管理器 - 用于管理内存使用的工具类"""
    
    def __init__(self, max_size: int = 1000, cleanup_threshold: float = 0.8):
        """
        初始化内存管理器
        
        Args:
            max_size: 最大存储数量
            cleanup_threshold: 清理阈值（当使用量达到此比例时触发清理）
        """
        self.max_size = max_size
        self.cleanup_threshold = cleanup_threshold
        self.data = {}
        self.access_times = {}
    
    def add(self, key: str, value: Any) -> None:
        """
        添加数据
        
        Args:
            key: 键
            value: 值
        """
        self.data[key] = value
        self.access_times[key] = datetime.now()
        
        # 检查是否需要清理
        if len(self.data) > self.max_size * self.cleanup_threshold:
            self._cleanup()
    
    def get(self, key: str) -> Any:
        """
        获取数据
        
        Args:
            key: 键
            
        Returns:
            值，如果不存在则返回None
        """
        if key in self.data:
            self.access_times[key] = datetime.now()
            return self.data[key]
        return None
    
    def remove(self, key: str) -> bool:
        """
        移除数据
        
        Args:
            key: 键
            
        Returns:
            是否成功移除
        """
        if key in self.data:
            del self.data[key]
            del self.access_times[key]
            return True
        return False
    
    def _cleanup(self) -> None:
        """清理最久未使用的数据"""
        if not self.data:
            return
        
        # 按访问时间排序，移除最久未使用的50%数据
        sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])
        items_to_remove = sorted_items[:len(sorted_items) // 2]
        
        for key, _ in items_to_remove:
            self.remove(key)
        
        logger.info(f"内存清理完成: 移除了 {len(items_to_remove)} 个条目，剩余 {len(self.data)} 个")
    
    def clear(self) -> None:
        """清空所有数据"""
        self.data.clear()
        self.access_times.clear()
        logger.info("内存管理器已清空")
    
    def size(self) -> int:
        """
        获取当前数据量
        
        Returns:
            当前存储的数据数量
        """
        return len(self.data)
    
    def is_full(self) -> bool:
        """
        检查是否已满
        
        Returns:
            是否达到最大容量
        """
        return len(self.data) >= self.max_size


# 全局工具实例
utils = Utils()