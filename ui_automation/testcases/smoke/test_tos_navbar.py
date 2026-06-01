"""
TOS 桌面导航栏冒烟测试

测试场景：点击导航栏中的以下应用并验证打开
1. 开始
2. 所有应用
3. 存储管理
4. 终端
5. 安全顾问

前置条件：已登录 TOS 系统
"""
import pytest
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.tos_login_page import TosLoginPage
from ui_automation.pages.pages.tos_navbar_page import TosNavbarPage
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("TestTosNavbar")

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')


@pytest.mark.smoke
@pytest.mark.ui
class TestTosNavbar:
    """TOS 桌面导航栏冒烟测试"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """前置条件：登录 TOS 并进入桌面"""
        # 登录
        self.login_page = TosLoginPage(driver)
        self.login_page.open_login_page(base_url)
        login_data = load_yaml_data(os.path.join(TESTDATA_DIR, "tos_login_data.yaml"))
        self.login_page.login(
            username=login_data["valid_login"]["username"],
            password=login_data["valid_login"]["password"],
            keep_login=False
        )
        assert self.login_page.is_login_successful(), "前置条件失败：登录未成功"

        # 初始化导航栏页面对象
        self.navbar = TosNavbarPage(driver)
        time.sleep(3)  # 等待桌面完全加载

        yield

        # teardown
        self.navbar.take_screenshot("navbar_test_end")

    def test_navbar_visible(self, driver, base_url):
        """
        用例：验证导航栏可见且包含图标

        用例编号: TC_NAVBAR_001
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤: 检查导航栏容器是否可见
        预期结果: 导航栏可见，图标数量 > 0
        """
        assert self.navbar.is_navbar_visible(), "导航栏应该可见"
        count = self.navbar.get_navbar_items_count()
        assert count > 0, f"导航栏应包含图标，实际数量: {count}"
        logger.info(f"TC_NAVBAR_001 通过：导航栏可见，共 {count} 个图标")

    def test_click_start(self, driver, base_url):
        """
        用例：悬浮识别并点击"开始"

        用例编号: TC_NAVBAR_002
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤:
            1. 遍历导航栏图标，悬浮查看 tooltip
            2. 找到"开始"后点击
        预期结果: 开始菜单打开
        """
        result = self.navbar.click_app_by_name("开始")
        assert result, "未找到导航栏中的'开始'图标"
        time.sleep(2)
        self.navbar.take_screenshot("after_click_start")
        logger.info("TC_NAVBAR_002 通过：悬浮识别并点击开始成功")

    def test_click_all_apps(self, driver, base_url):
        """
        用例：悬浮识别并点击"所有应用"

        用例编号: TC_NAVBAR_003
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤:
            1. 遍历导航栏图标，悬浮查看 tooltip
            2. 找到"所有应用"后点击
        预期结果: 所有应用列表打开
        """
        result = self.navbar.click_app_by_name("所有应用")
        assert result, "未找到导航栏中的'所有应用'图标"
        time.sleep(2)
        self.navbar.take_screenshot("after_click_all_apps")
        logger.info("TC_NAVBAR_003 通过：悬浮识别并点击所有应用成功")

    def test_click_storage_manager(self, driver, base_url):
        """
        用例：悬浮识别并点击"存储管理"

        用例编号: TC_NAVBAR_004
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤:
            1. 遍历导航栏图标，悬浮查看 tooltip
            2. 找到"存储管理"后点击
        预期结果: 存储管理应用窗口打开
        """
        result = self.navbar.click_app_by_name("存储管理")
        assert result, "未找到导航栏中的'存储管理'图标"
        time.sleep(3)
        self.navbar.take_screenshot("after_click_storage_manager")
        logger.info("TC_NAVBAR_004 通过：悬浮识别并点击存储管理成功")

    def test_click_terminal(self, driver, base_url):
        """
        用例：悬浮识别并点击"终端"

        用例编号: TC_NAVBAR_005
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤:
            1. 遍历导航栏图标，悬浮查看 tooltip
            2. 找到"终端"后点击
        预期结果: 终端应用窗口打开
        """
        result = self.navbar.click_app_by_name("终端")
        assert result, "未找到导航栏中的'终端'图标"
        time.sleep(3)
        self.navbar.take_screenshot("after_click_terminal")
        logger.info("TC_NAVBAR_005 通过：悬浮识别并点击终端成功")

    def test_click_security_advisor(self, driver, base_url):
        """
        用例：悬浮识别并点击"安全顾问"

        用例编号: TC_NAVBAR_006
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤:
            1. 遍历导航栏图标，悬浮查看 tooltip
            2. 找到"安全顾问"后点击
        预期结果: 安全顾问应用窗口打开
        """
        result = self.navbar.click_app_by_name("安全顾问")
        assert result, "未找到导航栏中的'安全顾问'图标"
        time.sleep(3)
        self.navbar.take_screenshot("after_click_security_advisor")
        logger.info("TC_NAVBAR_006 通过：悬浮识别并点击安全顾问成功")

    def test_click_control_panel(self, driver, base_url):
        """
        用例：悬浮识别并点击"控制面板"

        用例编号: TC_NAVBAR_007
        模块: TOS桌面-导航栏
        前置条件: 已登录
        操作步骤:
            1. 遍历导航栏图标，悬浮查看 tooltip
            2. 找到"控制面板"后点击
        预期结果: 控制面板应用窗口打开
        """
        result = self.navbar.click_app_by_name("控制面板")
        assert result, "未找到导航栏中的'控制面板'图标"
        time.sleep(3)
        self.navbar.take_screenshot("after_click_control_panel")
        logger.info("TC_NAVBAR_007 通过：悬浮识别并点击控制面板成功")
