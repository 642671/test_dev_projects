"""
测试用例生成器使用示例
演示如何从需求/测试点生成测试用例
"""
import os
import sys

# 确保可以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from testcase_generator.generator import TestCaseGenerator, generate_testcases

# 示例：登录模块测试用例生成
login_test_points = [
    {
        "name": "正确用户名密码登录",
        "steps": ["打开登录页面", "输入正确用户名", "输入正确密码", "点击登录按钮"],
        "expected": "登录成功，跳转首页",
        "precondition": "用户已注册",
        "input_data": "用户名: admin, 密码: admin123"
    },
    {
        "name": "用户名为空登录",
        "steps": ["打开登录页面", "不输入用户名", "输入密码", "点击登录按钮"],
        "expected": "提示\"用户名不能为空\"",
        "input_data": "用户名: 空, 密码: admin123"
    },
    {
        "name": "密码为空登录",
        "steps": ["打开登录页面", "输入用户名", "不输入密码", "点击登录按钮"],
        "expected": "提示\"密码不能为空\"",
        "input_data": "用户名: admin, 密码: 空"
    },
    {
        "name": "错误密码登录",
        "steps": ["打开登录页面", "输入正确用户名", "输入错误密码", "点击登录按钮"],
        "expected": "提示\"用户名或密码错误\"",
        "input_data": "用户名: admin, 密码: wrong123"
    },
]

if __name__ == "__main__":
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # 方式1：使用类
    print("=" * 50)
    print("方式1：使用 TestCaseGenerator 类")
    print("=" * 50)

    gen = TestCaseGenerator("登录模块", "LOGIN")
    gen.add_cases_from_test_points(login_test_points)

    # 导出为 YAML
    yaml_output = os.path.join(output_dir, "login_testcases.yaml")
    gen.export_to_yaml(yaml_output)
    print(f"YAML 文件已生成: {yaml_output}")

    # 导出为 Excel
    excel_output = os.path.join(output_dir, "login_testcases.xlsx")
    gen.export_to_excel(excel_output)
    print(f"Excel 文件已生成: {excel_output}")

    # 打印摘要
    summary = gen.get_summary()
    print(f"\n用例统计: {summary}")

    print("\n" + "=" * 50)
    print("方式2：使用 generate_testcases 便捷函数")
    print("=" * 50)

    # 方式2：使用便捷函数
    cases = generate_testcases("登录模块", login_test_points, output_dir=output_dir)
    print(f"共生成 {len(cases)} 条测试用例")

    # 展示生成的用例
    print("\n生成的测试用例预览:")
    print("-" * 50)
    for case in cases:
        print(f"  {case['case_id']}: {case['case_name']}")
        print(f"    预期结果: {case['expected_result']}")
        print()
