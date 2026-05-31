"""
api_testing/testcases 的 conftest.py
提供接口测试公共 fixtures：
- api_client: 基础 API 客户端（无认证）
- auth_client: 带 Token 认证的 API 客户端
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api_testing.api_client.base_client import BaseClient
from config.settings import settings


@pytest.fixture
def api_client():
    """
    基础 API 客户端 fixture（无认证）

    使用方式：
        def test_example(self, api_client):
            response = api_client.get("/api/health")
            api_client.assert_status_code(response, 200)
    """
    client = BaseClient()
    yield client
    # 测试结束后自动关闭连接
    client.close()


@pytest.fixture
def auth_client():
    """
    带 Token 认证的 API 客户端 fixture

    从配置文件中读取 token，或通过登录接口获取。
    适用于需要鉴权的接口测试。

    使用方式：
        def test_protected_api(self, auth_client):
            response = auth_client.get("/api/profile")
            auth_client.assert_status_code(response, 200)
    """
    client = BaseClient()

    # 方式1: 从配置文件获取 token（适用于静态 token 场景）
    token = settings.get("api", {}).get("token", "")

    # 方式2: 如果配置中没有 token，可以通过登录接口动态获取
    # [TODO: 替换] 取消下方注释并修改为实际的登录接口
    if not token:
        # try:
        #     login_data = {
        #         "username": settings.username,
        #         "password": settings.password
        #     }
        #     response = client.post("/api/login", json_data=login_data)
        #     if response.status_code == 200:
        #         token = response.json().get("token", "")
        # except Exception as e:
        #     pytest.skip(f"获取认证 token 失败: {e}")
        pass

    if token:
        client.set_token(token)

    yield client
    # 测试结束后自动关闭连接
    client.close()


@pytest.fixture
def base_url():
    """
    获取 API 基础地址 fixture
    便于测试中直接使用基础 URL
    """
    return settings.get("api", {}).get("base_url", "")
