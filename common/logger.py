# common/logger.py - 统一日志配置模块
"""
使用 loguru 实现统一日志管理：
- 控制台输出（INFO 级别及以上）
- 文件输出（DEBUG 级别及以上，按天轮转，保留 7 天）
- 提供 get_logger() 函数供其他模块导入使用
"""

import sys
import os

from loguru import logger

# 日志格式：时间 | 级别 | 模块名 | 消息
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[module]}</cyan> | "
    "<level>{message}</level>"
)

# 文件日志格式（不含颜色标签）
FILE_LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{extra[module]} | "
    "{message}"
)

# 日志输出目录：项目根目录下的 logs/ 文件夹
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 移除默认 handler，避免重复输出
logger.remove()

# 配置默认的 module 字段，防止未绑定时报错
logger.configure(extra={"module": "main"})

# 添加控制台输出 handler（INFO 级别及以上）
logger.add(
    sys.stdout,
    level="INFO",
    format=LOG_FORMAT,
    colorize=True,
)

# 添加文件输出 handler（DEBUG 级别及以上，按天轮转，保留 7 天）
logger.add(
    os.path.join(LOG_DIR, "{time:YYYY-MM-DD}.log"),
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format=FILE_LOG_FORMAT,
    encoding="utf-8",
)


def get_logger(name: str = None):
    """
    获取 logger 实例

    Args:
        name: 模块名称，用于日志中标识来源模块

    Returns:
        绑定了模块名的 logger 实例

    Usage:
        from common.logger import get_logger
        logger = get_logger("api_client")
        logger.info("请求发送成功")
    """
    if name:
        return logger.bind(module=name)
    return logger
