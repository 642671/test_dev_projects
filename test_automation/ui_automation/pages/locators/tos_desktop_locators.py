"""
TOS 桌面页面定位器
包含桌面区域和右键菜单相关定位
"""
from selenium.webdriver.common.by import By


class TosDesktopLocators:
    """TOS 桌面定位器"""

    # ========== 桌面区域 ==========
    # 桌面图标容器（右键目标区域）
    DESKTOP_ICONS_AREA = (By.CSS_SELECTOR, "div.desktop_icons")
    
    # ========== 右键菜单 ==========
    # 右键菜单容器
    CONTEXT_MENU = (By.CSS_SELECTOR, "div.contextmenu")
    CONTEXT_MENU_LIST = (By.CSS_SELECTOR, "ul.context-menu-list")
    
    # 菜单项（通用）
    MENU_ITEMS = (By.CSS_SELECTOR, "ul.context-menu-list li.context-menu-item")
    
    # 具体菜单项（通过 span.name 文字定位）
    MENU_REFRESH = (By.XPATH, "//ul[contains(@class,'context-menu-list')]//li[contains(@class,'context-menu-item')]//span[@class='name' and text()='刷新']")
    MENU_USER_SETTINGS = (By.XPATH, "//ul[contains(@class,'context-menu-list')]//li[contains(@class,'context-menu-item')]//span[@class='name' and text()='用户设置']")
    MENU_CREATE_URL = (By.XPATH, "//ul[contains(@class,'context-menu-list')]//li[contains(@class,'context-menu-item')]//span[@class='name' and contains(text(),'URL')]")
    
    # ========== 用户设置界面 ==========
    # 用户设置窗口（打开后的判断）
    USER_SETTINGS_WINDOW = (By.XPATH, "//*[contains(text(),'用户设置') or contains(text(),'账号')]")
