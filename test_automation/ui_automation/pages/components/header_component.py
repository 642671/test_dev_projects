"""
页头组件 - 网站顶部导航区域
通常包含 Logo、用户信息、退出登录等
多个页面共享此组件
"""
from selenium.webdriver.common.by import By
from ui_automation.pages.components.base_component import BaseComponent
from common.logger import get_logger

logger = get_logger("HeaderComponent")


class HeaderComponent(BaseComponent):
    """页头组件"""
    
    # 组件内元素定位器
    LOGO = (By.CSS_SELECTOR, "header .logo, .navbar-brand")
    USER_DROPDOWN = (By.CSS_SELECTOR, ".user-dropdown, .user-menu")
    USER_NAME_DISPLAY = (By.CSS_SELECTOR, ".user-name, .username-display")
    LOGOUT_BUTTON = (By.CSS_SELECTOR, "a[href*='logout'], .logout-btn, #logout")
    NOTIFICATION_ICON = (By.CSS_SELECTOR, ".notification-icon, .bell-icon")
    NOTIFICATION_COUNT = (By.CSS_SELECTOR, ".notification-count, .badge-count")
    SEARCH_INPUT = (By.CSS_SELECTOR, "header input[type='search'], .global-search")
    
    def __init__(self, driver):
        super().__init__(driver, root_locator=(By.TAG_NAME, "header"))
    
    def get_current_username(self):
        """获取当前登录用户名"""
        return self.get_text(self.USER_NAME_DISPLAY)
    
    def logout(self):
        """退出登录"""
        logger.info("执行退出登录操作")
        # 先点击用户下拉菜单
        if self.is_element_visible(self.USER_DROPDOWN, timeout=3):
            self.click(self.USER_DROPDOWN)
        self.click(self.LOGOUT_BUTTON)
    
    def get_notification_count(self):
        """获取通知数量"""
        if self.is_element_visible(self.NOTIFICATION_COUNT, timeout=3):
            text = self.get_text(self.NOTIFICATION_COUNT)
            return int(text) if text.isdigit() else 0
        return 0
    
    def click_logo(self):
        """点击 Logo 回到首页"""
        self.click(self.LOGO)
    
    def global_search(self, keyword):
        """全局搜索"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(self.SEARCH_INPUT)
        )
        element.clear()
        element.send_keys(keyword)
        element.submit()
        logger.info(f"全局搜索: {keyword}")
    
    def is_logged_in(self):
        """判断是否已登录（通过用户名显示判断）"""
        return self.is_element_visible(self.USER_NAME_DISPLAY, timeout=3)
