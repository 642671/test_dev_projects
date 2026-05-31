"""
ui_automation/pages 包
页面对象层统一入口，导出所有重要类便于外部导入

目录结构：
├── base_page.py          - 页面基类（核心元素操作 + Helpers 集成）
├── example_page.py       - 旧版示例（向后兼容）
├── locators/             - 定位器集中管理
│   ├── common_locators.py
│   ├── login_page_locators.py
│   └── dashboard_page_locators.py
├── components/           - 可复用 UI 组件
│   ├── base_component.py
│   ├── header_component.py
│   └── navigation_component.py
├── helpers/              - 辅助工具
│   ├── wait_helpers.py
│   ├── action_helpers.py
│   └── validation_helpers.py
└── pages/                - 业务页面对象（新结构）
    ├── login_page.py
    └── dashboard_page.py
"""

# 基类
from ui_automation.pages.base_page import BasePage

# 定位器
from ui_automation.pages.locators.common_locators import CommonLocators
from ui_automation.pages.locators.login_page_locators import LoginPageLocators
from ui_automation.pages.locators.dashboard_page_locators import DashboardPageLocators

# 组件
from ui_automation.pages.components.base_component import BaseComponent
from ui_automation.pages.components.header_component import HeaderComponent
from ui_automation.pages.components.navigation_component import NavigationComponent

# 辅助工具
from ui_automation.pages.helpers.wait_helpers import WaitHelpers
from ui_automation.pages.helpers.action_helpers import ActionHelpers
from ui_automation.pages.helpers.validation_helpers import ValidationHelpers

# 业务页面（新结构）
from ui_automation.pages.pages.login_page import LoginPage
from ui_automation.pages.pages.dashboard_page import DashboardPage

__all__ = [
    # 基类
    "BasePage",
    # 定位器
    "CommonLocators",
    "LoginPageLocators",
    "DashboardPageLocators",
    # 组件
    "BaseComponent",
    "HeaderComponent",
    "NavigationComponent",
    # 辅助工具
    "WaitHelpers",
    "ActionHelpers",
    "ValidationHelpers",
    # 业务页面
    "LoginPage",
    "DashboardPage",
]
