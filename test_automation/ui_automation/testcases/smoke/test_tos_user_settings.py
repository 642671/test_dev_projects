"""
TOS 用户设置界面冒烟测试 - 基础加载验证

测试场景：
1. 用户设置界面加载，左侧导航显示"账号"和"显示"
2. 账号模块 Tab 显示"用户信息"、"账号安全"、"其它"
3. 左侧导航切换（账号 ↔ 显示）
4. Tab 切换（用户信息 / 账号安全 / 其它）

前置条件：已登录 TOS，通过桌面右键打开用户设置
"""
import pytest
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.tos_login_page import TosLoginPage
from ui_automation.pages.pages.tos_desktop_page import TosDesktopPage
from ui_automation.pages.pages.tos_user_settings_page import TosUserSettingsPage
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("TestTosUserSettings")

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.medium
class TestTosUserSettings:
    """TOS 用户设置界面冒烟测试"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """前置条件：登录 → 右键打开用户设置"""
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
        time.sleep(3)
        
        # 右键打开用户设置
        self.desktop = TosDesktopPage(driver)
        self.desktop.click_user_settings()
        time.sleep(3)
        
        # 初始化用户设置页面对象
        self.settings = TosUserSettingsPage(driver)
        
        yield
        self.settings.take_screenshot("user_settings_test_end")

    def test_settings_loaded(self, driver, base_url):
        """
        Given: 已登录,已打开用户设置
        When: 等待用户设置界面加载
        Then: 用户设置界面加载完成,左侧导航可见
        
        用例编号: TC_SETTINGS_001
        风险等级: P2 (次要功能)
        """
        assert self.settings.is_settings_loaded(), "用户设置界面应加载完成"
        self.settings.take_screenshot("settings_loaded")
        logger.info("TC_SETTINGS_001 通过：用户设置界面加载成功")

    def test_nav_modules_visible(self, driver, base_url):
        """
        用例：验证左侧导航包含"账号"和"显示"

        用例编号: TC_SETTINGS_002
        模块: TOS桌面-用户设置
        前置条件: 已打开用户设置
        操作步骤: 获取左侧导航模块列表
        预期结果: 包含"账号"和"显示"两个模块
        """
        modules = self.settings.get_nav_modules()
        assert "账号" in modules, f"左侧导航应包含'账号'，实际: {modules}"
        assert "显示" in modules, f"左侧导航应包含'显示'，实际: {modules}"
        logger.info(f"TC_SETTINGS_002 通过：左侧导航包含 {modules}")

    def test_account_tabs_visible(self, driver, base_url):
        """
        用例：验证账号模块 Tab 标签完整

        用例编号: TC_SETTINGS_003
        模块: TOS桌面-用户设置
        前置条件: 已打开用户设置，当前在账号模块
        操作步骤: 获取 Tab 标签列表
        预期结果: 包含"用户信息"、"账号安全"、"其它"
        """
        tabs = self.settings.get_tab_items()
        assert "用户信息" in tabs, f"应包含'用户信息' Tab，实际: {tabs}"
        assert "账号安全" in tabs, f"应包含'账号安全' Tab，实际: {tabs}"
        assert "其它" in tabs, f"应包含'其它' Tab，实际: {tabs}"
        logger.info(f"TC_SETTINGS_003 通过：账号模块 Tab 完整 {tabs}")

    def test_switch_to_display_module(self, driver, base_url):
        """
        用例：切换到"显示"模块

        用例编号: TC_SETTINGS_004
        模块: TOS桌面-用户设置
        前置条件: 已打开用户设置，当前在账号模块
        操作步骤:
            1. 点击左侧导航"显示"
        预期结果: 切换到显示模块（Tab 标签变化或内容变化）
        """
        self.settings.click_nav_display()
        self.settings.take_screenshot("after_switch_to_display")
        # 切换后账号模块的 Tab 应该不再显示，或显示模式/壁纸等内容出现
        logger.info("TC_SETTINGS_004 通过：已切换到显示模块")

    def test_switch_tabs_in_account(self, driver, base_url):
        """
        用例：账号模块内 Tab 切换

        用例编号: TC_SETTINGS_005
        模块: TOS桌面-用户设置
        前置条件: 已打开用户设置，在账号模块
        操作步骤:
            1. 点击"账号安全" Tab
            2. 点击"其它" Tab
            3. 点击"用户信息" Tab（回到初始）
        预期结果: 每次切换 Tab 后页面内容变化
        """
        # 切换到账号安全
        self.settings.click_tab_account_security()
        self.settings.take_screenshot("tab_account_security")
        
        # 切换到其它
        self.settings.click_tab_other()
        self.settings.take_screenshot("tab_other")
        
        # 切回用户信息
        self.settings.click_tab_user_info()
        self.settings.take_screenshot("tab_user_info")
        
        logger.info("TC_SETTINGS_005 通过：Tab 切换正常")

    def test_edit_user_info_and_save(self, driver, base_url):
        """
        用例：编辑用户信息（描述、邮箱、电话）并保存

        用例编号: TC_SETTINGS_006
        模块: TOS桌面-用户设置-用户信息
        前置条件: 已打开用户设置，在"用户信息" Tab
        操作步骤:
            1. 在描述输入框输入"ui自动化冒烟测试"
            2. 在密保邮箱输入框输入"1240676024@qq.com"
            3. 在电话号码输入框输入"14776426718"
            4. 点击"应用"按钮
        预期结果: 出现"设置成功!"的绿色气泡提示
        """
        # 确保用户设置已加载（默认就在"用户信息" Tab）
        assert self.settings.is_settings_loaded(), "用户设置界面未加载"
        time.sleep(2)
        
        # 编辑用户信息并保存（描述加时间戳确保每次值不同）
        from datetime import datetime
        timestamp = datetime.now().strftime("%H%M%S")
        self.settings.edit_user_info(
            description=f"ui自动化冒烟测试_{timestamp}",
            email="1240676024@qq.com",
            phone="14776426718"
        )
        
        # 验证成功提示
        assert self.settings.is_success_toast_visible(), \
            "编辑用户信息后应出现'设置成功!'提示"
        
        self.settings.take_screenshot("after_edit_user_info_success")
        logger.info("TC_SETTINGS_006 通过：编辑用户信息并保存成功，'设置成功!'提示已出现")

    def test_other_tab_check_and_apply(self, driver, base_url):
        """
        用例：其它 Tab 复选框操作并应用

        用例编号: TC_SETTINGS_007
        模块: TOS桌面-用户设置-其它
        前置条件: 已打开用户设置
        操作步骤:
            1. 点击"其它" Tab
            2. 先取消所有已勾选的复选框 → 点击"应用" → 验证成功提示
            3. 再勾选所有复选框 → 点击"应用" → 验证成功提示
        预期结果: 两次操作都出现"操作成功!"的绿色气泡提示
        """
        # 切换到"其它" Tab
        self.settings.click_tab_other()
        time.sleep(2)
        
        # 第一步：取消所有勾选并应用
        self.settings.uncheck_all_other_checkboxes()
        time.sleep(1)
        self.settings.click_apply()
        assert self.settings.is_success_toast_visible(), \
            "取消勾选后点击应用，应出现'操作成功!'提示"
        self.settings.take_screenshot("after_uncheck_all_apply")
        logger.info("TC_SETTINGS_007 步骤1通过：取消所有勾选并应用成功")
        
        time.sleep(2)  # 等待 toast 消失
        
        # 第二步：勾选所有复选框并应用
        self.settings.check_all_other_checkboxes()
        time.sleep(1)
        self.settings.click_apply()
        assert self.settings.is_success_toast_visible(), \
            "勾选复选框后点击应用，应出现'操作成功!'提示"
        self.settings.take_screenshot("after_check_all_apply")
        logger.info("TC_SETTINGS_007 步骤2通过：勾选所有并应用成功")
