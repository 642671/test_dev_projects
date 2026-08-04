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
_MODULE_DIR = os.path.join(os.path.dirname(__file__), '..')
if os.path.abspath(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(_MODULE_DIR))

from api_testing.api_client.base_client import BaseClient
from config.settings import settings


@pytest.fixture
def api_client():
    """基础 API 客户端 fixture（无认证）"""
    client = BaseClient()
    yield client
    client.close()


@pytest.fixture
def auth_client():
    """带 Token 认证的 API 客户端 fixture"""
    client = BaseClient()
    token = settings.token
    if token:
        client.set_token(token)
    yield client
    client.close()


@pytest.fixture
def base_url():
    """获取 API 基础地址 fixture"""
    return settings.base_url
