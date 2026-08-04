// ======================================
// 普通用户登录接口后置脚本
// 功能：
// 1. 获取登录返回的 Cookie
// 2. 获取 X-Csrf-Token
// 3. 获取当前用户名
// 4. 自动拼接完整 Cookie
// 5. 保存到环境变量，供后续接口直接使用
// ======================================

// 获取变量（普通用户，已由 Apifox 后置操作提取）
const tmsessname = pm.variables.get("NormalUser_TMSESSNAME");
const tosCurrentUsername = pm.variables.get("NormalUser_tos_current_username");
const csrfToken = pm.variables.get("X-Csrf-Token");

// 输出日志，方便调试
console.log("========== 普通用户登录信息 ==========");
console.log("NormalUser_TMSESSNAME:", tmsessname);
console.log("NormalUser_tos_current_username:", tosCurrentUsername);
console.log("NormalUser_X-Csrf-Token:", csrfToken);

// 使用数组拼接 Cookie，避免多余分号
const cookieItems = [];

// X-Csrf-Token
if (csrfToken) {
    cookieItems.push(`X-Csrf-Token=${csrfToken}`);
}

// Session
if (tmsessname) {
    cookieItems.push(`TMSESSNAME=${tmsessname}`);
}

// 当前用户名
if (tosCurrentUsername) {
    cookieItems.push(`tos_current_username=${tosCurrentUsername}`);
    cookieItems.push(`userName=${tosCurrentUsername}`);
}

// 登录状态
cookieItems.push("loginStatus=true");

// 拼接完整 Cookie
const fullCookie = cookieItems.join("; ");

console.log("完整 NormalUserCookie：");
console.log(fullCookie);

// ======================
// 保存环境变量（普通用户专用）
// ======================

// 保存 X-Csrf-Token
if (csrfToken) {
    pm.environment.set("NormalUserCsrfToken", csrfToken);
}

// 保存 Cookie
pm.environment.set("NormalUserCookie", fullCookie);

// 调试输出
console.log("========== 已保存环境变量 ==========");
console.log("NormalUserCookie =", pm.environment.get("NormalUserCookie"));
console.log("NormalUserCsrfToken =", pm.environment.get("NormalUserCsrfToken"));
