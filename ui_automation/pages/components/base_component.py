"""
组件基类
封装可复用的 UI 组件（如页头、导航栏、侧边栏等）
组件是页面的一部分，可以被多个页面共享
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from common.logger import get_logger

logger = get_logger("BaseComponent")


class BaseComponent:
    """
    组件基类
    每个组件代表页面中一个可独立操作的区域
    """
    
    def __init__(self, driver, root_locator=None):
        """
        初始化组件
        :param driver: WebDriver 实例
        :param root_locator: 组件根元素定位器（可选，用于限定组件范围）
        """
        self.driver = driver
        self.root_locator = root_locator
        self.wait = WebDriverWait(driver, 10)
    
    @property
    def root_element(self):
        """获取组件根元素"""
        if self.root_locator:
            return self.wait.until(EC.presence_of_element_located(self.root_locator))
        return self.driver
    
    def find_element(self, locator, timeout=10):
        """在组件范围内查找元素"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            logger.error(f"组件内元素查找超时: {locator}")
            raise
    
    def click(self, locator, timeout=10):
        """点击组件内元素"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        logger.info(f"组件内点击: {locator}")
    
    def get_text(self, locator, timeout=10):
        """获取组件内元素文本"""
        element = self.find_element(locator, timeout)
        return element.text
    
    def is_visible(self, timeout=5):
        """判断组件是否可见"""
        if not self.root_locator:
            return True
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.root_locator)
            )
            return True
        except TimeoutException:
            return False
    
    def is_element_visible(self, locator, timeout=5):
        """判断组件内元素是否可见"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
