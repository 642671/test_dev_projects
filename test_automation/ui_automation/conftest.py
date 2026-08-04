"""
UI 自动化模块级 conftest
提供 UI 测试专用的 fixtures：
- driver: 浏览器实例管理（函数级）
- base_url: 测试环境 URL（会话级）
- clean_cookies: 清理 cookies
- screenshot_on_failure: 失败截图
"""
import pytest
import os
import sys

# 关键：优先加载本模块的 config（确保 from config.settings 取到 ui_automation/config/settings.py）
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from config.settings import settings           # ← ui_automation/config/settings.py
from common.logger import get_logger          # ← common/（项目根目录）
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

logger = get_logger("ui_conftest")


@pytest.fixture(scope="function")
def driver(request):
    """
    函数级 WebDriver fixture
    每个测试函数获得独立的浏览器实例
    """
    browser_config = settings.get("browser", {})
    browser_type = browser_config.get("type", "chrome")
    headless = browser_config.get("headless", False)

    logger.info(f"初始化浏览器: type={browser_type}, headless={headless}")

    if browser_type == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        _driver = webdriver.Chrome(options=options)
    elif browser_type == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        _driver = webdriver.Firefox(options=options)
    else:
        raise ValueError(f"不支持的浏览器类型: {browser_type}")

    # 设置超时
    implicit_wait = browser_config.get("implicit_wait", 10)
    page_load_timeout = browser_config.get("page_load_timeout", 30)
    _driver.implicitly_wait(implicit_wait)
    _driver.set_page_load_timeout(page_load_timeout)
    _driver.maximize_window()

    logger.info(f"浏览器已启动: {browser_type}")

    yield _driver

    _driver.quit()
    logger.info("浏览器已关闭")


@pytest.fixture(scope="session")
def base_url():
    """会话级 - 基础 URL（从本模块配置读取）"""
    url = settings.base_url
    logger.info(f"测试环境 URL: {url}")
    return url


@pytest.fixture(scope="function")
def clean_cookies(driver):
    """清理浏览器 cookies"""
    yield
    driver.delete_all_cookies()
    logger.debug("已清理所有 cookies")


@pytest.fixture(scope="function")
def screenshot_on_failure(request, driver):
    """
    失败时自动截图 fixture
    使用方式: 测试方法参数中加入 screenshot_on_failure
    """
    yield
    if request.node.rep_call and request.node.rep_call.failed:
        reports_dir = os.path.join(_MODULE_DIR, "reports", "screenshots")
        os.makedirs(reports_dir, exist_ok=True)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FAIL_{request.node.name}_{timestamp}.png"
        filepath = os.path.join(reports_dir, filename)
        driver.save_screenshot(filepath)
        logger.error(f"测试失败截图: {filepath}")
