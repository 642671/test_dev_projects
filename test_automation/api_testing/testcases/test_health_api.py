"""
API 健康检查测试

测试场景：
1. 验证 API 服务是否正常运行
2. 验证响应时间是否在可接受范围内

被测地址：从 config/settings.py 读取
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.data_loader import load_yaml_data
from common.logger import get_logger

logger = get_logger("TestHealthAPI")
TESTDATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'testdata')


@pytest.mark.api
@pytest.mark.critical
class TestHealthAPI:
    """API 健康检查测试"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, base_url):
        """测试前置：初始化 API 客户端和测试数据"""
        self.client = api_client
        self.base_url = base_url
        self.test_data = load_yaml_data(os.path.join(TESTDATA_DIR, "health_check.yaml"))
        yield

    def test_health_check(self):
        """
        Given: API 服务可访问
        When: 发送 GET 请求到 /api/health
        Then: 返回 200 状态码,响应时间 < 3s
        
        用例编号: API_HEALTH_001
        风险等级: P0 (核心功能)
        """
        endpoint = self.test_data["endpoints"]["health"]
        response = self.client.get(endpoint["path"])
        
        # 断言状态码
        self.client.assert_status_code(response, 200)
        
        # 断言响应时间
        expected = endpoint["test_cases"][0]["expected"]
        self.client.assert_response_time(response, expected["response_time_max"])
        
        logger.info("API_HEALTH_001 通过: 健康检查正常")
