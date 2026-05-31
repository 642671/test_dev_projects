"""
业务页面对象模块
使用新的 Locator 分离 + Component 组合模式
"""
from ui_automation.pages.pages.login_page import LoginPage
from ui_automation.pages.pages.dashboard_page import DashboardPage

__all__ = [
    "LoginPage",
    "DashboardPage",
]
