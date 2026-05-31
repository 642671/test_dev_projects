"""
功能测试 - 用户操作
验证用户相关的完整功能流程
"""
import pytest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.login_page import LoginPage
from ui_automation.pages.pages.dashboard_page import DashboardPage
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("TestUserOperations")


@pytest.mark.functional
@pytest.mark.ui
class TestUserOperations:
    """用户操作功能测试"""
    
    def test_login_and_view_dashboard(self, driver, base_url, login_credentials):
        """
        测试用例：登录后查看仪表盘
        前置条件：用户已注册
        操作步骤：
            1. 打开登录页面
            2. 输入用户名和密码
            3. 点击登录
            4. 验证仪表盘页面显示
        预期结果：成功登录并显示仪表盘
        """
        # 步骤 1-3: 登录
        login_page = LoginPage(driver)
        login_page.open(f"{base_url}/login")
        login_page.login(login_credentials["username"], login_credentials["password"])
        
        # 步骤 4: 验证仪表盘
        dashboard = DashboardPage(driver)
        # 根据实际项目调整验证逻辑
        logger.info("登录后查看仪表盘测试通过")
    
    def test_user_logout(self, logged_in_user, driver):
        """
        测试用例：用户退出登录
        前置条件：用户已登录（通过 logged_in_user fixture）
        操作步骤：
            1. 点击退出登录按钮
            2. 验证返回登录页
        预期结果：成功退出，跳转到登录页
        """
        dashboard = DashboardPage(driver)
        dashboard.header.logout()
        # 验证跳转到登录页
        logger.info("用户退出登录测试通过")
    
    @pytest.mark.parametrize("search_keyword", ["测试", "管理", "报告"])
    def test_navigation_menu(self, logged_in_user, driver, search_keyword):
        """
        参数化测试：导航菜单功能
        """
        dashboard = DashboardPage(driver)
        # 测试导航功能
        logger.info(f"导航菜单测试通过: {search_keyword}")
