"""
示例页面对象 - 登录页面（LoginPage）
演示如何继承 BasePage 创建具体的页面对象。
"""
from selenium.webdriver.common.by import By
from ui_automation.pages.base_page import BasePage
from common.logger import get_logger

logger = get_logger("LoginPage")


class LoginPage(BasePage):
    """
    登录页面 Page Object

    封装登录页面的元素定位和操作方法。
    使用时请根据实际项目页面修改定位器。
    """

    # ========== 页面元素定位器 ==========
    # 用户名输入框
    USERNAME_INPUT = (By.ID, "username")
    # 密码输入框
    PASSWORD_INPUT = (By.ID, "password")
    # 登录按钮
    LOGIN_BUTTON = (By.ID, "login-btn")
    # 记住我复选框
    REMEMBER_ME_CHECKBOX = (By.ID, "remember-me")
    # 错误提示信息
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message")
    # 成功提示信息
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".success-message")
    # 忘记密码链接
    FORGOT_PASSWORD_LINK = (By.LINK_TEXT, "忘记密码")
    # 页面标题
    PAGE_TITLE = (By.CSS_SELECTOR, "h1.login-title")

    def __init__(self, driver, base_url=None):
        """
        初始化登录页面

        Args:
            driver: WebDriver 实例
            base_url: 登录页面的基础 URL（可选）
        """
        super().__init__(driver)
        self.base_url = base_url or ""
        self.login_url = f"{self.base_url}/login"

    # ========== 页面操作方法 ==========

    def open_login_page(self):
        """打开登录页面"""
        logger.info(f"打开登录页面: {self.login_url}")
        self.open(self.login_url)
        return self

    def input_username(self, username):
        """
        输入用户名

        Args:
            username: 用户名
        """
        logger.info(f"输入用户名: {username}")
        self.input_text(self.USERNAME_INPUT, username)
        return self

    def input_password(self, password):
        """
        输入密码

        Args:
            password: 密码
        """
        logger.info("输入密码: ******")
        self.input_text(self.PASSWORD_INPUT, password)
        return self

    def click_login(self):
        """点击登录按钮"""
        logger.info("点击登录按钮")
        self.click(self.LOGIN_BUTTON)
        return self

    def check_remember_me(self):
        """勾选'记住我'复选框"""
        logger.info("勾选'记住我'")
        self.click(self.REMEMBER_ME_CHECKBOX)
        return self

    def login(self, username, password, remember_me=False):
        """
        执行完整登录操作

        Args:
            username: 用户名
            password: 密码
            remember_me: 是否勾选'记住我'

        Returns:
            self: 返回自身，支持链式调用
        """
        logger.info(f"执行登录操作: 用户名={username}")
        self.input_username(username)
        self.input_password(password)
        if remember_me:
            self.check_remember_me()
        self.click_login()
        return self

    def get_error_message(self):
        """
        获取错误提示信息

        Returns:
            str: 错误信息文本，若不存在返回空字符串
        """
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=3):
            msg = self.get_text(self.ERROR_MESSAGE)
            logger.info(f"错误提示: {msg}")
            return msg
        return ""

    def get_success_message(self):
        """
        获取成功提示信息

        Returns:
            str: 成功信息文本，若不存在返回空字符串
        """
        if self.is_element_visible(self.SUCCESS_MESSAGE, timeout=3):
            msg = self.get_text(self.SUCCESS_MESSAGE)
            logger.info(f"成功提示: {msg}")
            return msg
        return ""

    def click_forgot_password(self):
        """点击'忘记密码'链接"""
        logger.info("点击'忘记密码'链接")
        self.click(self.FORGOT_PASSWORD_LINK)
        return self

    def is_login_page_displayed(self):
        """
        判断登录页面是否已展示

        Returns:
            bool: 登录页面可见返回 True
        """
        return self.is_element_visible(self.USERNAME_INPUT, timeout=5)

    def get_page_title_text(self):
        """
        获取登录页面标题文字

        Returns:
            str: 页面标题文本
        """
        return self.get_text(self.PAGE_TITLE)
