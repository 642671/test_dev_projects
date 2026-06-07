"""
TOS 系统看板冒烟测试

测试场景：
1. 打开系统看板 → 钉住 → 拖动验证
2. 钉住后取消钉住 → 点击空白处隐藏

前置条件：已登录 TOS 系统
"""
import pytest
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.tos_login_page import TosLoginPage
from ui_automation.pages.pages.tos_dashboard_page import TosDashboardPage
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("TestTosDashboard")

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')


@pytest.mark.smoke
@pytest.mark.ui
class TestTosDashboard:
    """TOS 系统看板冒烟测试"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """前置条件：登录 TOS"""
        self.login_page = TosLoginPage(driver)
        self.login_page.open_login_page(base_url)
        login_data = load_yaml_data(os.path.join(TESTDATA_DIR, "tos_login_data.yaml"))
        self.login_page.login(
            username=login_data["valid_login"]["username"],
            password=login_data["valid_login"]["password"],
            keep_login=False
        )
        assert self.login_page.is_login_successful(), "前置条件失败：登录未成功"
        time.sleep(3)

        self.dashboard = TosDashboardPage(driver)
        yield
        self.dashboard.take_screenshot("dashboard_test_end")

    def test_pin_drag_unpin_hide_dashboard(self, driver, base_url):
        """
        用例：系统看板钉住拖动后取消钉住并隐藏

        用例编号: TC_DASHBOARD_001
        模块: TOS桌面-系统看板
        前置条件: 已登录
        操作步骤:
            1. 点击右侧栏系统看板图标，打开看板
            2. 点击"钉住"按钮
            3. 验证看板已钉住
            4. 拖动看板到新位置，验证位置变化
            5. 点击"取消钉住"按钮
            6. 点击桌面空白处
            7. 验证看板消失
        预期结果: 钉住后可拖动，取消钉住后点击空白处看板消失
        """
        # 打开系统看板
        self.dashboard.open_dashboard()
        assert self.dashboard.is_dashboard_visible(), "系统看板应成功打开"

        # 钉住看板
        self.dashboard.pin_dashboard()
        assert self.dashboard.is_pinned(), "看板应已钉住（iconPin 应含 fix-on class）"
        self.dashboard.take_screenshot("after_pin")

        # 拖动看板
        before_x, before_y, after_x, after_y = self.dashboard.drag_dashboard(offset_x=-200, offset_y=0)
        assert after_x != before_x, f"拖动后x位置应发生变化，拖动前={before_x}，拖动后={after_x}"
        self.dashboard.take_screenshot("after_drag")
        logger.info(f"钉住后拖动成功，位移dx={after_x - before_x}")

        # 取消钉住
        self.dashboard.unpin_dashboard()
        assert not self.dashboard.is_pinned(), "取消钉住后，按钮应恢复为未钉住状态"
        self.dashboard.take_screenshot("after_unpin")

        # 点击桌面空白处隐藏
        self.dashboard.click_desktop_to_hide()

        # 验证看板消失
        assert not self.dashboard.is_dashboard_visible(), "点击桌面后看板应隐藏"
        self.dashboard.take_screenshot("after_hide")

        logger.info("TC_DASHBOARD_001 通过：钉住→拖动→取消钉住→点击空白→看板消失")
