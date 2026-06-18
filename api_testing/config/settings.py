# api_testing/config/settings.py - 接口测试模块配置管理
"""
接口测试模块专属配置管理器：
- 读取本模块 config/environments/ 目录下的 YAML 配置文件
- 支持通过环境变量 TEST_ENV 切换环境（默认 test）
- 支持 local.yaml 本地覆盖（被 .gitignore 排除，不同步到 Git）
- 模块内使用：from config.settings import settings
"""

import os
import yaml
from common.config_utils import deep_merge


class Settings:
    """
    接口测试模块配置管理类

    配置加载优先级（后者覆盖前者）：
        environments/{env}.yaml  →  config/local.yaml

    Usage:
        from config.settings import settings
        print(settings.base_url)
        print(settings.get("timeout"))
    """

    def __init__(self, env: str = None):
        """
        Args:
            env: 环境名称（dev/test/prod），默认从环境变量 TEST_ENV 读取，缺省 test
        """
        self.env = env or os.getenv("TEST_ENV", "test")
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """
        加载配置文件，支持 local.yaml 本地覆盖：
        1. 加载 environments/{env}.yaml 作为基础配置
        2. 如果 config/local.yaml 存在，则深合并覆盖基础配置
        """
        # 步骤 1：加载环境 YAML
        config_dir = os.path.join(os.path.dirname(__file__), "environments")
        config_file = os.path.join(config_dir, f"{self.env}.yaml")

        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"配置文件不存在: {config_file}，请检查环境名称 '{self.env}' 是否正确"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # 步骤 2：加载 local.yaml 覆盖（如果存在）
        local_file = os.path.join(os.path.dirname(__file__), "local.yaml")
        if os.path.exists(local_file):
            with open(local_file, "r", encoding="utf-8") as f:
                local_config = yaml.safe_load(f) or {}
            config = deep_merge(config, local_config)

        return config

    @property
    def base_url(self) -> str:
        """接口基础地址"""
        return self._config.get("base_url", "")

    @property
    def timeout(self) -> int:
        """请求超时时间（秒）"""
        return self._config.get("timeout", 30)

    @property
    def token(self) -> str:
        """认证 Token"""
        return self._config.get("token", "")

    @property
    def env_name(self) -> str:
        """环境显示名称"""
        return self._config.get("env_name", "")

    def get(self, key: str, default=None):
        """通用配置获取方法"""
        return self._config.get(key, default)

    def __repr__(self) -> str:
        return f"<API Settings env='{self.env}' base_url='{self.base_url}'>"


# 模块全局配置实例
settings = Settings()
