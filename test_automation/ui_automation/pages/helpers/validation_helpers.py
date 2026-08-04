"""
验证辅助方法
提供常用的 UI 断言和验证功能
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.logger import get_logger

logger = get_logger("ValidationHelpers")


class ValidationHelpers:
    """验证辅助类"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def assert_text_in_element(self, locator, expected_text, timeout=10):
        """断言元素包含指定文本"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        actual_text = element.text
        assert expected_text in actual_text, \
            f"文本断言失败: 期望包含 '{expected_text}', 实际为 '{actual_text}'"
        logger.info(f"文本验证通过: '{expected_text}' in '{actual_text}'")
    
    def assert_element_text_equals(self, locator, expected_text, timeout=10):
        """断言元素文本完全等于指定文本"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        actual_text = element.text.strip()
        assert actual_text == expected_text, \
            f"文本断言失败: 期望 '{expected_text}', 实际 '{actual_text}'"
        logger.info(f"文本精确匹配验证通过: '{expected_text}'")
    
    def assert_element_visible(self, locator, timeout=10, message=""):
        """断言元素可见"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            logger.info(f"元素可见性验证通过: {locator}")
        except TimeoutException:
            raise AssertionError(message or f"元素不可见: {locator}")
    
    def assert_element_not_visible(self, locator, timeout=5, message=""):
        """断言元素不可见"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
            logger.info(f"元素不可见验证通过: {locator}")
        except TimeoutException:
            raise AssertionError(message or f"元素仍然可见: {locator}")
    
    def assert_url_contains(self, url_part, timeout=10):
        """断言当前 URL 包含指定内容"""
        try:
            WebDriverWait(self.driver, timeout).until(EC.url_contains(url_part))
            logger.info(f"URL 验证通过: 包含 '{url_part}'")
        except TimeoutException:
            actual_url = self.driver.current_url
            raise AssertionError(f"URL 断言失败: 期望包含 '{url_part}', 实际 URL: '{actual_url}'")
    
    def assert_title_contains(self, title_part, timeout=10):
        """断言页面标题包含指定内容"""
        try:
            WebDriverWait(self.driver, timeout).until(EC.title_contains(title_part))
            logger.info(f"标题验证通过: 包含 '{title_part}'")
        except TimeoutException:
            actual_title = self.driver.title
            raise AssertionError(f"标题断言失败: 期望包含 '{title_part}', 实际标题: '{actual_title}'")
    
    def assert_element_attribute(self, locator, attribute, expected_value, timeout=10):
        """断言元素属性值"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        actual_value = element.get_attribute(attribute)
        assert actual_value == expected_value, \
            f"属性断言失败: {attribute} 期望 '{expected_value}', 实际 '{actual_value}'"
        logger.info(f"属性验证通过: {attribute}='{expected_value}'")
    
    def assert_element_css_property(self, locator, css_property, expected_value, timeout=10):
        """断言元素 CSS 属性值"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        actual_value = element.value_of_css_property(css_property)
        assert actual_value == expected_value, \
            f"CSS 属性断言失败: {css_property} 期望 '{expected_value}', 实际 '{actual_value}'"
    
    def assert_element_count(self, locator, expected_count, timeout=10):
        """断言元素数量"""
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        elements = self.driver.find_elements(*locator)
        actual_count = len(elements)
        assert actual_count == expected_count, \
            f"元素数量断言失败: 期望 {expected_count}, 实际 {actual_count}"
        logger.info(f"元素数量验证通过: {actual_count} 个")
    
    def assert_element_enabled(self, locator, timeout=10):
        """断言元素可操作（enabled）"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        assert element.is_enabled(), f"元素不可操作: {locator}"
    
    def assert_element_disabled(self, locator, timeout=10):
        """断言元素不可操作（disabled）"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        assert not element.is_enabled(), f"元素不应可操作但当前可操作: {locator}"
    
    def assert_checkbox_checked(self, locator, timeout=10):
        """断言复选框被选中"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        assert element.is_selected(), f"复选框未被选中: {locator}"
    
    def get_validation_error_messages(self, error_locator, timeout=5):
        """获取所有表单验证错误信息"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(error_locator)
            )
            elements = self.driver.find_elements(*error_locator)
            return [el.text for el in elements if el.text.strip()]
        except TimeoutException:
            return []
