"""
文档生成器核心编排器

协调整个文档生成流程：加载配置 → 执行操作 → 截图 → 生成文档
"""

import os
import yaml
from datetime import datetime

from ui_automation.tools.doc_generator.executor import Executor
from ui_automation.tools.doc_generator.screenshot_mgr import ScreenshotMgr
from ui_automation.tools.doc_generator.templates import WordTemplates
from common.logger import get_logger

logger = get_logger("DocGenerator")


class DocGenerator:
    """UI自动化测试链路文档生成器"""
    
    def __init__(self, config_path, output_dir=None, headless=False):
        """
        初始化文档生成器
        
        Args:
            config_path: YAML配置文件路径
            output_dir: 输出目录，默认为配置文件所在目录下的output文件夹
            headless: 是否使用无头模式
        """
        self.config_path = config_path
        self.chain_config = self._load_config(config_path)
        
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(config_path), "output")
        self.output_dir = output_dir
        
        self.headless = headless
        self.executor = Executor(headless=headless)
        self.screenshot_mgr = ScreenshotMgr()
    
    def generate(self):
        """
        执行完整的文档生成流程
        
        Returns:
            str: 生成的Word文档路径
        """
        chain_name = self.chain_config.get("chain_name", "未命名链路")
        logger.info(f"开始生成测试链路文档: {chain_name}")
        
        try:
            # 1. 初始化浏览器
            logger.info("初始化浏览器...")
            self.executor.init_driver()
            
            # 2. 初始化截图目录
            logger.info("初始化截图目录...")
            self.screenshot_mgr.init_chain(chain_name)
            
            # 3. 创建Word文档
            doc = WordTemplates.create_document()
            
            # 4. 添加标题和链路头部信息
            WordTemplates.add_title(doc, "UI自动化测试链路文档")
            WordTemplates.add_chain_header(doc, self.chain_config)
            
            # 5. 执行每个步骤并生成文档内容
            steps = self.chain_config.get("steps", [])
            variables = self.chain_config.get("variables", {})
            
            # 合并环境变量到variables
            env = self.chain_config.get("environment", {})
            variables["environment"] = env
            
            for idx, step in enumerate(steps, 1):
                logger.info(f"执行步骤 {idx}/{len(steps)}: {step.get('name', '')}")
                
                # 执行步骤
                step_result = self.executor.execute_step(step, variables)
                
                # 截图
                screenshot_path = None
                try:
                    screenshot_path = self.screenshot_mgr.capture(
                        self.executor.driver,
                        step.get("name", f"step_{idx}"),
                        idx
                    )
                    logger.info(f"截图已保存: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"截图失败: {e}")
                
                # 添加到Word文档
                WordTemplates.add_step(doc, step_result, idx, screenshot_path)
                
                # 如果步骤执行失败，记录警告
                if step_result["status"] == "failed":
                    logger.warning(f"步骤 {idx} 执行失败: {step_result.get('actual', '')}")
            
            # 6. 保存文档
            safe_name = self._sanitize_filename(chain_name)
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{safe_name}_{timestamp}.docx"
            output_path = os.path.join(self.output_dir, filename)
            
            WordTemplates.save_document(doc, output_path)
            logger.info(f"文档已生成: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"文档生成失败: {e}", exc_info=True)
            raise
        finally:
            # 关闭浏览器
            self.executor.quit_driver()
    
    def _load_config(self, config_path):
        """
        加载YAML配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            dict: 配置字典
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ValueError("配置文件格式错误，应为YAML字典格式")
        
        # 验证必需字段
        required_fields = ["chain_name", "environment", "steps"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"配置文件缺少必需字段: {field}")
        
        return config
    
    def _sanitize_filename(self, name):
        """
        清理文件名，移除非法字符
        
        Args:
            name: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        import re
        # 移除或替换非法字符
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # 移除前后空白
        name = name.strip()
        # 限制长度
        if len(name) > 50:
            name = name[:50]
        return name
