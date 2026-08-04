#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI自动化文档生成器 - 命令行入口

用法:
  单链路模式:
    python -m ui_automation.tools.doc_generator.cli -c configs/login_chain.yaml
  
  批量模式:
    python -m ui_automation.tools.doc_generator.cli --batch configs/*.yaml
  
  指定输出目录:
    python -m ui_automation.tools.doc_generator.cli -c configs/login_chain.yaml -o ./output
  
  无头模式:
    python -m ui_automation.tools.doc_generator.cli -c configs/login_chain.yaml --headless
"""

import argparse
import sys
import os
import glob

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ui_automation.tools.doc_generator.generator import DocGenerator
from common.logger import get_logger

logger = get_logger("DocGeneratorCLI")


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="UI自动化测试链路文档生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成单个链路文档
  python -m ui_automation.tools.doc_generator.cli -c configs/login_chain.yaml

  # 批量生成多个链路文档
  python -m ui_automation.tools.doc_generator.cli --batch configs/*.yaml

  # 指定输出目录
  python -m ui_automation.tools.doc_generator.cli -c configs/login_chain.yaml -o ./output

  # 无头模式（不显示浏览器窗口）
  python -m ui_automation.tools.doc_generator.cli -c configs/login_chain.yaml --headless
        """
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="链路配置文件路径 (YAML格式)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出目录（默认在configs/output目录下）"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用无头模式运行浏览器（不显示窗口）"
    )
    
    parser.add_argument(
        "--batch",
        nargs="+",
        type=str,
        metavar="CONFIG",
        help="批量生成：传入多个配置文件路径，支持通配符（如 configs/*.yaml）"
    )
    
    args = parser.parse_args()
    
    # 批量模式
    if args.batch:
        config_files = []
        for pattern in args.batch:
            # 支持通配符
            matched = glob.glob(pattern)
            if matched:
                config_files.extend(matched)
            else:
                logger.warning(f"未找到匹配的配置文件: {pattern}")
        
        if not config_files:
            print("错误：未找到任何配置文件")
            sys.exit(1)
        
        print(f"\n🚀 批量生成模式：将处理 {len(config_files)} 个配置文件\n")
        
        success_count = 0
        fail_count = 0
        
        for i, config_path in enumerate(config_files, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(config_files)}] 处理: {config_path}")
            print(f"{'='*60}")
            
            try:
                gen = DocGenerator(config_path, args.output, args.headless)
                output_path = gen.generate()
                print(f"✅ 成功生成: {output_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ 生成失败: {e}")
                fail_count += 1
                logger.error(f"处理 {config_path} 失败: {e}", exc_info=True)
        
        print(f"\n{'='*60}")
        print(f"📊 批量生成完成")
        print(f"   成功: {success_count} 个")
        print(f"   失败: {fail_count} 个")
        print(f"{'='*60}\n")
        
        sys.exit(0 if fail_count == 0 else 1)
    
    # 单链路模式
    elif args.config:
        if not os.path.exists(args.config):
            print(f"错误：配置文件不存在: {args.config}")
            sys.exit(1)
        
        print(f"\n🚀 开始生成测试链路文档")
        print(f"   配置文件: {args.config}")
        if args.output:
            print(f"   输出目录: {args.output}")
        if args.headless:
            print(f"   模式: 无头模式")
        print()
        
        try:
            gen = DocGenerator(args.config, args.output, args.headless)
            output_path = gen.generate()
            print(f"\n✅ 文档生成成功: {output_path}\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 文档生成失败: {e}\n")
            logger.error(f"文档生成失败: {e}", exc_info=True)
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
