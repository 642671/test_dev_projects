"""
TOS 登录功能冒烟测试

测试场景：
1. 勾选"保持登录"进行登录
2. 不勾选"保持登录"进行登录

被测地址：http://192.168.64.7:8181
账号：test / Admin123
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.pages.pages.tos_login_page import TosLoginPage
from common.logger import get_logger
from common.data_loader import load_yaml_data

logger = get_logger("TestTosLogin")

# 测试数据目录
TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')


@pytest.mark.smoke
@pytest.mark.ui
class TestTosLogin:
    """TOS 登录功能冒烟测试"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """每个测试前打开登录页"""
        self.login_page = TosLoginPage(driver)
        self.login_page.open_login_page(base_url)
        self.test_data = load_yaml_data(
            os.path.join(TESTDATA_DIR, "tos_login_data.yaml")
        )
        yield
        # teardown: 截图保留证据
        self.login_page.take_screenshot("test_end")

    def test_login_with_keep_login(self, driver, base_url):
        """
        测试用例：勾选"保持登录"进行登录

        用例编号: TC_LOGIN_001
        模块: 登录模块
        前置条件: TOS 系统可访问，用户已注册
        操作步骤:
            1. 打开登录页面
            2. 输入用户名 test
            3. 点击下一步
            4. 输入密码 Admin123
            5. 勾选"保持登录"复选框
            6. 点击下一步完成登录
        预期结果: 登录成功，进入桌面页面
        """
        login_data = self.test_data["valid_login"]

        # 执行登录（勾选保持登录）
        self.login_page.login(
            username=login_data["username"],
            password=login_data["password"],
            keep_login=True
        )

        # 验证登录成功
        assert self.login_page.is_login_successful(), \
            "勾选保持登录后，应成功登录并进入桌面"

        logger.info("TC_LOGIN_001 通过：勾选保持登录，登录成功")

    def test_login_without_keep_login(self, driver, base_url):
        """
        测试用例：不勾选"保持登录"进行登录

        用例编号: TC_LOGIN_002
        模块: 登录模块
        前置条件: TOS 系统可访问，用户已注册
        操作步骤:
            1. 打开登录页面
            2. 输入用户名 test
            3. 点击下一步
            4. 输入密码 Admin123
            5. 不勾选"保持登录"复选框
            6. 点击下一步完成登录
        预期结果: 登录成功，进入桌面页面
        """
        login_data = self.test_data["valid_login"]

        # 执行登录（不勾选保持登录）
        self.login_page.login(
            username=login_data["username"],
            password=login_data["password"],
            keep_login=False
        )

        # 验证登录成功
        assert self.login_page.is_login_successful(), \
            "不勾选保持登录，也应成功登录并进入桌面"

        logger.info("TC_LOGIN_002 通过：不勾选保持登录，登录成功")
