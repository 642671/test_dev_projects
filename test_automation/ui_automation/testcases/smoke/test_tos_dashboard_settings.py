"""
TOS 系统看板卡片设置冒烟测试

测试场景：
1. 全部勾选初始化 + 设置面板验证
2. 取消后重新全部勾选恢复默认顺序

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

logger = get_logger("TestTosDashboardSettings")

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')

# 设置面板中应有的 8 个模块（按默认顺序）
EXPECTED_MODULES = ['设备信息', '系统信息', '资源', '网络', '接口', '磁盘', '存储', '硬件']


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.medium
class TestTosDashboardSettings:
    """TOS 系统看板卡片设置冒烟测试"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """前置条件：登录 TOS 并打开系统看板"""
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
        # 打开系统看板
        self.dashboard.open_dashboard()
        assert self.dashboard.is_dashboard_visible(), "前置条件失败：看板未打开"

        yield
        self.dashboard.take_screenshot("dashboard_settings_test_end")

    def test_check_all_and_verify_settings(self, driver, base_url):
        """
        Given: 已登录并打开系统看板
        When: 打开设置面板 → 勾选所有模块 → 关闭设置
        Then: 设置面板包含8个模块,看板显示所有模块卡片
        
        用例编号: TC_DASHBOARD_SETTINGS_001
        风险等级: P2 (次要功能)
        """
        # 打开设置并全部勾选
        self.dashboard.open_settings()
        options = self.dashboard.get_settings_options()

        # 验证设置面板包含所有模块
        option_names = [opt['name'] for opt in options]
        for module in EXPECTED_MODULES:
            assert module in option_names, f"设置面板应包含模块'{module}'，实际: {option_names}"

        # 全部勾选
        self.dashboard.check_all_modules()
        self.dashboard.close_settings()
        time.sleep(2)

        # 验证所有卡片存在（使用 get_all_card_names 不依赖视口，因为全勾选时需滚动才能看全）
        all_cards = self.dashboard.get_all_card_names()
        for module in EXPECTED_MODULES:
            assert module in all_cards, f"全部勾选后'{module}'卡片应存在，实际: {all_cards}"

        self.dashboard.take_screenshot("all_checked_initial")
        logger.info(f"TC_DASHBOARD_SETTINGS_001 通过：全部勾选，卡片: {all_cards}")

    def test_recheck_restores_default_order(self, driver, base_url):
        """
        用例：取消后重新全部勾选恢复默认顺序

        用例编号: TC_DASHBOARD_SETTINGS_002
        模块: 系统看板-设置
        操作步骤:
            1. 打开设置，取消所有模块
            2. 关闭设置
            3. 重新打开设置，全部勾选
            4. 关闭设置，检查卡片顺序
        预期结果: 卡片按默认模块名顺序排列
        """
        # 取消所有
        self.dashboard.open_settings()
        self.dashboard.uncheck_all_modules()
        self.dashboard.close_settings()
        time.sleep(2)

        # 重新全部勾选
        self.dashboard.open_settings()
        self.dashboard.check_all_modules()
        self.dashboard.close_settings()
        time.sleep(2)

        # 获取当前卡片顺序（使用 get_all_card_names 包含滚动区域）
        card_names = self.dashboard.get_all_card_names()

        # 验证所有模块都在
        for module in EXPECTED_MODULES:
            assert module in card_names, f"'{module}'应在看板中，实际: {card_names}"

        # 验证顺序（前面的模块索引应小于后面的）
        for i in range(len(EXPECTED_MODULES) - 1):
            if EXPECTED_MODULES[i] in card_names and EXPECTED_MODULES[i+1] in card_names:
                idx_a = card_names.index(EXPECTED_MODULES[i])
                idx_b = card_names.index(EXPECTED_MODULES[i+1])
                assert idx_a < idx_b, \
                    f"'{EXPECTED_MODULES[i]}'应在'{EXPECTED_MODULES[i+1]}'之前，实际顺序: {card_names}"

        self.dashboard.take_screenshot("after_recheck_all_order")
        logger.info(f"TC_DASHBOARD_SETTINGS_002 通过：重新勾选后恢复默认顺序: {card_names}")
