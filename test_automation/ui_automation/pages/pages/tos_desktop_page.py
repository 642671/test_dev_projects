"""
TOS 桌面页面对象
封装桌面右键菜单等操作
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.tos_desktop_locators import TosDesktopLocators
from common.logger import get_logger

logger = get_logger("TosDesktopPage")


class TosDesktopPage(BasePage):
    """
    TOS 桌面页面对象
    封装桌面右键菜单操作
    """

    def __init__(self, driver):
        super().__init__(driver)

    # ========== 右键菜单操作 ==========

    def right_click_desktop(self):
        """在桌面空白区域右键，弹出右键菜单"""
        logger.info("在桌面空白区域执行右键操作")
        desktop = self.find_element(TosDesktopLocators.DESKTOP_ICONS_AREA, timeout=10)
        ActionChains(self.driver).context_click(desktop).perform()
        # 等待右键菜单出现
        self.wait_for_element_visible(TosDesktopLocators.CONTEXT_MENU_LIST, timeout=5)
        return self

    def is_context_menu_visible(self):
        """判断右键菜单是否显示"""
        return self.is_element_visible(TosDesktopLocators.CONTEXT_MENU_LIST, timeout=5)

    def click_menu_item(self, menu_name):
        """
        点击右键菜单中的指定项
        :param menu_name: 菜单项名称（如 "刷新"、"用户设置"）
        """
        logger.info(f"点击右键菜单项: {menu_name}")
        # 通过 span.name 文字定位菜单项
        locator = (By.XPATH, f"//ul[contains(@class,'context-menu-list')]//li[contains(@class,'context-menu-item')]//span[@class='name' and text()='{menu_name}']")
        menu_item = self.find_element(locator, timeout=5)
        # 点击菜单项的父级 li 元素
        li_element = menu_item.find_element(By.XPATH, "./ancestor::li[contains(@class,'context-menu-item')]")
        li_element.click()
        # 等待菜单关闭和桌面恢复
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: not d.find_element(*TosDesktopLocators.CONTEXT_MENU_LIST).is_displayed()
            )
        except (TimeoutException, Exception):
            pass  # 菜单已关闭或超时
        return self

    def click_refresh(self):
        """右键菜单 → 刷新"""
        self.right_click_desktop()
        self.click_menu_item("刷新")
        logger.info("已执行桌面刷新")
        return self

    def click_user_settings(self):
        """右键菜单 → 用户设置"""
        self.right_click_desktop()
        self.click_menu_item("用户设置")
        logger.info("已点击用户设置")
        return self

    # ========== 验证方法 ==========

    def is_desktop_loaded(self):
        """判断桌面是否已加载"""
        return self.is_element_visible(TosDesktopLocators.DESKTOP_ICONS_AREA, timeout=10)

    def is_user_settings_opened(self):
        """判断用户设置界面是否打开"""
        # 用户设置窗口打开后会显示"账号"、"显示"等文字
        try:
            self.wait_for_element_visible(TosDesktopLocators.USER_SETTINGS_WINDOW, timeout=10)
            return True
        except Exception:
            return False

    def get_context_menu_items(self):
        """获取右键菜单所有菜单项的文字"""
        items = self.driver.find_elements(*TosDesktopLocators.MENU_ITEMS)
        texts = []
        for item in items:
            if item.is_displayed():
                name_span = item.find_elements(By.CSS_SELECTOR, "span.name")
                if name_span:
                    texts.append(name_span[0].text)
        logger.info(f"右键菜单项: {texts}")
        return texts
