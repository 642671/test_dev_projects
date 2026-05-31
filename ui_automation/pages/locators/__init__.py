"""
定位器集中管理模块
将页面元素定位器从 Page Object 中分离，便于维护和复用
"""
from ui_automation.pages.locators.common_locators import CommonLocators
from ui_automation.pages.locators.login_page_locators import LoginPageLocators
from ui_automation.pages.locators.dashboard_page_locators import DashboardPageLocators

__all__ = [
    "CommonLocators",
    "LoginPageLocators",
    "DashboardPageLocators",
]
