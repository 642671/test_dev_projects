"""
TOS 桌面顶部导航栏（Pin 条）定位器

导航栏结构：
- 容器: div.container-list
- 每个图标: div.app-item（首个"开始"无 .draggable，其余有）
- 内部: div.item-box → div.el-tooltip.item → img
- 名称: 悬浮后显示 el-tooltip__popper
"""
from selenium.webdriver.common.by import By


class TosNavbarLocators:
    """TOS 桌面顶部导航栏定位器"""

    # ========== 容器 ==========
    NAVBAR_CONTAINER = (By.CSS_SELECTOR, "div.container-list")

    # ========== 所有图标 ==========
    ALL_APP_ITEMS = (By.CSS_SELECTOR, "div.container-list .app-item")

    # ========== 通过 img src 定位具体应用 ==========
    # 使用 img[src*='关键词'] 来精确定位，不受顺序影响

    # 开始（固定，不可拖拽）
    START_BUTTON = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='TNAS_logo']")

    # 所有应用
    ALL_APPS = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='all_app']")

    # 文件管理
    FILE_MANAGER = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='folder']")

    # 控制面板
    CONTROL_PANEL = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='Control_panel']")

    # 存储管理
    STORAGE_MANAGER = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='Storage']")

    # 终端
    TERMINAL = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='Terminal']")

    # 安全顾问
    SECURITY_ADVISOR = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='Safety_Guidance']")

    # 备份
    BACKUP = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='Backup']")

    # 应用商店
    APP_STORE = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='app_store']")

    # Docker Manager
    DOCKER = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='docker']")

    # 支持与帮助
    TECH_SUPPORT = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='tech_support']")

    # 影视
    JELLYFIN = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='jellyfin']")

    # OpenClaw
    OPENCLAW = (By.CSS_SELECTOR, "div.container-list .app-item img[src*='openclaw']")

    # ========== Tooltip ==========
    TOOLTIP_POPPER = (By.CSS_SELECTOR, "div.el-tooltip__popper")
    TOOLTIP = TOOLTIP_POPPER  # 别名

    # ========== 桌面区域 ==========
    DESKTOP_AREA = (By.CSS_SELECTOR, "div.desktop_icons")

