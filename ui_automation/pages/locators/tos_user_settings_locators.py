"""
TOS 用户设置页面定位器
入口：桌面右键 → 用户设置
"""
from selenium.webdriver.common.by import By


class TosUserSettingsLocators:
    """TOS 用户设置页面定位器"""

    # ========== 左侧模块导航 ==========
    # 导航项容器
    NAV_ITEMS = (By.CSS_SELECTOR, "li.tab-list")
    
    # 具体导航项（通过文字定位）
    NAV_ACCOUNT = (By.XPATH, "//li[contains(@class,'tab-list')]//span[@class='tab-list-title' and text()='账号']")
    NAV_DISPLAY = (By.XPATH, "//li[contains(@class,'tab-list')]//span[@class='tab-list-title' and text()='显示']")

    # ========== 账号模块 - Tab 标签 ==========
    TAB_ITEMS = (By.CSS_SELECTOR, "div.tab-slider-item")
    
    TAB_USER_INFO = (By.XPATH, "//div[@class='tab-slider-item' and text()='用户信息']")
    TAB_ACCOUNT_SECURITY = (By.XPATH, "//div[@class='tab-slider-item' and text()='账号安全']")
    TAB_OTHER = (By.XPATH, "//div[@class='tab-slider-item' and text()='其它']")

    # ========== 用户信息字段标签 ==========
    # 这些是字段标签文字，用于验证页面加载完整
    FIELD_USERNAME = (By.XPATH, "//*[contains(text(),'test')]")
    FIELD_ROLE = (By.XPATH, "//*[contains(text(),'超级用户')]")
    
    # ========== 窗口标识 ==========
    # 用于判断用户设置窗口是否打开
    SETTINGS_WINDOW_TITLE = (By.XPATH, "//*[contains(text(),'用户设置')]")
