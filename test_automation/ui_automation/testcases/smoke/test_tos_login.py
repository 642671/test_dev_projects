"""
TOS 登录功能冒烟测试 (数据驱动版)

测试场景：
1. 勾选"保持登录"进行登录
2. 不勾选"保持登录"进行登录
3. 错误密码登录失败
4. 空用户名登录失败
5. 空密码登录失败

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
@pytest.mark.critical
class TestTosLogin:
    """TOS 登录功能冒烟测试 (数据驱动版)"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """每个测试前打开登录页"""
        self.base_url = base_url
        self.driver = driver
        yield
        # teardown: 截图保留证据
        if hasattr(self, 'login_page'):
            self.login_page.take_screenshot("test_end")

    @pytest.mark.parametrize("case", 
        load_yaml_data(os.path.join(TESTDATA_DIR, "tos_login_data.yaml")).get("test_cases", []),
        ids=lambda c: c["case_id"]
    )
    def test_login_scenarios(self, driver, base_url, case):
        """
        Given: TOS 系统可访问,用户已注册
        When: {case[description]}
        Then: 应得到 {case[expected_result]} 结果
        
        用例编号: {case[case_id]}
        风险等级: P0
        """
        self.login_page = TosLoginPage(driver)
        self.login_page.open_login_page(base_url)
        
        self.login_page.login(
            username=case["username"],
            password=case["password"],
            keep_login=case["keep_login"]
        )
        
        if case["expected_result"] == "success":
            assert self.login_page.is_login_successful(), \
                f"登录应成功: {case['description']}"
            logger.info(f"{case['case_id']} 通过: {case['description']}")
        else:
            assert not self.login_page.is_login_successful(), \
                f"登录应失败: {case['description']}"
            logger.info(f"{case['case_id']} 通过: {case['description']} (预期失败)")
