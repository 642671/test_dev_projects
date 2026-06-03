"""
TOS 用户设置页面对象
封装用户设置界面的导航、Tab切换、字段验证等操作
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from selenium.webdriver.common.by import By
from ui_automation.pages.base_page import BasePage
from ui_automation.pages.locators.tos_user_settings_locators import TosUserSettingsLocators
from common.logger import get_logger

logger = get_logger("TosUserSettingsPage")


class TosUserSettingsPage(BasePage):
    """TOS 用户设置页面对象"""

    def __init__(self, driver):
        super().__init__(driver)

    # ========== 界面验证 ==========

    def is_settings_loaded(self, timeout=10):
        """验证用户设置界面是否加载完成"""
        try:
            self.wait_for_element_visible(TosUserSettingsLocators.NAV_ACCOUNT, timeout=timeout)
            return True
        except Exception:
            return False

    def get_nav_modules(self):
        """获取左侧导航模块列表"""
        items = self.driver.find_elements(*TosUserSettingsLocators.NAV_ITEMS)
        modules = []
        for item in items:
            if item.is_displayed():
                title_span = item.find_elements(By.CSS_SELECTOR, "span.tab-list-title")
                if title_span:
                    modules.append(title_span[0].text)
        logger.info(f"用户设置左侧导航模块: {modules}")
        return modules

    def get_tab_items(self):
        """获取当前模块的 Tab 标签列表"""
        items = self.driver.find_elements(*TosUserSettingsLocators.TAB_ITEMS)
        tabs = [item.text for item in items if item.is_displayed() and item.text.strip()]
        logger.info(f"当前模块 Tab 标签: {tabs}")
        return tabs

    # ========== 导航操作 ==========

    def click_nav_account(self):
        """点击左侧导航 - 账号"""
        logger.info("点击左侧导航: 账号")
        self.click(TosUserSettingsLocators.NAV_ACCOUNT)
        time.sleep(2)
        return self

    def click_nav_display(self):
        """点击左侧导航 - 显示"""
        logger.info("点击左侧导航: 显示")
        self.click(TosUserSettingsLocators.NAV_DISPLAY)
        time.sleep(2)
        return self

    # ========== Tab 操作 ==========

    def click_tab_user_info(self):
        """点击 Tab: 用户信息"""
        logger.info("点击 Tab: 用户信息")
        self.click(TosUserSettingsLocators.TAB_USER_INFO)
        time.sleep(1)
        return self

    def click_tab_account_security(self):
        """点击 Tab: 账号安全"""
        logger.info("点击 Tab: 账号安全")
        self.click(TosUserSettingsLocators.TAB_ACCOUNT_SECURITY)
        time.sleep(1)
        return self

    def click_tab_other(self):
        """点击 Tab: 其它"""
        logger.info("点击 Tab: 其它")
        self.click(TosUserSettingsLocators.TAB_OTHER)
        time.sleep(1)
        return self

    # ========== 字段验证 ==========

    def is_username_displayed(self):
        """验证用户名 'test' 是否显示"""
        return self.is_element_visible(TosUserSettingsLocators.FIELD_USERNAME, timeout=5)

    def is_role_displayed(self):
        """验证角色 '超级用户' 是否显示"""
        return self.is_element_visible(TosUserSettingsLocators.FIELD_ROLE, timeout=5)

    # ========== 用户信息编辑操作 ==========

    def _get_visible_text_inputs(self):
        """获取用户信息页面中可见的文本输入框列表（排除密码框和下拉框）"""
        all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input.Xinput-input__inner")
        visible_text_inputs = []
        for inp in all_inputs:
            if inp.is_displayed() and inp.get_attribute('type') == 'text':
                visible_text_inputs.append(inp)
        return visible_text_inputs

    def _clear_and_input(self, element, text):
        """
        清空输入框并输入新内容（兼容 Vue 组件）
        使用全选+删除+输入的方式确保 Vue 检测到值变化
        """
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        # 点击激活输入框
        element.click()
        time.sleep(0.2)
        # 全选（Command+A on Mac）然后删除
        ActionChains(self.driver).key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
        time.sleep(0.1)
        ActionChains(self.driver).send_keys(Keys.BACKSPACE).perform()
        time.sleep(0.2)
        # 输入新内容
        element.send_keys(text)
        time.sleep(0.3)

    def input_description(self, text):
        """输入描述字段（第1个可见文本输入框）"""
        logger.info(f"输入描述: {text}")
        inputs = self._get_visible_text_inputs()
        if len(inputs) < 1:
            raise Exception("未找到描述输入框")
        self._clear_and_input(inputs[0], text)
        return self

    def input_email(self, email):
        """输入密保邮箱（第2个可见文本输入框）"""
        logger.info(f"输入密保邮箱: {email}")
        inputs = self._get_visible_text_inputs()
        if len(inputs) < 2:
            raise Exception("未找到密保邮箱输入框")
        self._clear_and_input(inputs[1], email)
        return self

    def input_phone(self, phone):
        """输入电话号码（第3个可见文本输入框）"""
        logger.info(f"输入电话号码: {phone}")
        inputs = self._get_visible_text_inputs()
        if len(inputs) < 3:
            raise Exception("未找到电话号码输入框")
        self._clear_and_input(inputs[2], phone)
        return self

    def click_apply(self):
        """点击应用按钮保存设置（使用 ActionChains 真实点击）"""
        logger.info("点击应用按钮")
        element = self.find_element(TosUserSettingsLocators.APPLY_BUTTON, timeout=10)
        # 必须用 ActionChains 真实点击，JS click 无法触发 Vue 事件
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).click(element).perform()
        # 不加额外等待，让调用方立即检测 toast
        return self

    def is_success_toast_visible(self, timeout=5):
        """
        验证成功提示是否出现（"设置成功！"或"操作成功！"）
        TOS 的 toast 出现后会很快消失，通过检查页面源码来确认
        """
        import time as _time
        end_time = _time.time() + timeout
        while _time.time() < end_time:
            try:
                page_source = self.driver.page_source
                if '设置成功' in page_source or '操作成功' in page_source:
                    logger.info("检测到成功提示（页面源码中）")
                    return True
            except Exception:
                pass
            _time.sleep(0.3)
        
        logger.warning("未检测到成功提示")
        return False

    def edit_user_info(self, description=None, email=None, phone=None):
        """
        编辑用户信息并保存
        :param description: 描述内容（None则不修改）
        :param email: 密保邮箱（None则不修改）
        :param phone: 电话号码（None则不修改）
        :return: self
        """
        logger.info(f"编辑用户信息: 描述='{description}', 邮箱='{email}', 电话='{phone}'")
        if description is not None:
            self.input_description(description)
        if email is not None:
            self.input_email(email)
        if phone is not None:
            self.input_phone(phone)
        
        self.click_apply()
        return self

    # ========== "其它" Tab 操作 ==========

    def get_other_tab_checkboxes(self):
        """获取'其它' Tab 中的所有可见复选框"""
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input.input_check")
        visible = [cb for cb in checkboxes if cb.is_displayed()]
        logger.info(f"'其它' Tab 复选框数量: {len(visible)}")
        return visible

    def check_all_other_checkboxes(self):
        """勾选'其它' Tab 中所有未勾选的复选框"""
        logger.info("勾选'其它' Tab 所有复选框")
        checkboxes = self.get_other_tab_checkboxes()
        for i, cb in enumerate(checkboxes):
            if not cb.is_selected():
                cb.click()
                logger.info(f"  勾选第 {i+1} 个复选框")
                time.sleep(0.3)
        return self

    def uncheck_all_other_checkboxes(self):
        """取消勾选'其它' Tab 中所有已勾选的复选框"""
        logger.info("取消勾选'其它' Tab 所有复选框")
        checkboxes = self.get_other_tab_checkboxes()
        for i, cb in enumerate(checkboxes):
            if cb.is_selected():
                cb.click()
                logger.info(f"  取消勾选第 {i+1} 个复选框")
                time.sleep(0.3)
        return self
