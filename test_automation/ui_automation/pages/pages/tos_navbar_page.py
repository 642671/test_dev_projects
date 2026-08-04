"""
TOS 桌面顶部导航栏页面对象
封装导航栏的所有操作：悬浮查看名称、点击打开应用
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.tos_navbar_locators import TosNavbarLocators
from common.logger import get_logger

logger = get_logger("TosNavbarPage")


class TosNavbarPage(BasePage):
    """
    TOS 桌面顶部导航栏页面对象

    导航栏是顶部的 pin 条，包含固定和可拖拽的应用图标。
    悬浮图标会显示 tooltip（应用名），点击图标打开对应应用。
    """

    def __init__(self, driver):
        super().__init__(driver)

    # ========== 导航栏基础操作 ==========

    def get_navbar_items_count(self):
        """获取导航栏图标总数"""
        items = self.driver.find_elements(*TosNavbarLocators.ALL_APP_ITEMS)
        visible_items = [item for item in items if item.is_displayed()]
        count = len(visible_items)
        logger.info(f"导航栏图标数量: {count}")
        return count

    def hover_app_icon(self, locator):
        """
        悬浮在指定应用图标上，触发 tooltip 显示

        :param locator: 应用图标的定位器（img 元素）
        :return: tooltip 文字
        """
        element = self.find_element(locator, timeout=10)
        # 需要悬浮在 img 的父级 app-item 上才能触发 tooltip
        app_item = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'app-item')]")
        ActionChains(self.driver).move_to_element(app_item).perform()
        # 等待 tooltip 出现
        self.wait_for_element_visible(TosNavbarLocators.TOOLTIP, timeout=3)

        # 获取 tooltip 文字
        tooltip_text = self._get_tooltip_text()
        logger.info(f"悬浮图标，tooltip 显示: '{tooltip_text}'")
        return tooltip_text

    def click_app_by_locator(self, locator, app_name=""):
        """
        通过定位器点击导航栏中的应用

        :param locator: 应用图标的定位器
        :param app_name: 应用名称（用于日志）
        """
        logger.info(f"点击导航栏应用: {app_name}")
        element = self.find_element(locator, timeout=10)
        # 点击 img 的父级 app-item
        app_item = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'app-item')]")
        self.driver.execute_script("arguments[0].click();", app_item)
        # 等待应用窗口加载（等待桌面区域出现变化）
        self.wait_for_element_visible(TosNavbarLocators.DESKTOP_AREA, timeout=10)
        return self

    def click_app_by_name(self, app_name):
        """
        通过悬浮遍历找到指定名称的应用并点击打开

        流程：遍历导航栏每个图标 → 悬浮触发 tooltip → 读取名称 → 匹配后双击打开
        :param app_name: 应用名称（如 "存储管理"、"终端"）
        :return: True 找到并点击成功，False 未找到
        """
        logger.info(f"通过名称查找并点击应用: {app_name}")
        items = self.driver.find_elements(*TosNavbarLocators.ALL_APP_ITEMS)

        for item in items:
            if not item.is_displayed():
                continue
            # 悬浮在图标上，等待 tooltip 显示
            ActionChains(self.driver).move_to_element(item).perform()
            # 等待 tooltip 出现
            try:
                self.wait_for_element_visible(TosNavbarLocators.TOOLTIP, timeout=2)
            except Exception:
                pass  # tooltip 可能未显示，继续
            
            tooltip = self._get_tooltip_text()
            logger.debug(f"  悬浮图标，tooltip='{tooltip}'")
            
            if tooltip and (tooltip == app_name or app_name in tooltip):
                logger.info(f"找到应用 '{app_name}'（tooltip='{tooltip}'），执行单击打开")
                # TOS 导航栏单击打开应用，双击是隐藏应用
                ActionChains(self.driver).click(item).perform()
                # 等待应用窗口加载
                self.wait_for_element_visible(TosNavbarLocators.DESKTOP_AREA, timeout=10)
                return True
        
        logger.warning(f"未找到应用: {app_name}")
        return False

    # ========== 具体应用快捷操作 ==========

    def click_start(self):
        """点击开始按钮"""
        self.click_app_by_locator(TosNavbarLocators.START_BUTTON, "开始")
        return self

    def click_all_apps(self):
        """点击所有应用"""
        self.click_app_by_locator(TosNavbarLocators.ALL_APPS, "所有应用")
        return self

    def click_file_manager(self):
        """点击文件管理"""
        self.click_app_by_locator(TosNavbarLocators.FILE_MANAGER, "文件管理")
        return self

    def click_control_panel(self):
        """点击控制面板"""
        self.click_app_by_locator(TosNavbarLocators.CONTROL_PANEL, "控制面板")
        return self

    def click_storage_manager(self):
        """点击存储管理"""
        self.click_app_by_locator(TosNavbarLocators.STORAGE_MANAGER, "存储管理")
        return self

    def click_terminal(self):
        """点击终端"""
        self.click_app_by_locator(TosNavbarLocators.TERMINAL, "终端")
        return self

    def click_security_advisor(self):
        """点击安全顾问"""
        self.click_app_by_locator(TosNavbarLocators.SECURITY_ADVISOR, "安全顾问")
        return self

    def click_backup(self):
        """点击备份"""
        self.click_app_by_locator(TosNavbarLocators.BACKUP, "备份")
        return self

    def click_app_store(self):
        """点击应用商店"""
        self.click_app_by_locator(TosNavbarLocators.APP_STORE, "应用商店")
        return self

    def click_docker(self):
        """点击 Docker Manager"""
        self.click_app_by_locator(TosNavbarLocators.DOCKER, "Docker Manager")
        return self

    def click_tech_support(self):
        """点击支持与帮助"""
        self.click_app_by_locator(TosNavbarLocators.TECH_SUPPORT, "支持与帮助")
        return self

    def click_jellyfin(self):
        """点击影视"""
        self.click_app_by_locator(TosNavbarLocators.JELLYFIN, "影视")
        return self

    def click_openclaw(self):
        """点击 OpenClaw"""
        self.click_app_by_locator(TosNavbarLocators.OPENCLAW, "OpenClaw")
        return self

    # ========== 验证方法 ==========

    def is_navbar_visible(self):
        """判断导航栏是否可见"""
        return self.is_element_visible(TosNavbarLocators.NAVBAR_CONTAINER, timeout=10)

    def is_app_in_navbar(self, locator):
        """
        判断指定应用是否在导航栏中

        :param locator: 应用图标的定位器
        :return: bool
        """
        try:
            element = self.driver.find_elements(*locator)
            return len(element) > 0 and element[0].is_displayed()
        except Exception:
            return False

    def is_app_window_opened(self, timeout=10):
        """
        判断是否有应用窗口被打开
        TOS 的微应用窗口通常会有特定容器，检测新窗口出现
        """
        try:
            # TOS 应用窗口通常有这些特征 class
            window_selectors = [
                "div.window-container",
                "div.app-window",
                "div.tos-window",
                "div.el-dialog",
                "div[class*='window']",
                "div[class*='panel']"
            ]
            for selector in window_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        logger.info(f"检测到应用窗口: {selector}")
                        return True
            return False
        except Exception:
            return False

    def get_tooltip_for_app(self, locator):
        """获取指定应用图标的 tooltip 文字"""
        return self.hover_app_icon(locator)

    # ========== 内部方法 ==========

    def _get_tooltip_text(self):
        """获取当前显示的 tooltip 文字"""
        try:
            tooltips = self.driver.find_elements(*TosNavbarLocators.TOOLTIP_POPPER)
            for tt in tooltips:
                if tt.is_displayed() and tt.text.strip():
                    return tt.text.strip()
        except Exception:
            pass
        return ""
