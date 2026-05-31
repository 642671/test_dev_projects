# config/settings.py - 全局配置管理模块
"""
环境配置管理：
- 读取 config/environments/ 目录下的 YAML 配置文件
- 支持通过环境变量 TEST_ENV 切换环境（默认 test）
- 提供全局配置对象 settings 供其他模块导入使用
"""

import os
import yaml


class Settings:
    """
    环境配置管理类

    根据环境变量 TEST_ENV 加载对应的 YAML 配置文件，
    提供属性访问和字典风格的 get 方法来获取配置项。

    Usage:
        from config.settings import settings
        print(settings.base_url)
        print(settings.get("database"))
    """

    def __init__(self, env: str = None):
        """
        初始化配置管理器

        Args:
            env: 环境名称，如 dev/test/prod。
                 如果未指定，则从环境变量 TEST_ENV 读取，默认为 test。
        """
        self.env = env or os.getenv("TEST_ENV", "test")
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """加载对应环境的 YAML 配置文件"""
        config_dir = os.path.join(os.path.dirname(__file__), "environments")
        config_file = os.path.join(config_dir, f"{self.env}.yaml")

        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"配置文件不存在: {config_file}，请检查环境名称 '{self.env}' 是否正确"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def base_url(self) -> str:
        """获取基础 URL"""
        return self._config.get("base_url", "")

    @property
    def username(self) -> str:
        """获取用户名"""
        return self._config.get("username", "")

    @property
    def password(self) -> str:
        """获取密码"""
        return self._config.get("password", "")

    @property
    def env_name(self) -> str:
        """获取环境显示名称"""
        return self._config.get("env_name", "")

    @property
    def database(self) -> dict:
        """获取数据库配置"""
        return self._config.get("database", {})

    @property
    def api(self) -> dict:
        """获取 API 配置"""
        return self._config.get("api", {})

    @property
    def browser(self) -> dict:
        """获取浏览器配置（UI 自动化使用）"""
        return self._config.get("browser", {})

    def get(self, key: str, default=None):
        """
        通用配置获取方法

        Args:
            key: 配置键名
            default: 默认值（键不存在时返回）

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def __repr__(self) -> str:
        return f"<Settings env='{self.env}' base_url='{self.base_url}'>"


# 全局配置实例，其他模块直接导入使用
settings = Settings()
