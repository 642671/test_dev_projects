// ======================================
// 超管用户登录接口后置脚本
// 功能：
// 1. 获取登录返回的 Cookie
// 2. 获取 X-Csrf-Token
// 3. 获取当前用户名
// 4. 自动拼接完整 Cookie
// 5. 保存到环境变量，供后续接口直接使用
// ======================================

// 获取变量
const tmsessname = pm.variables.get("TMSESSNAME");
const tosCurrentUsername = pm.variables.get("tos_current_username");
const csrfToken = pm.variables.get("X-Csrf-Token");

// 输出日志，方便调试
console.log("========== 超管登录信息 ==========");
console.log("TMSESSNAME:", tmsessname);
console.log("tos_current_username:", tosCurrentUsername);
console.log("X-Csrf-Token:", csrfToken);

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

console.log("完整 Cookie：");
console.log(fullCookie);

// ======================
// 保存环境变量
// ======================

// 保存 X-Csrf-Token
if (csrfToken) {
    pm.environment.set("X-Csrf-Token", csrfToken);
}

// 保存 Cookie
pm.environment.set("Cookie", fullCookie);

// 调试输出
console.log("========== 已保存环境变量 ==========");
console.log("Cookie =", pm.environment.get("Cookie"));
console.log("X-Csrf-Token =", pm.environment.get("X-Csrf-Token"));

// ======================
// 登出会话复用检测
// ======================

const prevCookie = pm.environment.get("expired_Cookie");
if (prevCookie) {
    if (prevCookie === fullCookie) {
        console.warn("⚠️ 重新登录 Cookie 与 expired_Cookie 完全相同！会话被复用");
        // 逐段拆解，定位未变的成分
        const prevMap = Object.fromEntries(prevCookie.split("; ").map(s => s.split(/=(.*)/s)));
        const currMap = Object.fromEntries(fullCookie.split("; ").map(s => s.split(/=(.*)/s)));
        const allKeys = new Set([...Object.keys(prevMap), ...Object.keys(currMap)]);
        for (const k of allKeys) {
            const p = prevMap[k] ?? "(无)";
            const c = currMap[k] ?? "(无)";
            console.warn(`  ${p === c ? "✓" : "✗"} ${k}: 旧=${p} 新=${c}`);
        }
    } else {
        console.log("✓ Cookie 已轮换，与 expired_Cookie 不同");
    }
} else {
    console.log("（未检测到 expired_Cookie，首次运行或未执行过登出）");
}

// ======================
// 生成 wrong_X-Csrf-Token（token 不一致场景）
// ======================

if (csrfToken) {
    // 修改第 10、30、50 位 hex 字符，生成与当前 token 不同的"不一致"token
    const hexNext = { "0":"1","1":"2","2":"3","3":"4","4":"5","5":"6","6":"7","7":"8","8":"9","9":"a","a":"b","b":"c","c":"d","d":"e","e":"f","f":"0" };
    let wrongToken = csrfToken.split("");
    [10, 30, 50].forEach(pos => {
        if (pos < wrongToken.length) {
            wrongToken[pos] = hexNext[wrongToken[pos]] || "0";
        }
    });
    pm.environment.set("wrong_X-Csrf-Token", wrongToken.join(""));
    console.log("wrong_X-Csrf-Token =", pm.environment.get("wrong_X-Csrf-Token"));
} else {
    console.warn("警告：未读取到 X-Csrf-Token，wrong_X-Csrf-Token 未更新");
}
