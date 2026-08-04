"""
TOS 系统看板（Dashboard）定位器
入口：桌面右侧栏第一个图标
"""
from selenium.webdriver.common.by import By


class TosDashboardLocators:
    """TOS 系统看板定位器"""

    # ========== 入口 ==========
    # 右侧栏系统看板图标
    DASHBOARD_ICON = (By.CSS_SELECTOR, "i.iconfont.icontosboard")

    # ========== 看板面板 ==========
    # 看板容器（打开后可见）
    DASHBOARD_PANEL = (By.CSS_SELECTOR, "div.resource.actived")

    # 看板头部用户信息区域（用于拖动）
    DASHBOARD_HEADER = (By.CSS_SELECTOR, "div.user_name")

    # ========== 钉住/取消钉住 ==========
    # 钉住按钮（未钉住状态）
    PIN_BUTTON = (By.CSS_SELECTOR, "i.iconfont.iconPin")

    # 钉住按钮（已钉住状态，带 fix-on class）
    PIN_BUTTON_ACTIVE = (By.CSS_SELECTOR, "i.iconfont.iconPin.fix-on")

    # 钉住按钮容器（el-tooltip，用于悬浮获取tooltip）
    PIN_CONTAINER = (By.XPATH, "//i[contains(@class,'iconPin')]/ancestor::div[contains(@class,'el-tooltip')]")

    # ========== 桌面空白区域（用于点击隐藏） ==========
    DESKTOP_AREA = (By.CSS_SELECTOR, "div.desktop_icons")

    # ========== 设置面板 ==========
    # 设置图标
    SETTINGS_ICON = (By.CSS_SELECTOR, "i.iconfont.iconrongqi1")

    # 设置面板中的模块选项（所有）
    SETTINGS_OPTIONS = (By.CSS_SELECTOR, ".custom-option.el-checkbox")

    # 设置面板中选项的文字（用于定位特定模块）
    SETTINGS_OPTION_NAME = ".custom-name"  # 相对于选项容器的子选择器

    # ========== 看板卡片 ==========
    # 卡片标题（用于验证模块是否显示）
    CARD_TITLES = (By.CSS_SELECTOR, "div.custom-name")

    # 时间区域（不可拖动的固定区域）
    TIME_AREA = (By.CSS_SELECTOR, "h1.resource-title")  # "您好，test"
