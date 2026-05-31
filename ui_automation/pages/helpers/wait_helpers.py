"""
自定义等待辅助方法
提供比 Selenium 原生更强大的等待功能
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.logger import get_logger

logger = get_logger("WaitHelpers")


class WaitHelpers:
    """自定义等待工具类"""
    
    def __init__(self, driver, default_timeout=10):
        self.driver = driver
        self.default_timeout = default_timeout
    
    def wait_for_element_with_retry(self, locator, retries=3, timeout=None):
        """带重试的元素等待"""
        timeout = timeout or self.default_timeout
        for attempt in range(retries):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
            except TimeoutException:
                if attempt < retries - 1:
                    logger.warning(f"元素查找超时 (第{attempt+1}次)，重试中: {locator}")
                    time.sleep(1)
                else:
                    logger.error(f"元素查找失败，已重试{retries}次: {locator}")
                    raise
    
    def wait_for_ajax(self, timeout=None):
        """等待 AJAX 请求完成"""
        timeout = timeout or self.default_timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "return (typeof jQuery !== 'undefined') ? jQuery.active == 0 : true"
                )
            )
            logger.debug("AJAX 请求已完成")
        except TimeoutException:
            logger.warning("等待 AJAX 完成超时")
    
    def wait_for_page_load(self, timeout=None):
        """等待页面完全加载"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.debug("页面加载完成")
    
    def wait_for_url_change(self, old_url, timeout=None):
        """等待 URL 变化"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.current_url != old_url
        )
        logger.info(f"URL 已变化: {self.driver.current_url}")
    
    def wait_for_url_contains(self, url_part, timeout=None):
        """等待 URL 包含指定内容"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains(url_part)
        )
    
    def wait_for_element_text_change(self, locator, old_text, timeout=None):
        """等待元素文本变化"""
        timeout = timeout or self.default_timeout
        def text_changed(driver):
            try:
                element = driver.find_element(*locator)
                return element.text != old_text
            except (StaleElementReferenceException, Exception):
                return False
        WebDriverWait(self.driver, timeout).until(text_changed)
    
    def wait_for_element_attribute(self, locator, attribute, expected_value, timeout=None):
        """等待元素属性值变为指定值"""
        timeout = timeout or self.default_timeout
        def attr_matches(driver):
            try:
                element = driver.find_element(*locator)
                return element.get_attribute(attribute) == expected_value
            except Exception:
                return False
        WebDriverWait(self.driver, timeout).until(attr_matches)
    
    def wait_for_element_count(self, locator, expected_count, timeout=None):
        """等待元素数量达到指定值"""
        timeout = timeout or self.default_timeout
        def count_matches(driver):
            elements = driver.find_elements(*locator)
            return len(elements) >= expected_count
        WebDriverWait(self.driver, timeout).until(count_matches)
    
    def wait_for_element_disappear(self, locator, timeout=None):
        """等待元素消失"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )
        logger.debug(f"元素已消失: {locator}")
    
    def wait_for_loading_complete(self, loading_locator, timeout=None):
        """等待加载动画消失"""
        timeout = timeout or self.default_timeout
        try:
            # 先等加载出现（短时间）
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(loading_locator)
            )
        except TimeoutException:
            pass  # 加载太快未捕获到，直接返回
        # 等待加载消失
        self.wait_for_element_disappear(loading_locator, timeout)
