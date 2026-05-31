# common/report_utils.py - 报告生成工具模块
"""
提供测试报告相关的工具函数：
- 时间戳生成
- 报告目录创建
- 简单 HTML 报告片段生成
"""

import os
from datetime import datetime


def get_timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """
    生成当前时间戳字符串

    Args:
        fmt: 时间格式，默认为 YYYYmmdd_HHMMSS

    Returns:
        格式化后的时间戳字符串

    Usage:
        >>> get_timestamp()
        '20260601_143025'
        >>> get_timestamp("%Y-%m-%d %H:%M:%S")
        '2026-06-01 14:30:25'
    """
    return datetime.now().strftime(fmt)


def get_readable_timestamp() -> str:
    """
    生成可读格式的时间戳

    Returns:
        格式如 '2026-06-01 14:30:25' 的字符串
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_report_dir(base_dir: str = None, prefix: str = "report") -> str:
    """
    创建带时间戳的报告输出目录

    Args:
        base_dir: 报告根目录，默认为项目根目录下的 reports/ 文件夹
        prefix: 目录前缀名

    Returns:
        创建好的报告目录绝对路径

    Usage:
        >>> report_dir = create_report_dir()
        >>> # 生成类似: /project/reports/report_20260601_143025/
    """
    if base_dir is None:
        # 默认使用项目根目录下的 reports 文件夹
        project_root = os.path.dirname(os.path.dirname(__file__))
        base_dir = os.path.join(project_root, "reports")

    timestamp = get_timestamp()
    report_dir = os.path.join(base_dir, f"{prefix}_{timestamp}")
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def generate_html_summary(
    title: str,
    total: int,
    passed: int,
    failed: int,
    skipped: int = 0,
) -> str:
    """
    生成简单的 HTML 测试报告摘要片段

    Args:
        title: 报告标题
        total: 总用例数
        passed: 通过数
        failed: 失败数
        skipped: 跳过数

    Returns:
        HTML 格式的报告摘要字符串
    """
    pass_rate = (passed / total * 100) if total > 0 else 0
    timestamp = get_readable_timestamp()

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .summary table {{ border-collapse: collapse; width: 100%; }}
        .summary td, .summary th {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        .pass {{ color: #28a745; font-weight: bold; }}
        .fail {{ color: #dc3545; font-weight: bold; }}
        .skip {{ color: #ffc107; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>生成时间: {timestamp}</p>
    <div class="summary">
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>用例总数</td><td>{total}</td></tr>
            <tr><td>通过</td><td class="pass">{passed}</td></tr>
            <tr><td>失败</td><td class="fail">{failed}</td></tr>
            <tr><td>跳过</td><td class="skip">{skipped}</td></tr>
            <tr><td>通过率</td><td>{pass_rate:.1f}%</td></tr>
        </table>
    </div>
</body>
</html>"""
    return html


def save_html_report(html_content: str, filepath: str) -> str:
    """
    将 HTML 报告内容保存到文件

    Args:
        html_content: HTML 字符串内容
        filepath: 保存路径

    Returns:
        实际保存的文件路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath
