"""登录页面定位器"""
from selenium.webdriver.common.by import By

class LoginPageLocators:
    """登录页面所有元素定位器"""
    # 表单元素
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], .login-btn")
    REMEMBER_ME_CHECKBOX = (By.ID, "remember-me")
    # 链接
    FORGOT_PASSWORD_LINK = (By.LINK_TEXT, "忘记密码")
    REGISTER_LINK = (By.LINK_TEXT, "注册")
    # 提示信息
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".login-error, .error-message")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".login-success")
    # 验证码（如果有）
    CAPTCHA_INPUT = (By.ID, "captcha")
    CAPTCHA_IMAGE = (By.CSS_SELECTOR, ".captcha-img")
