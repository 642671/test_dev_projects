"""
全局常量定义
集中管理项目中使用的常量值
"""

# === 超时配置（秒）===
DEFAULT_TIMEOUT = 10           # 默认等待超时
SHORT_TIMEOUT = 5              # 短等待
LONG_TIMEOUT = 30              # 长等待
PAGE_LOAD_TIMEOUT = 30         # 页面加载超时
AJAX_TIMEOUT = 15              # AJAX 等待超时

# === 重试配置 ===
MAX_RETRY_ATTEMPTS = 3         # 最大重试次数
RETRY_DELAY = 1                # 重试初始延迟（秒）
RETRY_BACKOFF = 2              # 重试退避倍数

# === 日志配置 ===
LOG_LEVEL = "INFO"             # 日志级别
LOG_RETENTION = "7 days"       # 日志保留时间
LOG_ROTATION = "1 day"         # 日志轮转周期

# === 测试标签 ===
class Markers:
    """pytest 标签常量"""
    SMOKE = "smoke"
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    SANITY = "sanity"
    UI = "ui"
    API = "api"

# === 浏览器配置常量 ===
class BrowserType:
    """浏览器类型"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"

# === 路径常量 ===
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_AUTOMATION_DIR = os.path.join(PROJECT_ROOT, "ui_automation")
EVIDENCE_DIR = os.path.join(UI_AUTOMATION_DIR, "evidence")
SCREENSHOTS_DIR = os.path.join(EVIDENCE_DIR, "screenshots")
PAGE_SOURCES_DIR = os.path.join(EVIDENCE_DIR, "page_sources")
TESTDATA_DIR = os.path.join(UI_AUTOMATION_DIR, "testdata")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

# === 测试用例状态 ===
class TestStatus:
    """测试结果状态"""
    PASS = "通过"
    FAIL = "失败"
    SKIP = "跳过"
    BLOCK = "阻塞"
    NOT_RUN = "未执行"
