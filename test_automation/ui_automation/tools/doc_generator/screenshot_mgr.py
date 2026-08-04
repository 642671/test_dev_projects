"""
截图管理器

管理UI自动化测试过程中的截图，每个测试链路独立文件夹
"""

import os
import re
from datetime import datetime


class ScreenshotMgr:
    """截图管理器"""
    
    def __init__(self, base_dir=None):
        """
        初始化截图管理器
        
        Args:
            base_dir: 截图基础目录，默认为当前文件所在目录下的evidence文件夹
        """
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), "evidence")
        self.base_dir = base_dir
        self.current_chain_dir = None
    
    def init_chain(self, chain_name):
        """
        为当前测试链路创建截图目录
        
        Args:
            chain_name: 测试链路名称
            
        Returns:
            str: 截图目录路径
        """
        safe_name = self._sanitize_filename(chain_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_chain_dir = os.path.join(
            self.base_dir,
            f"{safe_name}_{timestamp}"
        )
        os.makedirs(self.current_chain_dir, exist_ok=True)
        return self.current_chain_dir
    
    def capture(self, driver, step_name, step_index):
        """
        执行截图并保存
        
        Args:
            driver: WebDriver实例
            step_name: 步骤名称
            step_index: 步骤序号
            
        Returns:
            str: 截图文件路径
        """
        if self.current_chain_dir is None:
            raise RuntimeError("请先调用 init_chain() 初始化链路目录")
        
        # 生成文件名：step_01_步骤名称.png
        safe_name = self._sanitize_filename(step_name)
        filename = f"step_{step_index:02d}_{safe_name}.png"
        filepath = os.path.join(self.current_chain_dir, filename)
        
        # 执行截图
        driver.save_screenshot(filepath)
        
        return filepath
    
    def _sanitize_filename(self, name):
        """
        清理文件名，移除非法字符
        
        Args:
            name: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除或替换非法字符
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # 移除前后空白
        name = name.strip()
        # 限制长度
        if len(name) > 50:
            name = name[:50]
        return name
