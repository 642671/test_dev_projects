"""
自定义装饰器集合
提供重试、截图、执行时间记录等通用功能
"""
import functools
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.logger import get_logger

logger = get_logger("decorators")


def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    重试装饰器 - 指数退避
    
    :param max_attempts: 最大重试次数
    :param delay: 初始延迟（秒）
    :param backoff: 退避倍数
    :param exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"[重试] {func.__name__} 在第 {attempt} 次尝试后最终失败: {e}")
                        raise
                    wait_time = delay * (backoff ** (attempt - 1))
                    logger.warning(
                        f"[重试] {func.__name__} 第 {attempt} 次失败，"
                        f"等待 {wait_time:.1f}s 后重试 (剩余 {max_attempts - attempt} 次)"
                    )
                    time.sleep(wait_time)
        return wrapper
    return decorator


def screenshot_on_error(func):
    """
    异常时自动截图装饰器
    适用于 Page Object 方法（self 需要有 take_screenshot 方法）
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 尝试获取 self（第一个参数）的截图方法
            if args and hasattr(args[0], 'take_screenshot'):
                try:
                    args[0].take_screenshot(f"error_{func.__name__}")
                    logger.info(f"[截图] 异常截图已保存: error_{func.__name__}")
                except Exception as screenshot_error:
                    logger.warning(f"[截图] 截图失败: {screenshot_error}")
            raise
    return wrapper


def log_execution_time(func):
    """
    记录方法执行时间装饰器
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"[计时] 开始执行: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"[计时] 执行完成: {func.__name__}, 耗时: {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[计时] 执行失败: {func.__name__}, 耗时: {elapsed:.2f}s, 错误: {e}")
            raise
    return wrapper


def log_step(step_description):
    """
    测试步骤日志装饰器
    用于标记测试步骤
    
    使用方式：
        @log_step("输入用户名和密码")
        def login(self, username, password):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"[步骤] >>> {step_description}")
            result = func(*args, **kwargs)
            logger.info(f"[步骤] <<< {step_description} - 完成")
            return result
        return wrapper
    return decorator


def allure_step(step_name):
    """
    Allure 步骤装饰器（兼容无 allure 环境）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                import allure
                with allure.step(step_name):
                    return func(*args, **kwargs)
            except ImportError:
                # 未安装 allure 时退化为普通日志
                logger.info(f"[Allure Step] {step_name}")
                return func(*args, **kwargs)
        return wrapper
    return decorator
