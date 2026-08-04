# common/config_utils.py - 配置工具函数
"""
公共配置工具：
- deep_merge: 字典深度合并（用于 local.yaml 覆盖环境配置）
"""


def deep_merge(base: dict, override: dict) -> dict:
    """
    深度合并两个字典，override 中的值覆盖 base 中的同名值。
    - 嵌套字典会递归合并，不会丢失 base 中未被 override 覆盖的键
    - 非字典值直接覆盖
    - 返回新的字典，不修改原参数

    示例：
        base = {"base_url": "http://A", "browser": {"type": "chrome", "headless": False}}
        override = {"base_url": "http://B", "browser": {"headless": True}}
        result = {"base_url": "http://B", "browser": {"type": "chrome", "headless": True}}
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
