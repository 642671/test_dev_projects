// ======================================
// Apifox 前置脚本：调用本地 Selenium 服务获取 TNAS 登录 Cookie
// ======================================
// 
// 使用方式：
// 1. 将此脚本放在需要认证的接口的"前置脚本"中
// 2. 确保本地服务已启动：python tools/captcha_solver/tnas_login_service.py
// 3. 脚本会自动检查 Cookie 是否有效，无效则调用服务重新登录
//
// 环境变量依赖（在 Apifox 环境变量中配置）：
//   - captcha_service_url: http://localhost:8765 (默认)
//   - tnas_username: test (默认)
//   - tnas_password: Admin123 (默认)
// ======================================

const SERVICE_URL = pm.variables.get("captcha_service_url") || "http://localhost:8765";
const USERNAME = pm.variables.get("tnas_username") || "test";
const PASSWORD = pm.variables.get("tnas_password") || "Admin123";

// 检查当前环境变量中是否已有有效 Cookie
const currentToken = pm.variables.get("TMSESSNAME");
const currentCsrf = pm.variables.get("X-Csrf-Token");

if (currentToken && currentCsrf && currentToken !== "" && currentCsrf !== "") {
    console.log("[Apifox] 已有有效 Cookie，跳过登录");
    console.log("[Apifox] TMSESSNAME:", currentToken.substring(0, 15) + "...");
} else {
    console.log("[Apifox] Cookie 缺失或为空，调用本地登录服务...");
    console.log("[Apifox] 服务地址:", SERVICE_URL);

    // 调用本地 Selenium 服务
    pm.sendRequest({
        url: SERVICE_URL + "/login",
        method: "POST",
        header: {
            "Content-Type": "application/json"
        },
        body: {
            mode: "raw",
            raw: JSON.stringify({
                username: USERNAME,
                password: PASSWORD
            })
        }
    }, function (err, res) {
        if (err) {
            console.error("[Apifox] 调用登录服务失败:", err);
            console.error("[Apifox] 请确保本地服务已启动: python tools/captcha_solver/tnas_login_service.py");
            return;
        }

        console.log("[Apifox] 服务响应状态:", res.status);

        try {
            const data = res.json();
            
            if (data.success) {
                console.log("[Apifox] 登录成功！");
                
                // 保存到环境变量
                pm.environment.set("TMSESSNAME", data.TMSESSNAME || "");
                pm.environment.set("X-Csrf-Token", data.X-Csrf-Token || "");
                pm.environment.set("tos_current_username", data.tos_current_username || USERNAME);
                pm.environment.set("loginStatus", "true");
                
                // 拼接完整 Cookie（供后续接口使用）
                const cookieParts = [];
                if (data["X-Csrf-Token"]) {
                    cookieParts.push("X-Csrf-Token=" + data["X-Csrf-Token"]);
                }
                if (data.TMSESSNAME) {
                    cookieParts.push("TMSESSNAME=" + data.TMSESSNAME);
                }
                if (data.tos_current_username) {
                    cookieParts.push("tos_current_username=" + data.tos_current_username);
                    cookieParts.push("userName=" + data.tos_current_username);
                }
                cookieParts.push("loginStatus=true");
                const fullCookie = cookieParts.join("; ");
                
                pm.environment.set("full_cookie", fullCookie);
                
                console.log("[Apifox] Cookie 已注入环境变量");
                console.log("[Apifox] TMSESSNAME:", data.TMSESSNAME.substring(0, 15) + "...");
                console.log("[Apifox] X-Csrf-Token:", data["X-Csrf-Token"].substring(0, 15) + "...");
            } else {
                console.error("[Apifox] 登录失败:", data.error);
            }
        } catch (parseErr) {
            console.error("[Apifox] 解析响应失败:", parseErr);
            console.error("[Apifox] 原始响应:", res.text());
        }
    });
}
