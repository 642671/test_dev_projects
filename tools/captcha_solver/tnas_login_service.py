"""
TNAS 登录 HTTP 服务
功能：通过 Selenium 自动登录 TNAS，自动处理滑动验证码，返回 Cookie。
供 Apifox 前置脚本通过 pm.sendRequest 调用。

启动方式：python tnas_login_service.py
默认端口：8765
"""

import json
import subprocess
import time
import threading
import traceback
from flask import Flask, request, jsonify

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ===================== 配置 =====================
TNAS_BASE_URL = "http://192.168.64.8:8181"
SERVICE_PORT = 8765
LOGIN_TIMEOUT = 30  # 登录总超时（秒）

app = Flask(__name__)


def create_driver():
    """创建 Chrome WebDriver 实例"""
    options = webdriver.ChromeOptions()
    # 注意：滑块验证码通常需要非 headless 模式，否则可能被检测
    # 如果你的环境支持，可启用 headless=new（Chrome 112+）
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExcludeSwitches", True)

    driver = webdriver.Chrome(options=options)
    # 隐藏 webdriver 特征
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        },
    )
    return driver


def find_slider_element(driver, timeout=5):
    """查找页面上的滑块元素（尝试多种选择器）"""
    selectors = [
        # 常见滑块验证码组件的选择器
        (By.CSS_SELECTOR, ".slider-btn"),
        (By.CSS_SELECTOR, ".slide-btn"),
        (By.CSS_SELECTOR, ".captcha-slider .slider"),
        (By.CSS_SELECTOR, ".slider-trigger"),
        (By.CSS_SELECTOR, "[class*='slider']"),
        (By.CSS_SELECTOR, "[class*='slide']"),
        (By.CSS_SELECTOR, ".drag-btn"),
        (By.CSS_SELECTOR, ".verify-btn"),
        # 更通用的：可拖动的元素
        (By.CSS_SELECTOR, ".slider-trigger, .slide-btn, .drag-btn, [class*='slide']"),
    ]
    for by, selector in selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                if elem.is_displayed() and elem.size["width"] > 20:
                    return elem
        except Exception:
            continue
    return None


def find_slider_track(driver, timeout=5):
    """查找滑块轨道"""
    selectors = [
        (By.CSS_SELECTOR, ".slider-track"),
        (By.CSS_SELECTOR, ".slide-track"),
        (By.CSS_SELECTOR, ".captcha-slider .track"),
        (By.CSS_SELECTOR, "[class*='slider-track']"),
        (By.CSS_SELECTOR, "[class*='slide-track']"),
        (By.CSS_SELECTOR, ".drag-track"),
    ]
    for by, selector in selectors:
        try:
            elem = driver.find_element(by, selector)
            if elem.is_displayed():
                return elem
        except Exception:
            continue
    return None


def find_background_image(driver, timeout=5):
    """查找验证码背景图片元素"""
    selectors = [
        (By.CSS_SELECTOR, ".captcha-bg-img"),
        (By.CSS_SELECTOR, ".slider-bg"),
        (By.CSS_SELECTOR, ".captcha-img img"),
        (By.CSS_SELECTOR, "[class*='captcha'] img"),
        (By.CSS_SELECTOR, "[class*='slide'] img:first-child"),
    ]
    for by, selector in selectors:
        try:
            elem = driver.find_element(by, selector)
            if elem.is_displayed():
                return elem
        except Exception:
            continue
    return None


def extract_captcha_data_from_network(driver):
    """
    通过 JS 从页面中提取验证码数据。
    TNAS 前端可能已将 captcha 数据存储在某个全局变量或 DOM 属性中。
    尝试多种方式获取 tile_x 和 captcha_key。
    """
    # 尝试从已存储的全局变量获取
    scripts = [
        "return window.__captcha_data__;",
        "return window.captchaData;",
        "return window.captcha;",
        "return window.__SLIDE_DATA__;",
    ]
    for script in scripts:
        try:
            result = driver.execute_script(script)
            if result and isinstance(result, dict) and "tile_x" in result:
                return result
        except Exception:
            continue

    # 尝试从 DOM 元素属性中获取
    try:
        captcha_container = driver.find_element(By.CSS_SELECTOR, "[class*='captcha'], [class*='slider']")
        data_str = captcha_container.get_attribute("data-captcha")
        if data_str:
            return json.loads(data_str)
    except Exception:
        pass

    return None


def compute_drag_distance(driver, captcha_data):
    """
    根据 captcha_data 中的 tile_x/tile_y 计算滑块需要拖动的距离。

    captcha_data 预期结构：
    {
        "captcha_key": "...",
        "tile_x": 19,
        "tile_y": 66,
        "tile_width": 61,
        "tile_height": 61
    }

    计算逻辑：
    1. 找到背景图片元素，获取其在页面中的实际显示宽度
    2. 获取背景图片的自然宽度（通过 JS）
    3. drag_distance = tile_x * (display_width / natural_width)
    """
    tile_x = captcha_data.get("tile_x", 0)

    # 尝试找到背景图片元素
    bg_img = find_background_image(driver)
    if bg_img:
        display_width = bg_img.size["width"]
        natural_width = driver.execute_script(
            "return arguments[0].naturalWidth;", bg_img
        )
        if natural_width and natural_width > 0:
            ratio = display_width / natural_width
            drag_distance = tile_x * ratio
            print(f"[计算] tile_x={tile_x}, natural_width={natural_width}, "
                  f"display_width={display_width}, ratio={ratio:.4f}, "
                  f"drag_distance={drag_distance:.1f}")
            return drag_distance

    # 兜底：尝试查找滑块轨道宽度来估算
    track = find_slider_track(driver)
    if track:
        track_width = track.size["width"]
        # 假设背景图自然宽度为 300px（常见值）
        estimated_natural_width = 300
        drag_distance = tile_x * (track_width / estimated_natural_width)
        print(f"[估算] tile_x={tile_x}, track_width={track_width}, "
              f"drag_distance={drag_distance:.1f}")
        return drag_distance

    # 最终兜底：直接使用 tile_x（某些实现中 tile_x 即像素值）
    print(f"[兜底] 直接使用 tile_x={tile_x}")
    return tile_x


def perform_slide(driver, captcha_data, max_attempts=3):
    """
    执行滑块拖动操作。
    返回 (success, point_str)  — point_str 如 "124,61"
    """
    import random

    for attempt in range(max_attempts):
        print(f"[滑块] 第 {attempt + 1}/{max_attempts} 次尝试...")

        # 重新查找滑块元素（可能在 DOM 刷新后需要重新获取）
        time.sleep(1)
        slider = find_slider_element(driver)
        if not slider:
            print("[滑块] 未找到滑块元素，尝试刷新页面后查找...")
            # 尝试通过通用选择器
            try:
                slider = driver.find_element(
                    By.CSS_SELECTOR,
                    "[class*='slider-btn'], [class*='slide-btn'], "
                    "[class*='drag'], .verify-btn, [class*='slider']"
                )
            except NoSuchElementException:
                pass

        if not slider:
            print("[滑块] 仍然找不到滑块元素")
            # 尝试截图调试
            try:
                driver.save_screenshot(f"d:/test_dev_projects/tools/captcha_solver/debug_no_slider_{attempt}.png")
            except Exception:
                pass
            return False, None

        # 计算拖动距离
        drag_distance = compute_drag_distance(driver, captcha_data)

        # 模拟人类拖动：先加速再减速，带微小随机偏移
        print(f"[滑块] 拖动距离: {drag_distance:.1f}px")

        action = ActionChains(driver)
        action.click_and_hold(slider)

        # 分段移动模拟人类轨迹
        steps = 10
        for i in range(steps):
            # 使用缓动函数：先快后慢
            progress = (i + 1) / steps
            # ease-out 效果
            eased = 1 - (1 - progress) ** 2
            step_distance = drag_distance * eased - sum(
                drag_distance * (1 - (1 - (j / steps)) ** 2)
                for j in range(i)
            )
            # 添加微小 Y 轴偏移模拟人类不精确性
            y_offset = random.uniform(-1, 2)
            action.move_by_offset(step_distance, y_offset)
            action.pause(0.01 + random.uniform(0, 0.02))

        action.pause(0.3)  # 停留一下再松开
        action.release()
        action.perform()

        # 等待验证结果
        time.sleep(2)

        # 检查是否验证成功（滑块变为绿色/出现成功标志等）
        try:
            # 常见成功标志
            success_indicators = [
                (By.CSS_SELECTOR, ".slider-success"),
                (By.CSS_SELECTOR, ".slide-success"),
                (By.CSS_SELECTOR, ".verify-success"),
                (By.CSS_SELECTOR, "[class*='success']"),
                (By.CSS_SELECTOR, ".captcha-ok"),
            ]
            for by, sel in success_indicators:
                try:
                    elem = driver.find_element(by, sel)
                    if elem.is_displayed():
                        print("[滑块] 验证成功！")
                        # 返回 point：需要知道实际发送的 point 值
                        # point 通常格式为 "x,y"，x=drag_distance, y=0 或 tile_y
                        point_str = f"{int(drag_distance)},0"
                        return True, point_str
                except NoSuchElementException:
                    continue
        except Exception:
            pass

        # 检查滑块是否仍可见（如果不可见，可能验证已通过）
        try:
            if not slider.is_displayed():
                print("[滑块] 滑块已消失，可能验证通过")
                point_str = f"{int(drag_distance)},0"
                return True, point_str
        except Exception:
            print("[滑块] 滑块状态无法判断，假定失败")
            pass

        print(f"[滑块] 第 {attempt + 1} 次尝试未检测到成功标志")

    return False, None


def login_to_tnas(username, password):
    """
    使用 Selenium 登录 TNAS，自动处理滑动验证码。
    返回 {"success": bool, "cookies": {...}, "error": str}
    """
    driver = create_driver()
    result = {"success": False, "cookies": {}, "error": None}

    try:
        # ========== 第一步：打开登录页 ==========
        print(f"[登录] 打开 TNAS: {TNAS_BASE_URL}")
        driver.get(f"{TNAS_BASE_URL}/#/")
        time.sleep(3)

        # ========== 第一步：输入用户名 ==========
        print("[登录] 输入用户名...")
        username_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder='用户名']")
            )
        )
        username_input.clear()
        username_input.send_keys(username)

        # 点击下一步
        next_btn = driver.find_element(By.CSS_SELECTOR, "i.iconfont.iconright")
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(2)

        # ========== 第二步：输入密码 ==========
        print("[登录] 输入密码...")
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder='密码']")
            )
        )
        password_input.clear()
        password_input.send_keys(password)

        # 取消保持登录（可选）
        try:
            keep_login = driver.find_element(By.CSS_SELECTOR, "input.input_check")
            if keep_login.is_selected():
                keep_login.click()
        except Exception:
            pass

        # ========== 点击登录 ==========
        login_btn = driver.find_elements(By.CSS_SELECTOR, "i.iconfont.iconright")[-1]
        driver.execute_script("arguments[0].click();", login_btn)

        # ========== 等待登录结果 ==========
        print("[登录] 等待登录结果...")
        start_time = time.time()
        captcha_handled = False
        captcha_retry_count = 0
        MAX_CAPTCHA_RETRIES = 3

        while time.time() - start_time < LOGIN_TIMEOUT:
            current_url = driver.current_url

            # 检查是否登录成功
            if "desktop" in current_url:
                print("[登录] 登录成功！")
                break

            # 检查是否有密码错误提示（非验证码情况）
            try:
                error_msg = driver.find_element(By.CSS_SELECTOR, ".error-msg, .el-message--error")
                if error_msg.is_displayed():
                    text = error_msg.text.strip()
                    if "密码" in text or "password" in text.lower():
                        result["error"] = f"密码错误: {text}"
                        print(f"[登录] {result['error']}")
                        return result
            except NoSuchElementException:
                pass

            # 检查是否触发了验证码
            if not captcha_handled:
                slider = find_slider_element(driver, timeout=1)
                if slider:
                    captcha_retry_count += 1
                    print(f"[登录] 检测到滑块验证码（第{captcha_retry_count}次）")

                    if captcha_retry_count > MAX_CAPTCHA_RETRIES:
                        result["error"] = "验证码重试次数超限"
                        return result

                    # 尝试获取 captcha 数据
                    captcha_data = extract_captcha_data_from_network(driver)
                    if not captcha_data:
                        # 兜底：使用 JS 从页面中搜索 captcha 数据
                        print("[登录] 无法从全局变量获取 captcha 数据，尝试其他方式...")
                        # 如果找不到 captcha_data，尝试按经验值滑动
                        captcha_data = {"tile_x": 50, "tile_y": 60}

                    # 执行滑块操作
                    slide_success, _ = perform_slide(driver, captcha_data)

                    if slide_success:
                        # 滑块验证通过后，重新点击登录
                        print("[登录] 滑块验证完成，重新点击登录...")
                        time.sleep(1)
                        try:
                            login_btn = driver.find_elements(
                                By.CSS_SELECTOR, "i.iconfont.iconright"
                            )[-1]
                            driver.execute_script(
                                "arguments[0].click();", login_btn
                            )
                        except Exception:
                            pass
                        captcha_handled = True
                        # 重置超时计时
                        start_time = time.time()
                        time.sleep(2)
                        continue
                    else:
                        print("[登录] 滑块验证失败，等待重试...")
                        time.sleep(1)
                        continue

            time.sleep(1)

        # ========== 检查最终状态 ==========
        if "desktop" not in driver.current_url:
            result["error"] = f"登录超时或失败，当前URL: {driver.current_url}"
            try:
                driver.save_screenshot(
                    "d:/test_dev_projects/tools/captcha_solver/debug_login_fail.png"
                )
            except Exception:
                pass
            return result

        # ========== 提取 Cookie ==========
        print("[登录] 提取 Cookie...")
        cookies = driver.get_cookies()
        result["success"] = True
        for c in cookies:
            result["cookies"][c["name"]] = c["value"]

        # 特别标注关键 Cookie
        tmsessname = result["cookies"].get("TMSESSNAME", "")
        csrf_token = result["cookies"].get("X-Csrf-Token", "")
        print(f"[登录] TMSESSNAME: {tmsessname[:20]}...")
        print(f"[登录] X-Csrf-Token: {csrf_token[:20]}...")

        return result

    except Exception as e:
        result["error"] = f"登录异常: {str(e)}\n{traceback.format_exc()}"
        print(f"[登录] {result['error']}")
        try:
            driver.save_screenshot(
                "d:/test_dev_projects/tools/captcha_solver/debug_exception.png"
            )
        except Exception:
            pass
        return result
    finally:
        driver.quit()


# ===================== Flask API =====================


@app.route("/login", methods=["POST"])
def api_login():
    """
    POST /login
    Body: {"username": "test", "password": "Admin123", "reset_first": true}

    reset_first: 是否先清除登录失败计数再登录（默认 true，推荐开启避免验证码）
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "test")
    password = data.get("password", "Admin123")
    reset_first = data.get("reset_first", True)  # 默认自动重置

    print(f"\n{'='*50}")
    print(f"[API] 收到登录请求: user={username}, reset_first={reset_first}")
    print(f"{'='*50}")

    # 登录前先重置失败计数器，避免触发验证码
    if reset_first:
        print("[API] 登录前先清除失败计数器...")
        try:
            subprocess.run(
                ["ssh", "tnas", "sudo", "rm", "-f", "/etc/sysconfig/Records"],
                capture_output=True,
                timeout=10,
            )
            print("[API] 失败计数器已清除")
        except Exception as e:
            print(f"[API] 清除计数器警告（非致命）: {e}")

    result = login_to_tnas(username, password)

    if not result["success"]:
        return jsonify({"success": False, "error": result["error"]}), 500

    cookies = result["cookies"]
    tmsessname = cookies.get("TMSESSNAME", "")
    csrf_token = cookies.get("X-Csrf-Token", "")
    tos_username = cookies.get("tos_current_username", username)

    # 拼接完整 Cookie 字符串（与 Apifox 脚本中格式一致）
    cookie_parts = []
    if csrf_token:
        cookie_parts.append(f"X-Csrf-Token={csrf_token}")
    if tmsessname:
        cookie_parts.append(f"TMSESSNAME={tmsessname}")
    if tos_username:
        cookie_parts.append(f"tos_current_username={tos_username}")
        cookie_parts.append(f"userName={tos_username}")
    cookie_parts.append("loginStatus=true")
    full_cookie = "; ".join(cookie_parts)

    return jsonify(
        {
            "success": True,
            "TMSESSNAME": tmsessname,
            "X-Csrf-Token": csrf_token,
            "tos_current_username": tos_username,
            "full_cookie": full_cookie,
            "all_cookies": cookies,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "TNAS Login Service"})


@app.route("/reset-captcha", methods=["POST"])
def reset_captcha():
    """
    POST /reset-captcha
    通过 SSH 清除 NAS 上的 /etc/sysconfig/Records 文件，
    重置登录失败计数器，从而避免触发滑动验证码。

    依赖：用户已配置 ssh tnas 免密登录（~/.ssh/config 中 Host tnas）
    返回：{"success": true, "message": "..."}
    """
    print("\n[重置] 通过 SSH 清除登录失败计数...")
    try:
        result = subprocess.run(
            ["ssh", "tnas", "sudo", "rm", "-f", "/etc/sysconfig/Records"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            print("[重置] 成功清除 /etc/sysconfig/Records")
            return jsonify({
                "success": True,
                "message": "已重置登录失败计数器，验证码已解除",
            })
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            print(f"[重置] SSH 失败 (exit={result.returncode}): {error_msg}")
            return jsonify({
                "success": False,
                "error": f"SSH 命令执行失败: {error_msg}",
            }), 500
    except subprocess.TimeoutExpired:
        print("[重置] SSH 连接超时")
        return jsonify({
            "success": False,
            "error": "SSH 连接超时，请检查 NAS 是否可达 (ssh tnas)",
        }), 500
    except FileNotFoundError:
        print("[重置] 未找到 ssh 命令")
        return jsonify({
            "success": False,
            "error": "未找到 ssh 命令，请确保已安装 OpenSSH 客户端",
        }), 500
    except Exception as e:
        print(f"[重置] 异常: {e}")
        return jsonify({
            "success": False,
            "error": f"执行异常: {str(e)}",
        }), 500


if __name__ == "__main__":
    print(f"TNAS 登录服务启动中...")
    print(f"端口: {SERVICE_PORT}")
    print(f"TNAS 地址: {TNAS_BASE_URL}")
    print(f"\n调用示例:")
    print(f'  POST http://localhost:{SERVICE_PORT}/login')
    print(f'  Body: {{"username": "test", "password": "Admin123"}}')
    print()
    app.run(host="0.0.0.0", port=SERVICE_PORT, debug=False)
