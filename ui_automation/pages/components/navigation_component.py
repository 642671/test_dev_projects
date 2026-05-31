"""
导航组件 - 侧边栏或顶部导航菜单
支持多级菜单导航
"""
from selenium.webdriver.common.by import By
from ui_automation.pages.components.base_component import BaseComponent
from common.logger import get_logger

logger = get_logger("NavigationComponent")


class NavigationComponent(BaseComponent):
    """导航菜单组件"""
    
    # 导航相关定位器
    NAV_CONTAINER = (By.CSS_SELECTOR, "nav, .sidebar, .side-menu")
    MENU_ITEMS = (By.CSS_SELECTOR, "nav a, .menu-item, .nav-link")
    ACTIVE_MENU_ITEM = (By.CSS_SELECTOR, ".active, .menu-item.active, .nav-link.active")
    SUB_MENU = (By.CSS_SELECTOR, ".sub-menu, .dropdown-menu")
    MENU_TOGGLE = (By.CSS_SELECTOR, ".menu-toggle, .hamburger")
    BREADCRUMB = (By.CSS_SELECTOR, ".breadcrumb")
    
    def __init__(self, driver):
        super().__init__(driver, root_locator=(By.CSS_SELECTOR, "nav, .sidebar"))
    
    def navigate_to(self, menu_text):
        """通过菜单文本导航"""
        logger.info(f"导航到: {menu_text}")
        locator = (By.XPATH, f"//nav//a[contains(text(), '{menu_text}')]")
        self.click(locator)
    
    def navigate_to_submenu(self, parent_text, child_text):
        """导航到子菜单"""
        logger.info(f"导航到子菜单: {parent_text} → {child_text}")
        parent_locator = (By.XPATH, f"//nav//a[contains(text(), '{parent_text}')]")
        self.click(parent_locator)
        child_locator = (By.XPATH, f"//nav//a[contains(text(), '{child_text}')]")
        self.click(child_locator)
    
    def get_active_menu(self):
        """获取当前激活的菜单项文本"""
        return self.get_text(self.ACTIVE_MENU_ITEM)
    
    def get_all_menu_items(self):
        """获取所有菜单项文本"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        elements = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(self.MENU_ITEMS)
        )
        return [el.text for el in elements if el.text.strip()]
    
    def is_menu_item_active(self, menu_text):
        """判断指定菜单项是否为激活状态"""
        active_text = self.get_active_menu()
        return menu_text in active_text
    
    def toggle_sidebar(self):
        """切换侧边栏展开/收起"""
        if self.is_element_visible(self.MENU_TOGGLE, timeout=3):
            self.click(self.MENU_TOGGLE)
            logger.info("切换侧边栏状态")
