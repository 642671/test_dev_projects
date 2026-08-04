"""
TOS 系统看板页面对象
封装系统看板的打开、钉住、拖动、取消钉住操作
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.tos_dashboard_locators import TosDashboardLocators
from common.logger import get_logger

logger = get_logger("TosDashboardPage")


class TosDashboardPage(BasePage):
    """TOS 系统看板页面对象"""

    def __init__(self, driver):
        super().__init__(driver)

    # ========== 打开/关闭 ==========

    def open_dashboard(self):
        """点击右侧栏图标打开系统看板"""
        logger.info("点击右侧栏打开系统看板")
        icon = self.find_element(TosDashboardLocators.DASHBOARD_ICON, timeout=10)
        icon.click()
        # 等待看板面板出现
        self.wait_for_element_visible(TosDashboardLocators.DASHBOARD_PANEL, timeout=10)
        return self

    def is_dashboard_visible(self):
        """判断系统看板是否可见"""
        return self.is_element_visible(TosDashboardLocators.DASHBOARD_HEADER, timeout=5)

    # ========== 钉住操作 ==========

    def pin_dashboard(self):
        """钉住系统看板"""
        logger.info("钉住系统看板")
        pin_btn = self.find_element(TosDashboardLocators.PIN_BUTTON, timeout=10)
        ActionChains(self.driver).click(pin_btn).perform()
        # 等待钉住按钮变为 active 状态
        self.wait_for_element_visible(TosDashboardLocators.PIN_BUTTON_ACTIVE, timeout=5)
        return self

    def is_pinned(self):
        """判断看板是否已钉住（检查 fix-on class）"""
        try:
            self.driver.find_element(*TosDashboardLocators.PIN_BUTTON_ACTIVE)
            return True
        except Exception:
            return False

    def unpin_dashboard(self):
        """取消钉住系统看板"""
        logger.info("取消钉住系统看板")
        unpin_btn = self.find_element(TosDashboardLocators.PIN_BUTTON_ACTIVE, timeout=10)
        ActionChains(self.driver).click(unpin_btn).perform()
        # 等待钉住按钮恢复为非 active 状态
        self.wait_for_element_visible(TosDashboardLocators.PIN_BUTTON, timeout=5)
        return self

    # ========== 拖动操作 ==========

    def get_dashboard_position(self):
        """获取看板当前位置"""
        header = self.find_element(TosDashboardLocators.DASHBOARD_HEADER, timeout=10)
        loc = header.location
        logger.info(f"看板当前位置: x={loc['x']}, y={loc['y']}")
        return loc['x'], loc['y']

    def drag_dashboard(self, offset_x, offset_y=0):
        """
        拖动系统看板
        :param offset_x: 水平偏移量（负值=向左）
        :param offset_y: 垂直偏移量（负值=向上）
        :return: (拖动前x, 拖动前y, 拖动后x, 拖动后y)
        """
        logger.info(f"拖动系统看板: offset_x={offset_x}, offset_y={offset_y}")
        header = self.find_element(TosDashboardLocators.DASHBOARD_HEADER, timeout=10)

        before_x, before_y = header.location['x'], header.location['y']
        ActionChains(self.driver).drag_and_drop_by_offset(header, offset_x, offset_y).perform()
        
        # 等待拖动完成（位置发生变化）
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(self.driver, 5).until(
            lambda d: abs(header.location['x'] - before_x) > 5 or abs(header.location['y'] - before_y) > 5
        )
        after_x, after_y = header.location['x'], header.location['y']

        logger.info(f"  拖动前: ({before_x}, {before_y}) → 拖动后: ({after_x}, {after_y})")
        return before_x, before_y, after_x, after_y

    # ========== 隐藏 ==========

    def click_desktop_to_hide(self):
        """点击右侧栏系统看板图标隐藏看板（toggle 行为）"""
        logger.info("再次点击系统看板图标以隐藏看板")
        # 取消钉住后，再次点击右侧栏的系统看板图标即可隐藏（toggle）
        icon = self.find_element(TosDashboardLocators.DASHBOARD_ICON, timeout=10)
        icon.click()
        # 等待看板面板消失
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: not d.find_element(*TosDashboardLocators.DASHBOARD_PANEL).is_displayed()
            )
        except (TimeoutException, Exception):
            pass  # 看板已隐藏或超时，继续执行
        return self

    # ========== 设置面板操作 ==========

    def open_settings(self):
        """打开看板设置面板"""
        logger.info("打开系统看板设置面板")
        setting_icon = self.find_element(TosDashboardLocators.SETTINGS_ICON, timeout=10)
        setting_icon.click()
        # 等待设置面板中的选项出现
        self.wait_for_element_visible(TosDashboardLocators.SETTINGS_OPTIONS, timeout=5)
        return self

    def close_settings(self):
        """关闭设置面板（再次点击设置图标）"""
        logger.info("关闭设置面板")
        setting_icon = self.find_element(TosDashboardLocators.SETTINGS_ICON, timeout=10)
        setting_icon.click()
        # 等待设置面板消失（选项不可见）
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: len(d.find_elements(*TosDashboardLocators.SETTINGS_OPTIONS)) == 0
            )
        except TimeoutException:
            pass  # 面板已关闭或超时，继续执行
        return self

    def get_settings_options(self):
        """获取设置面板中所有模块选项的名称和勾选状态"""
        options = self.driver.find_elements(*TosDashboardLocators.SETTINGS_OPTIONS)
        result = []
        for opt in options:
            if opt.is_displayed():
                name_els = opt.find_elements(By.CSS_SELECTOR, TosDashboardLocators.SETTINGS_OPTION_NAME)
                name = ''
                for n in name_els:
                    if n.text.strip():
                        name = n.text.strip()
                        break
                cb = opt.find_elements(By.CSS_SELECTOR, "input.input_check")
                checked = cb[0].is_selected() if cb else False
                result.append({'name': name, 'checked': checked, 'element': opt})
        logger.info(f"设置面板模块列表: {[(r['name'], r['checked']) for r in result]}")
        return result

    def uncheck_module(self, module_name):
        """取消勾选指定模块"""
        logger.info(f"取消勾选模块: {module_name}")
        options = self.get_settings_options()
        for opt in options:
            if opt['name'] == module_name and opt['checked']:
                cb = opt['element'].find_element(By.CSS_SELECTOR, "input.input_check")
                self.driver.execute_script("arguments[0].click();", cb)
                # 等待复选框变为未勾选状态
                from selenium.webdriver.support.ui import WebDriverWait
                WebDriverWait(self.driver, 3).until(lambda d: not cb.is_selected())
                logger.info(f"  已取消勾选: {module_name}")
                return True
        logger.warning(f"  未找到或已取消勾选: {module_name}")
        return False

    def check_module(self, module_name):
        """勾选指定模块"""
        logger.info(f"勾选模块: {module_name}")
        options = self.get_settings_options()
        for opt in options:
            if opt['name'] == module_name and not opt['checked']:
                cb = opt['element'].find_element(By.CSS_SELECTOR, "input.input_check")
                self.driver.execute_script("arguments[0].click();", cb)
                # 等待复选框变为勾选状态
                from selenium.webdriver.support.ui import WebDriverWait
                WebDriverWait(self.driver, 3).until(lambda d: cb.is_selected())
                logger.info(f"  已勾选: {module_name}")
                return True
        logger.warning(f"  未找到或已勾选: {module_name}")
        return False

    def check_all_modules(self):
        """勾选所有未勾选的模块（确保初始状态一致）"""
        logger.info("勾选所有模块")
        options = self.get_settings_options()
        changed = False
        for opt in options:
            if not opt['checked']:
                cb = opt['element'].find_element(By.CSS_SELECTOR, "input.input_check")
                self.driver.execute_script("arguments[0].click();", cb)
                # 等待复选框变为勾选状态
                from selenium.webdriver.support.ui import WebDriverWait
                WebDriverWait(self.driver, 3).until(lambda d: cb.is_selected())
                logger.info(f"  已勾选: {opt['name']}")
                changed = True
        if not changed:
            logger.info("  所有模块已全部勾选，无需操作")
        return self

    def uncheck_all_modules(self):
        """取消勾选所有已勾选的模块"""
        logger.info("取消勾选所有模块")
        options = self.get_settings_options()
        for opt in options:
            if opt['checked']:
                cb = opt['element'].find_element(By.CSS_SELECTOR, "input.input_check")
                self.driver.execute_script("arguments[0].click();", cb)
                # 等待复选框变为未勾选状态
                from selenium.webdriver.support.ui import WebDriverWait
                WebDriverWait(self.driver, 3).until(lambda d: not cb.is_selected())
                logger.info(f"  已取消勾选: {opt['name']}")
        return self

    # ========== 看板卡片操作 ==========

    def scroll_dashboard(self, direction="down", pixels=300):
        """
        在系统看板面板内滚动
        :param direction: 'down' 向下滚动, 'up' 向上滚动
        :param pixels: 滚动像素量
        """
        scroll_amount = pixels if direction == "down" else -pixels
        # 找到看板的滚动容器
        try:
            scroll_container = self.driver.find_element(*TosDashboardLocators.DASHBOARD_PANEL)
            self.driver.execute_script(
                "arguments[0].scrollTop += arguments[1];", scroll_container, scroll_amount
            )
        except Exception:
            # 如果找不到面板容器，尝试在看板头部位置模拟滚轮
            header = self.driver.find_element(*TosDashboardLocators.DASHBOARD_HEADER)
            ActionChains(self.driver).move_to_element(header).perform()
            self.driver.execute_script(
                f"window.scrollBy(0, {scroll_amount});"
            )
        time.sleep(1)
        logger.info(f"看板内滚动: {direction} {pixels}px")
        return self

    def get_all_card_names(self):
        """
        获取看板中所有卡片名称（包括需要滚动才能看到的）
        通过 DOM 查找所有 custom-name 元素的文字（不依赖 is_displayed）
        """
        cards = self.driver.find_elements(*TosDashboardLocators.CARD_TITLES)
        names = [c.get_attribute('textContent').strip() for c in cards if c.get_attribute('textContent').strip()]
        logger.info(f"看板所有卡片(含滚动区域): {names}")
        return names

    def get_visible_card_names(self):
        """获取看板中当前可见的卡片名称（仅视口内可见的）"""
        cards = self.driver.find_elements(*TosDashboardLocators.CARD_TITLES)
        names = [c.text.strip() for c in cards if c.is_displayed() and c.text.strip()]
        logger.info(f"看板可见卡片: {names}")
        return names

    def is_card_visible(self, card_name):
        """判断指定名称的卡片是否在看板中存在（通过 DOM 检查，不依赖视口可见性）"""
        names = self.get_all_card_names()
        return card_name in names

    def drag_card(self, card_name, offset_x=0, offset_y=-100):
        """
        拖动指定名称的卡片
        使用 click_and_hold + move_by_offset + release 模拟拖动（兼容 Vue 自定义拖动）
        :return: (before_y, after_y) 拖动前后的 y 坐标
        """
        logger.info(f"拖动卡片: {card_name}, offset=({offset_x}, {offset_y})")
        cards = self.driver.find_elements(*TosDashboardLocators.CARD_TITLES)
        target = None
        for card in cards:
            if card.is_displayed() and card.text.strip() == card_name:
                target = card
                break

        if not target:
            logger.warning(f"未找到卡片: {card_name}")
            return None, None

        before_y = target.location['y']

        # 使用 click_and_hold + 缓慢移动 + release 模拟真实拖动
        actions = ActionChains(self.driver)
        actions.click_and_hold(target).pause(1)
        # 分多步移动，模拟真实拖动轨迹
        steps = 5
        step_x = offset_x // steps
        step_y = offset_y // steps
        for _ in range(steps):
            actions.move_by_offset(step_x, step_y).pause(0.1)
        actions.release().perform()
        
        # 等待拖动完成（位置发生变化）
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(self.driver, 5).until(
            lambda d: abs(target.location['y'] - before_y) > 5
        )

        # 重新获取位置
        cards_after = self.driver.find_elements(*TosDashboardLocators.CARD_TITLES)
        after_y = before_y
        for card in cards_after:
            if card.is_displayed() and card.text.strip() == card_name:
                after_y = card.location['y']
                break

        logger.info(f"  拖动前 y={before_y}, 拖动后 y={after_y}")
        return before_y, after_y
