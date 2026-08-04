"""
可复用 UI 组件模块
封装页面中可被多个页面共享的组件（如页头、导航栏等）
"""
from ui_automation.pages.components.base_component import BaseComponent
from ui_automation.pages.components.header_component import HeaderComponent
from ui_automation.pages.components.navigation_component import NavigationComponent

__all__ = [
    "BaseComponent",
    "HeaderComponent",
    "NavigationComponent",
]
