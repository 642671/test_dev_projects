"""
TOS 登录页面对象
封装两步式登录流程的所有操作
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.tos_login_locators import TosLoginLocators
from common.logger import get_logger

logger = get_logger("TosLoginPage")


class TosLoginPage(BasePage):
    """
    TOS 登录页面对象

    两步式登录流程：
    1. 输入用户名 → 点击下一步
    2. 输入密码 → 可选勾选保持登录 → 点击下一步
    """

    def __init__(self, driver):
        super().__init__(driver)

    def open_login_page(self, base_url):
        """打开 TOS 登录页面"""
        logger.info(f"打开 TOS 登录页面: {base_url}")
        self.open(base_url)
        # TOS 是 SPA，等待页面 JS 渲染完成（等待用户名输入框出现）
        self.wait_for_element_visible(TosLoginLocators.USERNAME_INPUT, timeout=15)
        return self

    # ========== 第一步操作 ==========

    def input_username(self, username):
        """输入用户名"""
        logger.info(f"输入用户名: {username}")
        self.wait_for_element_visible(TosLoginLocators.USERNAME_INPUT, timeout=15)
        self.input_text(TosLoginLocators.USERNAME_INPUT, username)
        return self

    def click_next_step1(self):
        """点击第一步的下一步按钮（<i>图标元素，使用JS点击更可靠）"""
        logger.info("点击下一步（第一步）")
        element = self.find_element(TosLoginLocators.NEXT_BUTTON_STEP1, timeout=10)
        # TOS的"下一步"是<i>图标，普通click可能无效，使用JS点击
        self.driver.execute_script("arguments[0].click();", element)
        # 等待第二步页面加载（密码输入框变为可见）
        self.wait_for_element_visible(TosLoginLocators.PASSWORD_INPUT, timeout=10)
        return self

    # ========== 第二步操作 ==========

    def input_password(self, password):
        """输入密码"""
        logger.info("输入密码")
        self.wait_for_element_visible(TosLoginLocators.PASSWORD_INPUT, timeout=10)
        self.input_text(TosLoginLocators.PASSWORD_INPUT, password)
        return self

    def check_keep_login(self):
        """勾选保持登录"""
        logger.info("勾选保持登录")
        checkbox = self.find_element(TosLoginLocators.KEEP_LOGIN_CHECKBOX, timeout=5)
        if not checkbox.is_selected():
            checkbox.click()
        return self

    def uncheck_keep_login(self):
        """取消勾选保持登录"""
        logger.info("取消勾选保持登录")
        checkbox = self.find_element(TosLoginLocators.KEEP_LOGIN_CHECKBOX, timeout=5)
        if checkbox.is_selected():
            checkbox.click()
        return self

    def click_next_step2(self):
        """点击第二步的下一步/登录按钮（<i>图标元素）"""
        logger.info("点击下一步（第二步/登录）")
        element = self.find_element(TosLoginLocators.NEXT_BUTTON_STEP2, timeout=10)
        # 使用JS点击
        self.driver.execute_script("arguments[0].click();", element)
        # 等待登录完成和桌面加载（通过URL变化判断）
        self.wait_for_url_contains("desktop", timeout=20)
        return self

    # ========== 组合操作 ==========

    def login(self, username, password, keep_login=False):
        """
        完整登录操作

        :param username: 用户名
        :param password: 密码
        :param keep_login: 是否勾选保持登录
        """
        logger.info(f"执行登录: 用户={username}, 保持登录={keep_login}")

        # 第一步：输入用户名
        self.input_username(username)
        self.click_next_step1()

        # 第二步：输入密码
        self.input_password(password)

        # 勾选/取消保持登录
        if keep_login:
            self.check_keep_login()
        else:
            self.uncheck_keep_login()

        # 点击登录
        self.click_next_step2()
        return self

    # ========== 验证方法 ==========

    def is_login_successful(self, timeout=20):
        """
        判断是否登录成功
        主要通过 URL 变化来判断（登录成功后 URL 包含 'desktop'）
        """
        logger.info("验证登录是否成功...")
        
        # 方法一：URL 包含 'desktop'（最可靠）
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            WebDriverWait(self.driver, timeout).until(
                lambda d: TosLoginLocators.DESKTOP_URL_KEYWORD in d.current_url
            )
            logger.info(f"登录成功：URL 已变为 {self.driver.current_url}")
            return True
        except Exception:
            pass
        
        # 方法二：页面标题变为 TNAS
        try:
            if self.driver.title == TosLoginLocators.DESKTOP_TITLE:
                logger.info("登录成功：页面标题为 TNAS")
                return True
        except Exception:
            pass
        
        logger.warning(f"登录验证失败：当前 URL={self.driver.current_url}, Title={self.driver.title}")
        return False

    def is_on_login_page(self):
        """判断当前是否在登录页面"""
        return self.is_element_visible(TosLoginLocators.USERNAME_INPUT, timeout=5) or \
               self.is_element_visible(TosLoginLocators.PASSWORD_INPUT, timeout=3)

    def get_welcome_text(self):
        """获取欢迎文字内容"""
        try:
            return self.get_text(TosLoginLocators.WELCOME_TEXT, timeout=10)
        except Exception:
            return ""
