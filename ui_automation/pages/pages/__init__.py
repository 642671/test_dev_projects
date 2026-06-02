"""
业务页面对象模块
使用新的 Locator 分离 + Component 组合模式
"""
from ui_automation.pages.pages.tos_login_page import TosLoginPage
from ui_automation.pages.pages.tos_navbar_page import TosNavbarPage
from ui_automation.pages.pages.tos_desktop_page import TosDesktopPage

__all__ = [
    "TosLoginPage",
    "TosNavbarPage",
    "TosDesktopPage",
]
