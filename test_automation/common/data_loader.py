"""
统一数据加载工具
支持 YAML、JSON、Excel 格式的测试数据加载
提供 pytest 参数化所需的数据格式
"""
import os
import json
import yaml
from common.logger import get_logger

logger = get_logger("DataLoader")


class DataLoader:
    """统一测试数据加载器"""
    
    # 项目根目录
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @classmethod
    def load_yaml(cls, file_path, key=None):
        """
        加载 YAML 测试数据
        
        :param file_path: 文件路径（相对于项目根目录或绝对路径）
        :param key: 可选，获取特定键的数据
        :return: 数据字典或列表
        """
        full_path = cls._resolve_path(file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            logger.debug(f"加载 YAML 数据: {full_path}")
            if key:
                return data.get(key)
            return data
        except FileNotFoundError:
            logger.error(f"YAML 文件不存在: {full_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"YAML 解析错误: {e}")
            raise
    
    @classmethod
    def load_json(cls, file_path, key=None):
        """加载 JSON 测试数据"""
        full_path = cls._resolve_path(file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"加载 JSON 数据: {full_path}")
            if key:
                return data.get(key)
            return data
        except FileNotFoundError:
            logger.error(f"JSON 文件不存在: {full_path}")
            raise
    
    @classmethod
    def load_test_cases(cls, file_path, case_key="test_cases"):
        """
        加载用于参数化的测试用例数据
        
        :param file_path: 数据文件路径
        :param case_key: 测试用例的键名
        :return: 测试用例列表（可直接用于 @pytest.mark.parametrize）
        """
        data = cls.load_yaml(file_path)
        cases = data.get(case_key, [])
        logger.info(f"加载了 {len(cases)} 条测试用例: {file_path}")
        return cases
    
    @classmethod
    def load_parametrize_data(cls, file_path, case_key="test_cases", id_field="case_id"):
        """
        加载参数化数据，返回 (ids, data) 元组
        适配 pytest.mark.parametrize(ids=..., argvalues=...)
        
        :return: (ids_list, data_list)
        """
        cases = cls.load_test_cases(file_path, case_key)
        ids = [case.get(id_field, f"case_{i}") for i, case in enumerate(cases)]
        return ids, cases
    
    @classmethod
    def load_fixture_data(cls, file_path):
        """
        加载 fixture 数据（预置数据集）
        
        :return: 数据字典
        """
        return cls.load_yaml(file_path)
    
    @classmethod
    def _resolve_path(cls, file_path):
        """解析文件路径"""
        if os.path.isabs(file_path):
            return file_path
        return os.path.join(cls.PROJECT_ROOT, file_path)


# === 便捷函数（供 conftest 和测试用例直接使用）===

def load_yaml_data(file_path, key=None):
    """便捷函数：加载 YAML 数据"""
    return DataLoader.load_yaml(file_path, key)

def load_test_cases(file_path, case_key="test_cases"):
    """便捷函数：加载测试用例"""
    return DataLoader.load_test_cases(file_path, case_key)

def load_parametrize(file_path, case_key="test_cases", id_field="case_id"):
    """便捷函数：加载参数化数据"""
    return DataLoader.load_parametrize_data(file_path, case_key, id_field)
