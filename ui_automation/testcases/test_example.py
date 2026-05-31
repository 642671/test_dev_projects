"""
UI 自动化示例测试用例 - 登录功能
演示如何使用 driver fixture + Page Object 模式编写 UI 自动化测试。

注意：以下测试用例为框架演示用途，实际使用时需要：
1. 将 BASE_URL 替换为真实的测试环境地址
2. 将页面元素定位器替换为真实页面的定位器
3. 将断言替换为实际的验证逻辑
"""
import pytest
import yaml
import os

from ui_automation.pages.example_page import LoginPage
from config.settings import settings
from common.logger import get_logger

logger = get_logger("TestLogin")

# 测试数据文件路径
TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "..", "testdata")


def load_login_data():
    """加载登录测试数据"""
    data_file = os.path.join(TESTDATA_DIR, "login_data.yaml")
    with open(data_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.ui
class TestLogin:
    """登录功能测试类"""

    @pytest.mark.smoke
    @pytest.mark.skip(reason="示例测试 - 请替换为实际测试环境地址后运行")
    def test_valid_login(self, driver, base_url):
        """
        测试用例：使用有效凭据登录

        步骤：
        1. 打开登录页面
        2. 输入正确的用户名和密码
        3. 点击登录
        4. 验证登录成功（URL 跳转到首页）
        """
        # 加载测试数据
        test_data = load_login_data()
        valid_data = test_data["valid_login"]

        # 实例化登录页面
        login_page = LoginPage(driver, base_url=base_url)

        # 打开登录页面
        login_page.open_login_page()

        # 执行登录操作
        login_page.login(
            username=valid_data["username"],
            password=valid_data["password"]
        )

        # 验证登录成功 - 检查 URL 是否跳转到首页
        login_page.wait_for_url_contains("/dashboard")
        assert "/dashboard" in driver.current_url, "登录后应跳转到首页"
        logger.info("有效登录测试通过")

    @pytest.mark.skip(reason="示例测试 - 请替换为实际测试环境地址后运行")
    def test_invalid_login_empty_username(self, driver, base_url):
        """
        测试用例：用户名为空时登录失败

        步骤：
        1. 打开登录页面
        2. 不输入用户名，输入密码
        3. 点击登录
        4. 验证错误提示显示
        """
        # 加载测试数据
        test_data = load_login_data()
        invalid_data = test_data["invalid_login"][0]  # 用户名为空的数据

        # 实例化登录页面
        login_page = LoginPage(driver, base_url=base_url)

        # 打开登录页面
        login_page.open_login_page()

        # 执行登录操作（用户名为空）
        login_page.login(
            username=invalid_data["username"],
            password=invalid_data["password"]
        )

        # 验证错误提示
        error_msg = login_page.get_error_message()
        assert error_msg == invalid_data["expected"], \
            f"错误提示不匹配，期望: '{invalid_data['expected']}', 实际: '{error_msg}'"
        logger.info("空用户名登录测试通过")

    @pytest.mark.skip(reason="示例测试 - 请替换为实际测试环境地址后运行")
    def test_invalid_login_wrong_credentials(self, driver, base_url):
        """
        测试用例：使用错误的用户名和密码登录

        步骤：
        1. 打开登录页面
        2. 输入错误的用户名和密码
        3. 点击登录
        4. 验证错误提示显示
        """
        # 加载测试数据
        test_data = load_login_data()
        invalid_data = test_data["invalid_login"][2]  # 错误用户名/密码的数据

        # 实例化登录页面
        login_page = LoginPage(driver, base_url=base_url)

        # 打开登录页面
        login_page.open_login_page()

        # 执行登录操作（错误凭据）
        login_page.login(
            username=invalid_data["username"],
            password=invalid_data["password"]
        )

        # 验证错误提示
        error_msg = login_page.get_error_message()
        assert error_msg == invalid_data["expected"], \
            f"错误提示不匹配，期望: '{invalid_data['expected']}', 实际: '{error_msg}'"
        logger.info("错误凭据登录测试通过")


@pytest.mark.ui
class TestLoginPageDisplay:
    """登录页面展示测试类"""

    @pytest.mark.skip(reason="示例测试 - 请替换为实际测试环境地址后运行")
    def test_login_page_elements_visible(self, driver, base_url):
        """
        测试用例：验证登录页面核心元素是否可见

        步骤：
        1. 打开登录页面
        2. 验证用户名输入框可见
        3. 验证密码输入框可见
        4. 验证登录按钮可见
        """
        login_page = LoginPage(driver, base_url=base_url)
        login_page.open_login_page()

        # 验证页面元素可见
        assert login_page.is_element_visible(LoginPage.USERNAME_INPUT), \
            "用户名输入框应可见"
        assert login_page.is_element_visible(LoginPage.PASSWORD_INPUT), \
            "密码输入框应可见"
        assert login_page.is_element_visible(LoginPage.LOGIN_BUTTON), \
            "登录按钮应可见"
        logger.info("登录页面元素展示测试通过")
