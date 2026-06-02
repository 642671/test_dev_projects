"""
TOS 用户设置页面对象
封装用户设置界面的导航、Tab切换、字段验证等操作
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from selenium.webdriver.common.by import By
from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.tos_user_settings_locators import TosUserSettingsLocators
from common.logger import get_logger

logger = get_logger("TosUserSettingsPage")


class TosUserSettingsPage(BasePage):
    """TOS 用户设置页面对象"""

    def __init__(self, driver):
        super().__init__(driver)

    # ========== 界面验证 ==========

    def is_settings_loaded(self, timeout=10):
        """验证用户设置界面是否加载完成"""
        try:
            self.wait_for_element_visible(TosUserSettingsLocators.NAV_ACCOUNT, timeout=timeout)
            return True
        except Exception:
            return False

    def get_nav_modules(self):
        """获取左侧导航模块列表"""
        items = self.driver.find_elements(*TosUserSettingsLocators.NAV_ITEMS)
        modules = []
        for item in items:
            if item.is_displayed():
                title_span = item.find_elements(By.CSS_SELECTOR, "span.tab-list-title")
                if title_span:
                    modules.append(title_span[0].text)
        logger.info(f"用户设置左侧导航模块: {modules}")
        return modules

    def get_tab_items(self):
        """获取当前模块的 Tab 标签列表"""
        items = self.driver.find_elements(*TosUserSettingsLocators.TAB_ITEMS)
        tabs = [item.text for item in items if item.is_displayed() and item.text.strip()]
        logger.info(f"当前模块 Tab 标签: {tabs}")
        return tabs

    # ========== 导航操作 ==========

    def click_nav_account(self):
        """点击左侧导航 - 账号"""
        logger.info("点击左侧导航: 账号")
        self.click(TosUserSettingsLocators.NAV_ACCOUNT)
        time.sleep(2)
        return self

    def click_nav_display(self):
        """点击左侧导航 - 显示"""
        logger.info("点击左侧导航: 显示")
        self.click(TosUserSettingsLocators.NAV_DISPLAY)
        time.sleep(2)
        return self

    # ========== Tab 操作 ==========

    def click_tab_user_info(self):
        """点击 Tab: 用户信息"""
        logger.info("点击 Tab: 用户信息")
        self.click(TosUserSettingsLocators.TAB_USER_INFO)
        time.sleep(1)
        return self

    def click_tab_account_security(self):
        """点击 Tab: 账号安全"""
        logger.info("点击 Tab: 账号安全")
        self.click(TosUserSettingsLocators.TAB_ACCOUNT_SECURITY)
        time.sleep(1)
        return self

    def click_tab_other(self):
        """点击 Tab: 其它"""
        logger.info("点击 Tab: 其它")
        self.click(TosUserSettingsLocators.TAB_OTHER)
        time.sleep(1)
        return self

    # ========== 字段验证 ==========

    def is_username_displayed(self):
        """验证用户名 'test' 是否显示"""
        return self.is_element_visible(TosUserSettingsLocators.FIELD_USERNAME, timeout=5)

    def is_role_displayed(self):
        """验证角色 '超级用户' 是否显示"""
        return self.is_element_visible(TosUserSettingsLocators.FIELD_ROLE, timeout=5)
