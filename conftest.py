"""
pytest 全局配置
- WebDriver 初始化和销毁
- 失败自动截图
- 测试钩子函数
"""
import pytest
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# 项目根目录
ROOT_DIR = os.path.dirname(__file__)
import sys
sys.path.insert(0, ROOT_DIR)

from config.settings import settings
from common.logger import get_logger

logger = get_logger("conftest")


@pytest.fixture(scope="function")
def driver():
    """
    WebDriver fixture - 每个测试函数独立的浏览器实例
    
    注意：UI 自动化测试推荐使用 ui_automation/conftest.py 中的模块级 driver fixture，
    该 fixture 提供更完善的浏览器配置（headless=new、--disable-gpu 等）。
    此全局 driver 主要供非 UI 模块（如需要浏览器的集成测试）使用。

    根据 config/environments/{env}.yaml 中的 browser 配置来初始化浏览器：
    - type: 浏览器类型（chrome / firefox）
    - headless: 是否无头模式
    - implicit_wait: 隐式等待时间
    - page_load_timeout: 页面加载超时时间
    """
    browser_config = settings.get("browser", {})
    browser_type = browser_config.get("type", "chrome")
    headless = browser_config.get("headless", False)

    # 根据浏览器类型初始化 WebDriver
    if browser_type == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        _driver = webdriver.Chrome(options=options)
    elif browser_type == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        _driver = webdriver.Firefox(options=options)
    else:
        raise ValueError(f"不支持的浏览器类型: {browser_type}")

    # 设置等待时间
    implicit_wait = browser_config.get("implicit_wait", 10)
    page_load_timeout = browser_config.get("page_load_timeout", 30)
    _driver.implicitly_wait(implicit_wait)
    _driver.set_page_load_timeout(page_load_timeout)

    logger.info(f"浏览器已启动: {browser_type}, headless={headless}")

    yield _driver

    # 测试结束后关闭浏览器
    _driver.quit()
    logger.info("浏览器已关闭")


@pytest.fixture(scope="function")
def base_url():
    """
    提供基础 URL fixture，方便测试用例获取当前环境的 base_url
    """
    return settings.base_url


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试失败时自动截图钩子

    当测试用例在 call 阶段（实际执行阶段）失败时：
    1. 自动保存浏览器截图到 ui_automation/evidence/ 目录
    2. 记录错误日志
    """
    outcome = yield
    report = outcome.get_result()

    # 仅在测试执行阶段（call）失败时截图
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver:
            # 确保证据目录存在
            evidence_dir = os.path.join(ROOT_DIR, "ui_automation", "evidence")
            os.makedirs(evidence_dir, exist_ok=True)

            # 生成截图文件名：FAIL_测试名_时间戳.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"FAIL_{item.name}_{timestamp}.png"
            screenshot_path = os.path.join(evidence_dir, screenshot_name)

            try:
                driver.save_screenshot(screenshot_path)
                logger.error(f"测试失败，截图已保存: {screenshot_path}")
                
                # Allure 报告附件 - 失败截图
                try:
                    import allure
                    allure.attach.file(
                        screenshot_path,
                        name=screenshot_name,
                        attachment_type=allure.attachment_type.PNG
                    )
                except ImportError:
                    pass  # 未安装 allure 时跳过
            except Exception as e:
                logger.error(f"测试失败截图保存异常: {e}")


def pytest_configure(config):
    """
    pytest 配置钩子 - 注册自定义 marker

    注册测试相关的 marker，避免 pytest 警告。
    """
    config.addinivalue_line("markers", "ui: UI 自动化测试用例")
    config.addinivalue_line("markers", "smoke: 冒烟测试用例")
    config.addinivalue_line("markers", "regression: 回归测试用例")
    config.addinivalue_line("markers", "api: 接口测试用例")
    config.addinivalue_line("markers", "functional: 功能测试用例")
    config.addinivalue_line("markers", "sanity: 基本健全性测试用例")


@pytest.fixture(scope="session")
def env_config():
    """
    会话级 fixture - 提供当前环境的完整配置
    可在任何测试中使用以获取环境信息
    """
    return settings.to_dict() if hasattr(settings, 'to_dict') else settings._config
