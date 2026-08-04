"""冒烟测试级 conftest - 快速验证核心功能"""
import pytest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.logger import get_logger

logger = get_logger("smoke_conftest")

@pytest.fixture(autouse=True)
def smoke_test_setup(request):
    """冒烟测试通用前置"""
    logger.info(f"[冒烟测试] 开始: {request.node.name}")
    yield
    logger.info(f"[冒烟测试] 结束: {request.node.name}")
