"""通用定位器 - 跨页面共享的元素"""
from selenium.webdriver.common.by import By

class CommonLocators:
    """通用/全局定位器"""
    # 全局加载动画
    LOADING_SPINNER = (By.CSS_SELECTOR, ".loading-spinner")
    # 全局提示消息
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".alert-success, .message-success")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".alert-danger, .message-error, .error-message")
    WARNING_MESSAGE = (By.CSS_SELECTOR, ".alert-warning, .message-warning")
    # Toast 通知
    TOAST_NOTIFICATION = (By.CSS_SELECTOR, ".toast, .notification")
    # 模态框
    MODAL_DIALOG = (By.CSS_SELECTOR, ".modal.show, .modal-dialog")
    MODAL_CLOSE_BUTTON = (By.CSS_SELECTOR, ".modal .close, .modal .btn-close")
    MODAL_CONFIRM_BUTTON = (By.CSS_SELECTOR, ".modal .btn-primary, .modal .btn-confirm")
