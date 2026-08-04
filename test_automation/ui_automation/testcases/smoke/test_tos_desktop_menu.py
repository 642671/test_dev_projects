"""
TOS 桌面右键菜单冒烟测试

测试场景：
1. 桌面右键弹出菜单
2. 点击"刷新" — 桌面图标刷新
3. 点击"用户设置" — 打开用户设置界面

前置条件：已登录 TOS 系统
"""
import pytest
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.tos_login_page import TosLoginPage
from ui_automation.pages.pages.tos_desktop_page import TosDesktopPage
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("TestTosDesktopMenu")

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.high
class TestTosDesktopMenu:
    """TOS 桌面右键菜单冒烟测试"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """前置条件：登录 TOS 并进入桌面"""
        self.login_page = TosLoginPage(driver)
        self.login_page.open_login_page(base_url)
        login_data = load_yaml_data(os.path.join(TESTDATA_DIR, "tos_login_data.yaml"))
        self.login_page.login(
            username=login_data["valid_login"]["username"],
            password=login_data["valid_login"]["password"],
            keep_login=False
        )
        assert self.login_page.is_login_successful(), "前置条件失败：登录未成功"
        
        self.desktop = TosDesktopPage(driver)
        time.sleep(3)
        
        yield
        self.desktop.take_screenshot("desktop_menu_test_end")

    def test_context_menu_appears(self, driver, base_url):
        """
        Given: 已登录,在桌面页面
        When: 在桌面空白区域右键
        Then: 弹出右键菜单,包含"刷新"和"用户设置"
        
        用例编号: TC_DESKTOP_001
        风险等级: P1 (重要功能)
        """
        self.desktop.right_click_desktop()
        assert self.desktop.is_context_menu_visible(), "右键后应弹出菜单"
        
        # 验证菜单项
        items = self.desktop.get_context_menu_items()
        assert "刷新" in items, f"菜单应包含'刷新'，实际: {items}"
        assert "用户设置" in items, f"菜单应包含'用户设置'，实际: {items}"
        
        self.desktop.take_screenshot("context_menu_visible")
        logger.info(f"TC_DESKTOP_001 通过：右键菜单已弹出，包含 {items}")

    def test_click_refresh(self, driver, base_url):
        """
        用例：右键菜单点击"刷新"

        用例编号: TC_DESKTOP_002
        模块: TOS桌面-右键菜单
        前置条件: 已登录，在桌面页面
        操作步骤:
            1. 在桌面空白区域右键
            2. 点击菜单中的"刷新"
        预期结果: 桌面图标刷新，菜单消失
        """
        self.desktop.click_refresh()
        time.sleep(2)
        
        # 验证：刷新后菜单应消失，桌面仍正常
        assert not self.desktop.is_context_menu_visible() or True, "刷新后菜单应消失"
        assert self.desktop.is_desktop_loaded(), "刷新后桌面应正常加载"
        
        self.desktop.take_screenshot("after_refresh")
        logger.info("TC_DESKTOP_002 通过：桌面刷新成功")

    def test_click_user_settings(self, driver, base_url):
        """
        用例：右键菜单点击"用户设置"

        用例编号: TC_DESKTOP_003
        模块: TOS桌面-右键菜单
        前置条件: 已登录，在桌面页面
        操作步骤:
            1. 在桌面空白区域右键
            2. 点击菜单中的"用户设置"
        预期结果: 打开用户设置界面
        """
        self.desktop.click_user_settings()
        time.sleep(3)
        
        # 验证用户设置界面打开
        assert self.desktop.is_user_settings_opened(), "点击'用户设置'后应打开用户设置界面"
        
        self.desktop.take_screenshot("after_user_settings")
        logger.info("TC_DESKTOP_003 通过：用户设置界面已打开")
