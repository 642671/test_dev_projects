"""
UI 测试用例级 conftest
提供预登录用户、测试数据加载等前置条件 fixtures
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
# 优先加载 ui_automation 模块目录（确保 config.settings 取到模块私有配置）
_MODULE_DIR = os.path.join(os.path.dirname(__file__), '..')
if os.path.abspath(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(_MODULE_DIR))
from config.settings import settings
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("testcases_conftest")

# 测试数据目录
TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "..", "testdata")


@pytest.fixture
def test_data():
    """
    通用测试数据加载 fixture
    返回一个加载函数，测试中按需加载
    """
    def _load(filename, key=None):
        filepath = os.path.join(TESTDATA_DIR, filename)
        return load_yaml_data(filepath, key)
    return _load


@pytest.fixture
def login_credentials():
    """登录凭证数据"""
    return {
        "username": settings.username,
        "password": settings.password
    }


@pytest.fixture
def logged_in_user(driver, base_url, login_credentials):
    """
    前置条件 fixture - 预登录用户
    测试开始前自动完成登录
    
    使用方式：
        def test_something(logged_in_user, driver):
            # driver 已处于登录状态
            ...
    """
    from ui_automation.pages.login_page import LoginPage
    
    login_page = LoginPage(driver)
    login_page.open(f"{base_url}/login")
    login_page.login(
        login_credentials["username"],
        login_credentials["password"]
    )
    logger.info(f"预登录完成: {login_credentials['username']}")
    
    yield driver
    
    # teardown: 可选 - 登出
    logger.info("测试结束，清理登录状态")


@pytest.fixture
def fresh_page(driver, base_url):
    """
    干净的页面 fixture
    确保从首页开始
    """
    driver.get(base_url)
    driver.delete_all_cookies()
    driver.refresh()
    return driver
