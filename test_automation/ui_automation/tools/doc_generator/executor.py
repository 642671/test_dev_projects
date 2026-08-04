"""
UI操作执行器

负责驱动UI操作执行，复用现有POM架构的页面对象
"""

import importlib
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Executor:
    """UI操作执行器"""
    
    def __init__(self, driver=None, headless=False):
        """
        初始化执行器
        
        Args:
            driver: 已有的WebDriver实例（可选）
            headless: 是否使用无头模式
        """
        self.driver = driver
        self.headless = headless
        self.page_instances = {}
    
    def init_driver(self):
        """初始化WebDriver"""
        if self.driver is not None:
            return
        
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # 常用配置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(30)
    
    def quit_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def execute_step(self, step_config, variables=None):
        """
        执行单个步骤
        
        Args:
            step_config: 步骤配置字典，包含：
                - name: 步骤名称
                - page: 页面对象类名（如 "TosLoginPage"）
                - action: 要执行的方法名（如 "input_username"）
                - args: 方法参数列表（可选）
                - expected: 预期结果描述
            variables: 变量字典，用于替换 ${variable} 占位符
            
        Returns:
            dict: 执行结果，包含：
                - name: 步骤名称
                - description: 操作描述
                - input_data: 输入数据
                - expected: 预期结果
                - actual: 实际结果
                - status: 执行状态（success/failed）
        """
        if variables is None:
            variables = {}
        
        page_class_name = step_config.get("page", "")
        action_name = step_config.get("action", "")
        args = step_config.get("args", [])
        
        # 解析参数中的变量
        resolved_args = self._resolve_args(args, variables)
        
        try:
            # 获取页面对象
            page_obj = self._get_page(page_class_name)
            
            # 获取要执行的方法
            action_method = getattr(page_obj, action_name, None)
            if action_method is None:
                raise AttributeError(f"页面对象 {page_class_name} 中没有方法 {action_name}")
            
            # 执行操作
            if resolved_args:
                action_method(*resolved_args)
            else:
                action_method()
            
            # 等待（如果配置了）
            wait_after = step_config.get("wait_after", 0)
            if wait_after > 0:
                time.sleep(wait_after)
            
            # 格式化输入数据
            input_data = self._format_input_data(resolved_args)
            
            return {
                "name": step_config.get("name", ""),
                "description": step_config.get("description", ""),
                "input_data": input_data,
                "expected": step_config.get("expected", ""),
                "actual": "操作执行成功",
                "status": "success"
            }
            
        except Exception as e:
            # 执行失败
            input_data = self._format_input_data(resolved_args)
            return {
                "name": step_config.get("name", ""),
                "description": step_config.get("description", ""),
                "input_data": input_data,
                "expected": step_config.get("expected", ""),
                "actual": f"执行失败: {str(e)}",
                "status": "failed"
            }
    
    def _get_page(self, page_class_name):
        """
        动态获取页面对象实例
        
        Args:
            page_class_name: 页面对象类名（如 "TosLoginPage"）
            
        Returns:
            页面对象实例
        """
        if page_class_name not in self.page_instances:
            # 将 PascalCase 转换为 snake_case
            # TosLoginPage -> tos_login_page
            module_name = self._pascal_to_snake(page_class_name)
            
            # 动态导入模块
            module_path = f"ui_automation.pages.pages.{module_name}"
            try:
                module = importlib.import_module(module_path)
                page_class = getattr(module, page_class_name)
                self.page_instances[page_class_name] = page_class(self.driver)
            except ImportError as e:
                raise ImportError(f"无法导入页面对象模块 {module_path}: {e}")
            except AttributeError as e:
                raise AttributeError(f"模块 {module_path} 中没有类 {page_class_name}: {e}")
        
        return self.page_instances[page_class_name]
    
    def _resolve_args(self, args, variables):
        """
        解析参数中的变量占位符
        
        Args:
            args: 参数列表
            variables: 变量字典
            
        Returns:
            list: 解析后的参数列表
        """
        resolved = []
        for arg in args:
            if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                # 提取变量名
                var_name = arg[2:-1]
                
                # 支持嵌套变量（如 environment.url）
                if "." in var_name:
                    parts = var_name.split(".")
                    value = variables
                    for part in parts:
                        if isinstance(value, dict):
                            value = value.get(part, arg)
                        else:
                            value = arg
                            break
                    resolved.append(value)
                else:
                    # 简单变量
                    resolved.append(variables.get(var_name, arg))
            else:
                resolved.append(arg)
        
        return resolved
    
    def _format_input_data(self, args):
        """
        格式化输入数据用于显示
        
        Args:
            args: 参数列表
            
        Returns:
            str: 格式化后的输入数据
        """
        if not args:
            return "无"
        
        # 过滤掉 None 和空字符串
        valid_args = [str(arg) for arg in args if arg is not None and str(arg).strip()]
        
        if not valid_args:
            return "无"
        
        return ", ".join(valid_args)
    
    def _pascal_to_snake(self, name):
        """
        将 PascalCase 转换为 snake_case
        
        Args:
            name: PascalCase 名称
            
        Returns:
            str: snake_case 名称
        """
        import re
        # 在大写字母前插入下划线，然后转小写
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()
