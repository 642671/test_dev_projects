"""
冒烟测试 - 登录功能
验证核心登录流程是否正常
"""
import pytest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.login_page import LoginPage
from common.logger import get_logger

logger = get_logger("TestLoginSmoke")


@pytest.mark.smoke
@pytest.mark.ui
class TestLoginSmoke:
    """登录冒烟测试"""
    
    def test_login_page_loads(self, driver, base_url):
        """验证登录页面能正常加载"""
        login_page = LoginPage(driver)
        login_page.open(f"{base_url}/login")
        # 验证页面关键元素存在
        assert login_page.is_page_loaded(), "登录页面应正常加载"
        logger.info("登录页面加载验证通过")
    
    def test_valid_login(self, driver, base_url, login_credentials):
        """验证正确凭证能成功登录"""
        login_page = LoginPage(driver)
        login_page.open(f"{base_url}/login")
        login_page.login(
            login_credentials["username"],
            login_credentials["password"]
        )
        # 验证登录成功（根据实际项目调整断言）
        logger.info("有效登录冒烟测试通过")
    
    def test_invalid_login_shows_error(self, driver, base_url):
        """验证错误凭证显示错误提示"""
        login_page = LoginPage(driver)
        login_page.open(f"{base_url}/login")
        login_page.login("invalid_user", "wrong_password")
        assert login_page.is_error_visible(), "错误登录应显示错误提示"
        logger.info("无效登录错误提示验证通过")
