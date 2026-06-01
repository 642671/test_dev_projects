"""
TOS 登录页面定位器
两步式登录：第一步用户名 → 第二步密码+保持登录

TOS 使用 Vue.js + 自定义组件，页面无标准 <button> 标签。
"下一步"按钮是一个 <i> 图标元素（右箭头），class 为 iconfont iconright。
"""
from selenium.webdriver.common.by import By


class TosLoginLocators:
    """TOS 登录页面定位器（两步式登录）"""

    # ========== 第一步：用户名 ==========

    # 用户名输入框
    # class: Xinput-input__inner fullWidth, placeholder: 用户名
    USERNAME_INPUT = (By.CSS_SELECTOR, "input.Xinput-input__inner[placeholder='用户名']")

    # 下一步按钮（第一步）— 是一个 <i> 图标（右箭头），不是 <button>
    NEXT_BUTTON_STEP1 = (By.CSS_SELECTOR, "i.iconfont.iconright")

    # ========== 第二步：密码 ==========

    # 密码输入框
    # class: Xinput-input__inner fullWidth, placeholder: 密码
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input.Xinput-input__inner[placeholder='密码']")

    # 保持登录复选框
    # class: input_check
    KEEP_LOGIN_CHECKBOX = (By.CSS_SELECTOR, "input.input_check")

    # 下一步/登录按钮（第二步）— 同样是 <i> 图标
    # 注意：第二步出现后，页面上可能有同一个 iconright 图标
    NEXT_BUTTON_STEP2 = (By.CSS_SELECTOR, "i.iconfont.iconright")

    # ========== 登录成功判断 ==========

    # 方法一：URL 包含 /desktop（最可靠）
    # 登录成功后 URL 会从 /#/ 变为 /#/desktop
    DESKTOP_URL_KEYWORD = "desktop"

    # 方法二：欢迎文字（存在但 displayed=False，不推荐作为主判断）
    WELCOME_TEXT = (By.CSS_SELECTOR, "div.user_name")

    # 方法三：页面标题变为 TNAS
    DESKTOP_TITLE = "TNAS"
