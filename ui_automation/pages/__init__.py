"""
ui_automation/pages 包
页面对象层统一入口，导出所有重要类便于外部导入

目录结构：
├── base_page.py          - 页面基类（核心元素操作 + Helpers 集成）
├── locators/             - 定位器集中管理
│   ├── common_locators.py
│   ├── tos_login_locators.py
│   ├── tos_navbar_locators.py
│   └── tos_desktop_locators.py
├── components/           - 可复用 UI 组件
│   ├── base_component.py
│   ├── header_component.py
│   └── navigation_component.py
├── helpers/              - 辅助工具
│   ├── wait_helpers.py
│   ├── action_helpers.py
│   └── validation_helpers.py
└── pages/                - 业务页面对象
    ├── tos_login_page.py
    ├── tos_navbar_page.py
    └── tos_desktop_page.py
"""

# 基类
from ui_automation.pages.base_page import BasePage

# 定位器
from ui_automation.pages.locators.common_locators import CommonLocators

# 组件
from ui_automation.pages.components.base_component import BaseComponent
from ui_automation.pages.components.header_component import HeaderComponent
from ui_automation.pages.components.navigation_component import NavigationComponent

# 辅助工具
from ui_automation.pages.helpers.wait_helpers import WaitHelpers
from ui_automation.pages.helpers.action_helpers import ActionHelpers
from ui_automation.pages.helpers.validation_helpers import ValidationHelpers

# 业务页面
from ui_automation.pages.pages.tos_login_page import TosLoginPage
from ui_automation.pages.pages.tos_navbar_page import TosNavbarPage
from ui_automation.pages.pages.tos_desktop_page import TosDesktopPage

__all__ = [
    # 基类
    "BasePage",
    # 定位器
    "CommonLocators",
    # 组件
    "BaseComponent",
    "HeaderComponent",
    "NavigationComponent",
    # 辅助工具
    "WaitHelpers",
    "ActionHelpers",
    "ValidationHelpers",
    # 业务页面
    "TosLoginPage",
    "TosNavbarPage",
    "TosDesktopPage",
]
