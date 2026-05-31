"""
示例接口测试用例
演示如何使用 BaseClient 进行接口测试

说明：
    - 本文件为接口测试示例，展示 BaseClient 的常用调用方式
    - 标注 [TODO: 替换] 的地方需要替换为实际接口地址和参数
    - 运行命令: pytest api_testing/testcases/test_example_api.py -v -m api
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api_testing.api_client.base_client import BaseClient


class TestExampleAPI:
    """示例 API 测试类 —— 展示接口测试的基本写法"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        测试前置：初始化 API 客户端
        - autouse=True 表示每个测试方法执行前自动调用
        - yield 之后的代码在测试结束后执行（清理工作）
        """
        self.client = BaseClient()
        yield
        # 测试结束后关闭 session，释放资源
        self.client.close()

    @pytest.mark.api
    def test_health_check(self):
        """
        测试健康检查接口
        场景：验证服务是否正常运行，通常返回 200 状态码
        """
        # [TODO: 替换] 将 /api/health 替换为实际的健康检查接口路径
        # response = self.client.get("/api/health")
        #
        # 断言状态码为 200，表示服务正常
        # self.client.assert_status_code(response, 200)
        #
        # 断言响应时间在 3 秒以内
        # self.client.assert_response_time(response, max_time=3.0)
        pass  # 移除 pass 并取消上方注释以启用测试

    @pytest.mark.api
    def test_get_request_example(self):
        """
        示例 GET 请求测试
        场景：获取资源列表，验证返回数据结构
        """
        # [TODO: 替换] 将路径和参数替换为实际接口
        # 发送带查询参数的 GET 请求
        # response = self.client.get("/api/users", params={"page": 1, "size": 10})
        #
        # 步骤1: 验证状态码
        # self.client.assert_status_code(response, 200)
        #
        # 步骤2: 验证响应中包含指定字段
        # self.client.assert_json_key(response, "data")
        #
        # 步骤3: 验证列表不为空
        # self.client.assert_json_list_not_empty(response, key="data")
        #
        # 步骤4: 验证响应时间
        # self.client.assert_response_time(response, max_time=5.0)
        pass  # 移除 pass 并取消上方注释以启用测试

    @pytest.mark.api
    def test_post_request_example(self):
        """
        示例 POST 请求测试
        场景：创建资源（如用户注册、提交表单）
        """
        # [TODO: 替换] 将路径和请求体替换为实际接口
        # 构造请求体
        # request_body = {
        #     "username": "testuser",
        #     "email": "test@example.com",
        #     "password": "Test123456"
        # }
        #
        # 发送 POST 请求，json_data 会自动序列化为 JSON
        # response = self.client.post("/api/users", json_data=request_body)
        #
        # 步骤1: 验证状态码（创建成功通常返回 201）
        # self.client.assert_status_code(response, 201)
        #
        # 步骤2: 验证响应中包含新建资源的 ID
        # self.client.assert_json_key(response, "id")
        #
        # 步骤3: 验证响应包含期望的键值对
        # self.client.assert_json_contains(response, {"username": "testuser"})
        pass  # 移除 pass 并取消上方注释以启用测试

    @pytest.mark.api
    def test_response_assertion_example(self):
        """
        响应断言示例
        场景：展示各种断言方法的使用方式
        """
        # [TODO: 替换] 将路径替换为实际接口
        # response = self.client.get("/api/status")
        #
        # --- 断言状态码 ---
        # self.client.assert_status_code(response, 200)
        #
        # --- 断言响应 JSON 中包含 key ---
        # self.client.assert_json_key(response, "code")
        #
        # --- 断言响应 JSON 中 key 的值 ---
        # self.client.assert_json_key(response, "code", expected_value=0)
        #
        # --- 断言响应包含多个键值对 ---
        # self.client.assert_json_contains(response, {
        #     "code": 0,
        #     "message": "success"
        # })
        #
        # --- 断言列表不为空 ---
        # self.client.assert_json_list_not_empty(response, key="items")
        #
        # --- 断言响应时间 ---
        # self.client.assert_response_time(response, max_time=2.0)
        pass  # 移除 pass 并取消上方注释以启用测试

    @pytest.mark.api
    def test_custom_headers_example(self):
        """
        自定义 Headers 示例
        场景：某些接口需要额外的自定义请求头
        """
        # [TODO: 替换] 替换为实际接口
        # 自定义请求头（会覆盖默认 headers 中的同名字段）
        # custom_headers = {
        #     "X-Request-Id": "test-12345",
        #     "X-Custom-Header": "custom-value"
        # }
        # response = self.client.get("/api/data", headers=custom_headers)
        # self.client.assert_status_code(response, 200)
        pass  # 移除 pass 并取消上方注释以启用测试

    @pytest.mark.api
    def test_token_auth_example(self):
        """
        Token 认证示例
        场景：先登录获取 token，再用 token 访问需要鉴权的接口
        """
        # [TODO: 替换] 替换为实际的登录和业务接口
        # 步骤1: 登录获取 token
        # login_body = {"username": "admin", "password": "admin123"}
        # login_resp = self.client.post("/api/login", json_data=login_body)
        # self.client.assert_status_code(login_resp, 200)
        # token = login_resp.json().get("token")
        #
        # 步骤2: 设置 token 到客户端
        # self.client.set_token(token)
        #
        # 步骤3: 使用 token 访问需要认证的接口
        # response = self.client.get("/api/profile")
        # self.client.assert_status_code(response, 200)
        # self.client.assert_json_key(response, "username")
        pass  # 移除 pass 并取消上方注释以启用测试
