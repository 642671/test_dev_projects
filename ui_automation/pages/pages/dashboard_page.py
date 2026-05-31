"""
仪表盘页面 Page Object
组合 HeaderComponent + NavigationComponent
实现仪表盘业务操作
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.dashboard_page_locators import DashboardPageLocators
from ui_automation.pages.locators.common_locators import CommonLocators
from ui_automation.pages.components.header_component import HeaderComponent
from ui_automation.pages.components.navigation_component import NavigationComponent
from common.logger import get_logger

logger = get_logger("DashboardPage")


class DashboardPage(BasePage):
    """
    仪表盘页面 Page Object
    
    特点：
    - 组合了 HeaderComponent 和 NavigationComponent
    - 定位器集中在 DashboardPageLocators
    - 集成 BasePage 中的 helpers 工具
    """
    
    def __init__(self, driver, base_url=None):
        """
        初始化仪表盘页面
        
        Args:
            driver: WebDriver 实例
            base_url: 基础 URL
        """
        super().__init__(driver)
        self.base_url = base_url or ""
        self.dashboard_url = f"{self.base_url}/dashboard"
        # 组合组件
        self.header = HeaderComponent(driver)
        self.navigation = NavigationComponent(driver)
    
    # ========== 页面导航 ==========
    
    def open_dashboard(self):
        """打开仪表盘页面"""
        logger.info(f"打开仪表盘: {self.dashboard_url}")
        self.open(self.dashboard_url)
        self.waits.wait_for_page_load()
        self.waits.wait_for_loading_complete(CommonLocators.LOADING_SPINNER)
        return self
    
    # ========== 页面信息 ==========
    
    def get_welcome_text(self):
        """获取欢迎文本"""
        text = self.get_text(DashboardPageLocators.WELCOME_TEXT)
        logger.info(f"欢迎文本: {text}")
        return text
    
    def get_statistics_count(self):
        """获取统计卡片数量"""
        elements = self.find_elements(DashboardPageLocators.STATISTICS_CARDS)
        count = len(elements)
        logger.info(f"统计卡片数量: {count}")
        return count
    
    def is_quick_actions_visible(self):
        """判断快捷操作区域是否可见"""
        return self.is_element_visible(DashboardPageLocators.QUICK_ACTIONS)
    
    # ========== 通过组件操作 ==========
    
    def get_current_user(self):
        """通过页头组件获取当前用户名"""
        return self.header.get_current_username()
    
    def logout(self):
        """通过页头组件退出登录"""
        self.header.logout()
        self.waits.wait_for_url_contains("/login")
        logger.info("已退出登录")
    
    def navigate_to_menu(self, menu_text):
        """通过导航组件导航到指定菜单"""
        self.navigation.navigate_to(menu_text)
        self.waits.wait_for_loading_complete(CommonLocators.LOADING_SPINNER)
    
    def navigate_to_submenu(self, parent_text, child_text):
        """通过导航组件导航到子菜单"""
        self.navigation.navigate_to_submenu(parent_text, child_text)
        self.waits.wait_for_loading_complete(CommonLocators.LOADING_SPINNER)
    
    def get_notification_count(self):
        """通过页头组件获取通知数量"""
        return self.header.get_notification_count()
    
    def global_search(self, keyword):
        """通过页头组件执行全局搜索"""
        self.header.global_search(keyword)
        self.waits.wait_for_loading_complete(CommonLocators.LOADING_SPINNER)
    
    # ========== 页面状态验证 ==========
    
    def is_dashboard_loaded(self):
        """判断仪表盘是否已加载"""
        return (
            self.is_element_visible(DashboardPageLocators.WELCOME_TEXT, timeout=5)
            and self.header.is_logged_in()
        )
    
    def assert_dashboard_loaded(self):
        """断言仪表盘已加载"""
        self.validator.assert_element_visible(
            DashboardPageLocators.WELCOME_TEXT,
            message="仪表盘未加载：欢迎文本不可见"
        )
        self.validator.assert_url_contains("/dashboard")
        logger.info("仪表盘页面加载验证通过")
    
    def assert_user_logged_in(self, expected_username=None):
        """断言用户已登录"""
        assert self.header.is_logged_in(), "用户未登录：页头用户名不可见"
        if expected_username:
            actual = self.header.get_current_username()
            assert expected_username in actual, \
                f"用户名不匹配: 期望 '{expected_username}', 实际 '{actual}'"
        logger.info("用户登录状态验证通过")
