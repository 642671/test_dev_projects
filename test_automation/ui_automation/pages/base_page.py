"""
Page Object 基类
封装 Selenium WebDriver 常用操作，所有页面对象继承此类。
提供核心元素操作方法，并集成 Helpers 辅助工具。

辅助方法已拆分至 helpers/ 模块：
- WaitHelpers: 自定义等待（AJAX、页面加载、元素消失等）
- ActionHelpers: 高级交互（拖拽、双击、键盘快捷键等）
- ValidationHelpers: UI 断言验证

通过 self.waits / self.actions_helper / self.validator 属性访问
"""
import os
import time
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 导入项目日志模块
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.logger import get_logger

# 导入辅助工具
from ui_automation.pages.helpers.wait_helpers import WaitHelpers
from ui_automation.pages.helpers.action_helpers import ActionHelpers
from ui_automation.pages.helpers.validation_helpers import ValidationHelpers

logger = get_logger("BasePage")


class BasePage:
    """页面对象基类，封装 WebDriver 核心操作并集成辅助工具"""

    # 证据保存目录
    EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence")

    def __init__(self, driver):
        """
        初始化 BasePage

        Args:
            driver: Selenium WebDriver 实例
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        # 确保证据目录存在
        os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        # 集成辅助工具
        self.waits = WaitHelpers(driver)
        self.actions_helper = ActionHelpers(driver)
        self.validator = ValidationHelpers(driver)

    # ========== 元素操作 ==========

    def find_element(self, locator, timeout=10):
        """
        查找单个元素，带显式等待

        Args:
            locator: 元素定位器，格式为 (By.XXX, "value")
            timeout: 超时时间（秒）

        Returns:
            WebElement: 找到的元素

        Raises:
            TimeoutException: 超时未找到元素
        """
        logger.debug(f"查找元素: {locator}, 超时: {timeout}s")
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            logger.debug(f"元素已找到: {locator}")
            return element
        except TimeoutException:
            logger.error(f"查找元素超时: {locator}")
            self.take_screenshot("find_element_timeout")
            raise

    def find_elements(self, locator, timeout=10):
        """
        查找多个元素

        Args:
            locator: 元素定位器，格式为 (By.XXX, "value")
            timeout: 超时时间（秒）

        Returns:
            list[WebElement]: 找到的元素列表，未找到返回空列表
        """
        logger.debug(f"查找多个元素: {locator}, 超时: {timeout}s")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            elements = self.driver.find_elements(*locator)
            logger.debug(f"找到 {len(elements)} 个元素: {locator}")
            return elements
        except TimeoutException:
            logger.warning(f"未找到任何元素: {locator}")
            return []

    def click(self, locator, timeout=10):
        """
        点击元素

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）
        """
        logger.info(f"点击元素: {locator}")
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            element.click()
            logger.info(f"元素点击成功: {locator}")
        except TimeoutException:
            logger.error(f"等待元素可点击超时: {locator}")
            self.take_screenshot("click_timeout")
            raise
        except Exception as e:
            logger.error(f"点击元素异常: {locator}, 错误: {e}")
            self.take_screenshot("click_error")
            raise

    def input_text(self, locator, text, clear_first=True, timeout=10):
        """
        输入文本

        Args:
            locator: 元素定位器
            text: 要输入的文本
            clear_first: 输入前是否先清空（默认 True）
            timeout: 超时时间（秒）
        """
        logger.info(f"输入文本到元素: {locator}, 内容: '{text}'")
        try:
            element = self.find_element(locator, timeout)
            if clear_first:
                element.clear()
                logger.debug("已清空输入框")
            element.send_keys(text)
            logger.info(f"文本输入成功: '{text}'")
        except Exception as e:
            logger.error(f"输入文本异常: {locator}, 错误: {e}")
            self.take_screenshot("input_text_error")
            raise

    def get_text(self, locator, timeout=10):
        """
        获取元素文本

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）

        Returns:
            str: 元素的文本内容
        """
        logger.debug(f"获取元素文本: {locator}")
        try:
            element = self.find_element(locator, timeout)
            text = element.text
            logger.debug(f"元素文本为: '{text}'")
            return text
        except Exception as e:
            logger.error(f"获取元素文本异常: {locator}, 错误: {e}")
            self.take_screenshot("get_text_error")
            raise

    def get_attribute(self, locator, attr_name, timeout=10):
        """
        获取元素属性值

        Args:
            locator: 元素定位器
            attr_name: 属性名称
            timeout: 超时时间（秒）

        Returns:
            str: 属性值
        """
        logger.debug(f"获取元素属性: {locator}, 属性名: '{attr_name}'")
        try:
            element = self.find_element(locator, timeout)
            value = element.get_attribute(attr_name)
            logger.debug(f"属性值为: '{value}'")
            return value
        except Exception as e:
            logger.error(f"获取元素属性异常: {locator}, 错误: {e}")
            self.take_screenshot("get_attribute_error")
            raise

    def is_element_visible(self, locator, timeout=5):
        """
        判断元素是否可见

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）

        Returns:
            bool: 元素可见返回 True，否则返回 False
        """
        logger.debug(f"判断元素是否可见: {locator}")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            logger.debug(f"元素可见: {locator}")
            return True
        except TimeoutException:
            logger.debug(f"元素不可见: {locator}")
            return False

    # ========== 等待操作 ==========

    def wait_for_element_visible(self, locator, timeout=10):
        """
        等待元素可见

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）

        Returns:
            WebElement: 可见的元素
        """
        logger.debug(f"等待元素可见: {locator}, 超时: {timeout}s")
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            logger.debug(f"元素已可见: {locator}")
            return element
        except TimeoutException:
            logger.error(f"等待元素可见超时: {locator}")
            self.take_screenshot("wait_visible_timeout")
            raise

    def wait_for_element_clickable(self, locator, timeout=10):
        """
        等待元素可点击

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）

        Returns:
            WebElement: 可点击的元素
        """
        logger.debug(f"等待元素可点击: {locator}, 超时: {timeout}s")
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            logger.debug(f"元素已可点击: {locator}")
            return element
        except TimeoutException:
            logger.error(f"等待元素可点击超时: {locator}")
            self.take_screenshot("wait_clickable_timeout")
            raise

    def wait_for_url_contains(self, url_part, timeout=10):
        """
        等待 URL 包含指定内容

        Args:
            url_part: URL 中应包含的字符串
            timeout: 超时时间（秒）

        Returns:
            bool: URL 包含指定内容返回 True
        """
        logger.debug(f"等待 URL 包含: '{url_part}', 超时: {timeout}s")
        try:
            result = WebDriverWait(self.driver, timeout).until(
                EC.url_contains(url_part)
            )
            logger.debug(f"URL 已包含: '{url_part}'")
            return result
        except TimeoutException:
            logger.error(f"等待 URL 包含 '{url_part}' 超时，当前 URL: {self.driver.current_url}")
            self.take_screenshot("wait_url_timeout")
            raise

    # ========== 页面操作 ==========

    def open(self, url):
        """
        打开页面

        Args:
            url: 要打开的页面 URL
        """
        logger.info(f"打开页面: {url}")
        try:
            self.driver.get(url)
            logger.info(f"页面已打开: {url}")
        except Exception as e:
            logger.error(f"打开页面失败: {url}, 错误: {e}")
            self.take_screenshot("open_page_error")
            raise

    def get_title(self):
        """
        获取页面标题

        Returns:
            str: 页面标题
        """
        title = self.driver.title
        logger.debug(f"页面标题: '{title}'")
        return title

    def get_current_url(self):
        """
        获取当前 URL

        Returns:
            str: 当前页面 URL
        """
        url = self.driver.current_url
        logger.debug(f"当前 URL: '{url}'")
        return url

    def refresh(self):
        """刷新页面"""
        logger.info("刷新页面")
        self.driver.refresh()
        logger.info("页面已刷新")

    def switch_to_frame(self, frame_locator):
        """
        切换到 iframe

        Args:
            frame_locator: iframe 定位器（可以是元素定位器元组、索引或名称）
        """
        logger.info(f"切换到 iframe: {frame_locator}")
        try:
            if isinstance(frame_locator, tuple):
                # 如果是定位器元组，先找到元素再切换
                frame_element = self.find_element(frame_locator)
                self.driver.switch_to.frame(frame_element)
            else:
                # 直接用索引或名称切换
                self.driver.switch_to.frame(frame_locator)
            logger.info("已切换到 iframe")
        except Exception as e:
            logger.error(f"切换 iframe 失败: {frame_locator}, 错误: {e}")
            self.take_screenshot("switch_frame_error")
            raise

    def switch_to_default(self):
        """切回默认内容（退出所有 iframe）"""
        logger.info("切回默认内容")
        self.driver.switch_to.default_content()
        logger.info("已切回默认内容")

    # ========== 截图与证据 ==========

    def take_screenshot(self, name=None):
        """
        截图保存到 evidence 目录

        Args:
            name: 截图文件名前缀（不含扩展名），默认使用时间戳

        Returns:
            str: 截图文件的完整路径
        """
        os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        if name:
            filename = f"{name}_{timestamp}.png"
        else:
            filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.EVIDENCE_DIR, filename)
        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"截图已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"截图保存失败: {e}")
            return ""

    def save_page_source(self, name=None):
        """
        保存页面源码到 evidence 目录

        Args:
            name: 文件名前缀（不含扩展名），默认使用时间戳

        Returns:
            str: 页面源码文件的完整路径
        """
        os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        if name:
            filename = f"{name}_{timestamp}.html"
        else:
            filename = f"page_source_{timestamp}.html"
        filepath = os.path.join(self.EVIDENCE_DIR, filename)
        try:
            page_source = self.driver.page_source
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(page_source)
            logger.info(f"页面源码已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存页面源码失败: {e}")
            return ""

    # ========== 高级操作 ==========

    def hover(self, locator, timeout=10):
        """
        鼠标悬停到元素上

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）
        """
        logger.info(f"鼠标悬停: {locator}")
        try:
            element = self.find_element(locator, timeout)
            ActionChains(self.driver).move_to_element(element).perform()
            logger.info(f"鼠标悬停成功: {locator}")
        except Exception as e:
            logger.error(f"鼠标悬停失败: {locator}, 错误: {e}")
            self.take_screenshot("hover_error")
            raise

    def scroll_to_element(self, locator, timeout=10):
        """
        滚动页面到元素位置

        Args:
            locator: 元素定位器
            timeout: 超时时间（秒）
        """
        logger.info(f"滚动到元素: {locator}")
        try:
            element = self.find_element(locator, timeout)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            logger.info(f"已滚动到元素: {locator}")
        except Exception as e:
            logger.error(f"滚动到元素失败: {locator}, 错误: {e}")
            self.take_screenshot("scroll_error")
            raise

    def execute_script(self, script, *args):
        """
        执行 JavaScript 脚本

        Args:
            script: JavaScript 代码字符串
            *args: 传递给脚本的参数

        Returns:
            脚本执行的返回值
        """
        logger.debug(f"执行 JavaScript: {script[:80]}...")
        try:
            result = self.driver.execute_script(script, *args)
            logger.debug(f"JavaScript 执行完成，返回值: {result}")
            return result
        except Exception as e:
            logger.error(f"JavaScript 执行失败: {e}")
            self.take_screenshot("js_error")
            raise

    def select_dropdown(self, locator, text=None, value=None, index=None):
        """
        下拉框选择（支持 <select> 标签）

        Args:
            locator: 下拉框元素定位器
            text: 按可见文本选择
            value: 按 value 属性选择
            index: 按索引选择

        注意: text、value、index 三选一，优先级 text > value > index
        """
        logger.info(f"下拉框选择: {locator}, text={text}, value={value}, index={index}")
        try:
            element = self.find_element(locator)
            select = Select(element)
            if text is not None:
                select.select_by_visible_text(text)
                logger.info(f"按文本选择: '{text}'")
            elif value is not None:
                select.select_by_value(value)
                logger.info(f"按 value 选择: '{value}'")
            elif index is not None:
                select.select_by_index(index)
                logger.info(f"按索引选择: {index}")
            else:
                logger.warning("未指定选择方式（text/value/index）")
        except Exception as e:
            logger.error(f"下拉框选择失败: {locator}, 错误: {e}")
            self.take_screenshot("select_dropdown_error")
            raise
