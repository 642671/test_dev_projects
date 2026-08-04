"""
pytest 全局配置（根目录 conftest）
- 测试钩子函数（失败自动截图）
- marker 注册
- 注意：不包含 driver fixture，各模块自行管理
"""
import pytest
import os
from datetime import datetime

# 项目根目录
ROOT_DIR = os.path.dirname(__file__)
import sys
sys.path.insert(0, ROOT_DIR)

from common.logger import get_logger

logger = get_logger("conftest")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试失败时自动截图钩子
    当测试用例在 call 阶段失败时：
    1. 自动保存截图到对应模块的 reports/screenshots/ 目录
    2. 记录错误日志
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver:
            test_file_dir = os.path.dirname(item.fspath.strpath)
            module_dir = test_file_dir
            while module_dir and not os.path.exists(os.path.join(module_dir, "reports")):
                parent = os.path.dirname(module_dir)
                if parent == module_dir:
                    break
                module_dir = parent

            if os.path.exists(os.path.join(module_dir, "reports")):
                evidence_dir = os.path.join(module_dir, "reports", "screenshots")
            else:
                evidence_dir = os.path.join(ROOT_DIR, "ui_automation", "reports", "screenshots")

            os.makedirs(evidence_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"FAIL_{item.name}_{timestamp}.png"
            screenshot_path = os.path.join(evidence_dir, screenshot_name)

            try:
                driver.save_screenshot(screenshot_path)
                logger.error(f"测试失败，截图已保存: {screenshot_path}")
                try:
                    import allure
                    allure.attach.file(
                        screenshot_path,
                        name=screenshot_name,
                        attachment_type=allure.attachment_type.PNG
                    )
                except ImportError:
                    pass
            except Exception as e:
                logger.error(f"截图保存异常: {e}")


def pytest_configure(config):
    """pytest 配置钩子 - 注册自定义 marker"""
    config.addinivalue_line("markers", "ui: UI 自动化测试用例")
    config.addinivalue_line("markers", "smoke: 冒烟测试用例")
    config.addinivalue_line("markers", "regression: 回归测试用例")
    config.addinivalue_line("markers", "api: 接口测试")
    config.addinivalue_line("markers", "functional: 功能测试用例")
    config.addinivalue_line("markers", "sanity: 基本健全性测试用例")
    config.addinivalue_line("markers", "slow: 执行较慢的测试")
    config.addinivalue_line("markers", "wip: 正在开发中的测试")
