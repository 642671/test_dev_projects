"""
登录页面 Page Object（新结构）
使用 Locator 分离模式，导入 LoginPageLocators
包含 HeaderComponent（如果登录页有公共头部）
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.login_page_locators import LoginPageLocators
from ui_automation.pages.locators.common_locators import CommonLocators
from common.logger import get_logger

logger = get_logger("LoginPage")


class LoginPage(BasePage):
    """
    登录页面 Page Object（新结构版本）
    
    特点：
    - 定位器从 LoginPageLocators 集中管理
    - 集成了 WaitHelpers / ActionHelpers / ValidationHelpers（通过 BasePage）
    - 支持链式调用
    """
    
    def __init__(self, driver, base_url=None):
        """
        初始化登录页面
        
        Args:
            driver: WebDriver 实例
            base_url: 基础 URL
        """
        super().__init__(driver)
        self.base_url = base_url or ""
        self.login_url = f"{self.base_url}/login"
    
    # ========== 页面导航 ==========
    
    def open_login_page(self):
        """打开登录页面"""
        logger.info(f"打开登录页面: {self.login_url}")
        self.open(self.login_url)
        self.waits.wait_for_page_load()
        return self
    
    # ========== 元素操作 ==========
    
    def input_username(self, username):
        """输入用户名"""
        logger.info(f"输入用户名: {username}")
        self.input_text(LoginPageLocators.USERNAME_INPUT, username)
        return self
    
    def input_password(self, password):
        """输入密码"""
        logger.info("输入密码: ******")
        self.input_text(LoginPageLocators.PASSWORD_INPUT, password)
        return self
    
    def click_login(self):
        """点击登录按钮"""
        logger.info("点击登录按钮")
        self.click(LoginPageLocators.LOGIN_BUTTON)
        return self
    
    def check_remember_me(self):
        """勾选'记住我'复选框"""
        logger.info("勾选'记住我'")
        self.click(LoginPageLocators.REMEMBER_ME_CHECKBOX)
        return self
    
    def input_captcha(self, captcha_text):
        """输入验证码"""
        logger.info(f"输入验证码: {captcha_text}")
        self.input_text(LoginPageLocators.CAPTCHA_INPUT, captcha_text)
        return self
    
    # ========== 业务操作 ==========
    
    def login(self, username, password, remember_me=False):
        """
        执行完整登录操作
        
        Args:
            username: 用户名
            password: 密码
            remember_me: 是否勾选'记住我'
        """
        logger.info(f"执行登录操作: 用户名={username}")
        self.input_username(username)
        self.input_password(password)
        if remember_me:
            self.check_remember_me()
        self.click_login()
        # 等待加载完成
        self.waits.wait_for_loading_complete(CommonLocators.LOADING_SPINNER)
        return self
    
    def login_and_wait_redirect(self, username, password, expected_url_part="/dashboard"):
        """登录并等待跳转到指定页面"""
        self.login(username, password)
        self.waits.wait_for_url_contains(expected_url_part)
        logger.info(f"登录成功，已跳转到: {self.get_current_url()}")
        return self
    
    # ========== 信息获取 ==========
    
    def get_error_message(self):
        """获取登录错误信息"""
        if self.is_element_visible(LoginPageLocators.ERROR_MESSAGE, timeout=3):
            msg = self.get_text(LoginPageLocators.ERROR_MESSAGE)
            logger.info(f"登录错误提示: {msg}")
            return msg
        return ""
    
    def get_success_message(self):
        """获取登录成功信息"""
        if self.is_element_visible(LoginPageLocators.SUCCESS_MESSAGE, timeout=3):
            msg = self.get_text(LoginPageLocators.SUCCESS_MESSAGE)
            logger.info(f"登录成功提示: {msg}")
            return msg
        return ""
    
    # ========== 导航链接 ==========
    
    def click_forgot_password(self):
        """点击'忘记密码'链接"""
        logger.info("点击'忘记密码'链接")
        self.click(LoginPageLocators.FORGOT_PASSWORD_LINK)
        return self
    
    def click_register(self):
        """点击'注册'链接"""
        logger.info("点击'注册'链接")
        self.click(LoginPageLocators.REGISTER_LINK)
        return self
    
    # ========== 页面状态验证 ==========
    
    def is_login_page_displayed(self):
        """判断登录页面是否已展示"""
        return self.is_element_visible(LoginPageLocators.USERNAME_INPUT, timeout=5)
    
    def is_captcha_displayed(self):
        """判断验证码是否展示"""
        return self.is_element_visible(LoginPageLocators.CAPTCHA_IMAGE, timeout=3)
    
    def assert_login_error(self, expected_message):
        """断言登录错误信息"""
        self.validator.assert_text_in_element(
            LoginPageLocators.ERROR_MESSAGE, expected_message
        )
    
    def assert_login_page_loaded(self):
        """断言登录页面已加载"""
        self.validator.assert_element_visible(
            LoginPageLocators.USERNAME_INPUT,
            message="登录页面未加载：用户名输入框不可见"
        )
        self.validator.assert_element_visible(
            LoginPageLocators.LOGIN_BUTTON,
            message="登录页面未加载：登录按钮不可见"
        )
