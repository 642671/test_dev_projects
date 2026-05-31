"""
测试用例生成器
从需求描述/测试点生成结构化的测试用例
支持导出为 YAML 和 Excel 格式
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.logger import get_logger
from common.file_handler import YAMLHandler, ExcelHandler

logger = get_logger("TestCaseGenerator")


class TestCaseGenerator:
    """测试用例生成器"""

    # Excel 表头（对应用例字段）
    EXCEL_HEADERS = ["用例编号", "模块", "用例名称", "前置条件", "操作步骤", "输入数据", "预期结果", "测试结果", "备注"]

    def __init__(self, module_name, module_abbr=None):
        """
        初始化
        :param module_name: 模块名称（如 "登录模块"）
        :param module_abbr: 模块缩写（如 "LOGIN"），用于生成用例编号
        """
        self.module_name = module_name
        self.module_abbr = module_abbr or self._generate_abbr(module_name)
        self.test_cases = []
        self._seq = 0
        logger.info(f"初始化测试用例生成器 - 模块: {self.module_name}, 缩写: {self.module_abbr}")

    @staticmethod
    def _generate_abbr(module_name):
        """
        从模块名生成缩写
        规则：
        - 如果模块名包含英文，取英文部分大写
        - 如果纯中文，取拼音首字母（简化处理：取每个字的 Unicode 编码后几位）
        - 去掉常见后缀如"模块"
        :param module_name: 模块名称
        :return: 模块缩写（大写字母）
        """
        import re
        # 去掉"模块"后缀
        name = module_name.replace("模块", "").strip()

        # 尝试提取英文部分
        english_parts = re.findall(r'[a-zA-Z]+', name)
        if english_parts:
            # 有英文字符，取英文部分拼接并大写
            return "".join(english_parts).upper()

        # 纯中文：使用简化的拼音首字母映射
        # 这里采用简单方式：取每个汉字的序号作为标识
        abbr = ""
        for char in name:
            if '\u4e00' <= char <= '\u9fff':
                # 中文字符，使用简单的首字母映射表（常用字）
                abbr += _get_pinyin_initial(char)
            elif char.isalnum():
                abbr += char.upper()
        return abbr.upper() if abbr else "MOD"

    def _next_case_id(self):
        """生成下一个用例编号"""
        self._seq += 1
        return f"TC_{self.module_abbr}_{self._seq:03d}"

    def add_case(self, case_name, steps, expected_result,
                 precondition="无", input_data="无", remark=""):
        """
        添加一条测试用例
        :param case_name: 用例名称
        :param steps: 操作步骤（列表）
        :param expected_result: 预期结果
        :param precondition: 前置条件
        :param input_data: 输入数据
        :param remark: 备注
        :return: 生成的用例字典
        """
        case_id = self._next_case_id()
        test_case = {
            "case_id": case_id,
            "module": self.module_name,
            "case_name": case_name,
            "precondition": precondition,
            "steps": steps if isinstance(steps, list) else [steps],
            "input_data": input_data,
            "expected_result": expected_result,
            "test_result": "未执行",
            "remark": remark
        }
        self.test_cases.append(test_case)
        logger.info(f"添加测试用例: {case_id} - {case_name}")
        return test_case

    def add_cases_from_test_points(self, test_points):
        """
        从测试点列表批量生成测试用例
        :param test_points: 测试点列表，每项为字典:
            {
                "name": "测试点名称",
                "steps": ["步骤1", "步骤2"],
                "expected": "预期结果",
                "precondition": "前置条件（可选）",
                "input_data": "输入数据（可选）"
            }
        :return: 生成的用例列表
        """
        generated = []
        for point in test_points:
            case = self.add_case(
                case_name=point.get("name", "未命名测试点"),
                steps=point.get("steps", []),
                expected_result=point.get("expected", ""),
                precondition=point.get("precondition", "无"),
                input_data=point.get("input_data", "无"),
                remark=point.get("remark", "")
            )
            generated.append(case)
        logger.info(f"从测试点批量生成 {len(generated)} 条用例")
        return generated

    def export_to_yaml(self, output_path):
        """
        导出测试用例为 YAML 格式
        :param output_path: 输出文件路径
        """
        if not self.test_cases:
            logger.warning("没有可导出的测试用例")
            return

        # 构建导出数据
        export_data = {
            "module": self.module_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": len(self.test_cases),
            "test_cases": self.test_cases
        }

        YAMLHandler.write(output_path, export_data)
        logger.info(f"测试用例已导出为 YAML: {output_path}, 共 {len(self.test_cases)} 条")

    def export_to_excel(self, output_path):
        """
        导出测试用例为 Excel 格式
        :param output_path: 输出文件路径
        """
        if not self.test_cases:
            logger.warning("没有可导出的测试用例")
            return

        # 将用例数据转换为 Excel 行格式
        excel_data = []
        for case in self.test_cases:
            row = {
                "用例编号": case["case_id"],
                "模块": case["module"],
                "用例名称": case["case_name"],
                "前置条件": case["precondition"],
                "操作步骤": "\n".join(case["steps"]) if isinstance(case["steps"], list) else case["steps"],
                "输入数据": case["input_data"],
                "预期结果": case["expected_result"],
                "测试结果": case["test_result"],
                "备注": case["remark"]
            }
            excel_data.append(row)

        ExcelHandler.write(output_path, excel_data, sheet_name="测试用例", headers=self.EXCEL_HEADERS)
        logger.info(f"测试用例已导出为 Excel: {output_path}, 共 {len(self.test_cases)} 条")

    def get_summary(self):
        """获取用例统计摘要"""
        return {
            "module": self.module_name,
            "total_cases": len(self.test_cases),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def clear(self):
        """清空已生成的用例"""
        self.test_cases = []
        self._seq = 0
        logger.info(f"已清空模块 '{self.module_name}' 的所有测试用例")


# === 辅助函数 ===

def _get_pinyin_initial(char):
    """
    获取中文字符的拼音首字母（简化版）
    使用 Unicode 编码区间粗略映射
    :param char: 单个中文字符
    :return: 拼音首字母（大写）
    """
    # 常用汉字拼音首字母映射表（覆盖常见字）
    pinyin_map = {
        '登': 'D', '录': 'L', '注': 'Z', '册': 'C', '搜': 'S', '索': 'S',
        '购': 'G', '物': 'W', '车': 'C', '支': 'Z', '付': 'F', '订': 'D',
        '单': 'D', '用': 'Y', '户': 'H', '管': 'G', '理': 'L', '系': 'X',
        '统': 'T', '设': 'S', '置': 'Z', '首': 'S', '页': 'Y', '商': 'S',
        '品': 'P', '分': 'F', '类': 'L', '消': 'X', '息': 'X', '通': 'T',
        '知': 'Z', '报': 'B', '表': 'B', '权': 'Q', '限': 'X', '角': 'J',
        '色': 'S', '数': 'S', '据': 'J', '导': 'D', '入': 'R', '出': 'C',
        '文': 'W', '件': 'J', '上': 'S', '传': 'C', '下': 'X', '载': 'Z',
        '审': 'S', '核': 'H', '流': 'L', '程': 'C', '测': 'C', '试': 'S',
        '接': 'J', '口': 'K', '配': 'P', '个': 'G', '人': 'R', '中': 'Z',
        '心': 'X', '安': 'A', '全': 'Q', '日': 'R', '志': 'Z', '评': 'P',
        '论': 'L', '收': 'S', '藏': 'C', '地': 'D', '址': 'Z', '活': 'H',
        '动': 'D', '优': 'Y', '惠': 'H', '券': 'Q', '积': 'J', '分': 'F',
    }
    if char in pinyin_map:
        return pinyin_map[char]
    # 如果不在映射表中，根据 Unicode 粗略估算
    code = ord(char)
    # 简单取模生成一个字母
    return chr(65 + (code % 26))


# === 便捷函数 ===

def generate_testcases(module_name, test_points, output_dir=None, formats=None):
    """
    便捷函数：一键从测试点生成测试用例并导出
    :param module_name: 模块名称
    :param test_points: 测试点列表
    :param output_dir: 输出目录（默认当前目录）
    :param formats: 导出格式列表，如 ["yaml", "excel"]，默认两种都导出
    :return: 生成的用例列表
    """
    if output_dir is None:
        output_dir = os.getcwd()
    if formats is None:
        formats = ["yaml", "excel"]

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 创建生成器并生成用例
    gen = TestCaseGenerator(module_name)
    gen.add_cases_from_test_points(test_points)

    # 生成安全的文件名（去掉中文"模块"后缀，使用模块缩写）
    safe_name = gen.module_abbr.lower()

    # 按格式导出
    if "yaml" in formats:
        yaml_path = os.path.join(output_dir, f"{safe_name}_testcases.yaml")
        gen.export_to_yaml(yaml_path)

    if "excel" in formats:
        excel_path = os.path.join(output_dir, f"{safe_name}_testcases.xlsx")
        gen.export_to_excel(excel_path)

    # 打印摘要
    summary = gen.get_summary()
    logger.info(f"用例生成完成 - {summary}")

    return gen.test_cases
