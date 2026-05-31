"""
高级交互辅助方法
提供复杂的用户交互操作封装
"""
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.logger import get_logger

logger = get_logger("ActionHelpers")


class ActionHelpers:
    """高级交互辅助类"""
    
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
    
    def double_click(self, locator, timeout=10):
        """双击元素"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        ActionChains(self.driver).double_click(element).perform()
        logger.info(f"双击元素: {locator}")
    
    def right_click(self, locator, timeout=10):
        """右键点击"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        ActionChains(self.driver).context_click(element).perform()
        logger.info(f"右键点击: {locator}")
    
    def drag_and_drop(self, source_locator, target_locator, timeout=10):
        """拖拽操作"""
        source = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(source_locator)
        )
        target = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(target_locator)
        )
        ActionChains(self.driver).drag_and_drop(source, target).perform()
        logger.info(f"拖拽: {source_locator} → {target_locator}")
    
    def hover_and_click(self, hover_locator, click_locator, timeout=10):
        """悬停后点击（用于下拉菜单等）"""
        hover_element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(hover_locator)
        )
        ActionChains(self.driver).move_to_element(hover_element).perform()
        time.sleep(0.5)  # 等待菜单展开
        click_element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(click_locator)
        )
        click_element.click()
        logger.info(f"悬停 {hover_locator} 后点击 {click_locator}")
    
    def scroll_to_bottom(self):
        """滚动到页面底部"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logger.info("滚动到页面底部")
    
    def scroll_to_top(self):
        """滚动到页面顶部"""
        self.driver.execute_script("window.scrollTo(0, 0);")
        logger.info("滚动到页面顶部")
    
    def scroll_by(self, x=0, y=500):
        """按指定距离滚动"""
        self.driver.execute_script(f"window.scrollBy({x}, {y});")
    
    def press_key(self, key):
        """按下键盘按键"""
        ActionChains(self.driver).send_keys(key).perform()
        logger.info(f"按下按键: {key}")
    
    def press_enter(self):
        """按下回车键"""
        self.press_key(Keys.ENTER)
    
    def press_escape(self):
        """按下 ESC 键"""
        self.press_key(Keys.ESCAPE)
    
    def press_tab(self):
        """按下 Tab 键"""
        self.press_key(Keys.TAB)
    
    def keyboard_shortcut(self, *keys):
        """键盘组合快捷键，如 Ctrl+A"""
        actions = ActionChains(self.driver)
        for key in keys[:-1]:
            actions.key_down(key)
        actions.send_keys(keys[-1])
        for key in keys[:-1]:
            actions.key_up(key)
        actions.perform()
        logger.info(f"键盘快捷键: {keys}")
    
    def select_all_and_delete(self, locator, timeout=10):
        """全选并删除输入框内容"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        ActionChains(self.driver).key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
        ActionChains(self.driver).send_keys(Keys.DELETE).perform()
        logger.info(f"全选并删除: {locator}")
    
    def upload_file(self, file_input_locator, file_path, timeout=10):
        """文件上传（通过 input[type=file]）"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(file_input_locator)
        )
        element.send_keys(file_path)
        logger.info(f"上传文件: {file_path}")

