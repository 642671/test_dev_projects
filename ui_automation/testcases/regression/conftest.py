"""回归测试级 conftest"""
import pytest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.logger import get_logger

logger = get_logger("regression_conftest")

@pytest.fixture(autouse=True)
def regression_test_setup(request):
    """回归测试通用前置"""
    logger.info(f"[回归测试] 开始: {request.node.name}")
    yield
    logger.info(f"[回归测试] 结束: {request.node.name}")
