"""仪表盘页面定位器"""
from selenium.webdriver.common.by import By

class DashboardPageLocators:
    """仪表盘页面定位器"""
    WELCOME_TEXT = (By.CSS_SELECTOR, ".welcome-text, .dashboard-title")
    USER_AVATAR = (By.CSS_SELECTOR, ".user-avatar, .avatar")
    NOTIFICATION_BADGE = (By.CSS_SELECTOR, ".notification-badge, .badge")
    QUICK_ACTIONS = (By.CSS_SELECTOR, ".quick-actions")
    STATISTICS_CARDS = (By.CSS_SELECTOR, ".stat-card, .statistics-item")
