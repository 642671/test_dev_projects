// ======================================
// 登出接口后置脚本（POST /v2/logout）
// 功能：
// 1. 把登出前 Cookie 存为 expired_Cookie（原始失效凭证）
// 2. 把登出前 X-Csrf-Token 存为 expired_X-Csrf-Token（原始值备份）
// 3. 将原始 token 改 2 位 → 覆盖环境变量 X-Csrf-Token（后续接口自动用错的）
// 4. 在步骤 3 的新值基础上再改 2 位 → 存入 wrong_X-Csrf-Token
// 注意：
//   - 登出后 X-Csrf-Token 不会变化，所以必须手动篡改才能构造"不一致"场景
//   - expired_Cookie 保留原始 Cookie 用于"过期会话"测试
// ======================================

// 读取登出前的有效凭证（当前 environment 里保存的仍是登出前的值）
const currentCookie = pm.environment.get("Cookie");
const currentCsrfToken = pm.environment.get("X-Csrf-Token");

console.log("========== 登出前凭证快照 ==========");
console.log("Cookie:", currentCookie);
console.log("X-Csrf-Token:", currentCsrfToken);

// hex 字符往后推一位的映射表（0→1 → … → f→0）
const hexNext = { "0":"1","1":"2","2":"3","3":"4","4":"5","5":"6","6":"7","7":"8","8":"9","9":"a","a":"b","b":"c","c":"d","d":"e","e":"f","f":"0" };

// ======================
// ① 备份原始凭证
// ======================

if (currentCookie) {
    pm.environment.set("expired_Cookie", currentCookie);
} else {
    console.warn("警告：未读取到 Cookie，expired_Cookie 未更新");
}

if (currentCsrfToken) {
    pm.environment.set("expired_X-Csrf-Token", currentCsrfToken);
} else {
    console.warn("警告：未读取到 X-Csrf-Token，expired_X-Csrf-Token 未更新");
}

// ======================
// ② 篡改 X-Csrf-Token → 覆盖环境变量（后续接口自动用错的）
// ======================

if (currentCsrfToken) {
    // 改第 10、30 位 → 作为新 X-Csrf-Token
    let newToken = currentCsrfToken.split("");
    [10, 30].forEach(pos => {
        if (pos < newToken.length) {
            newToken[pos] = hexNext[newToken[pos]] || "0";
        }
    });
    const newCsrfToken = newToken.join("");
    pm.environment.set("X-Csrf-Token", newCsrfToken);
    console.log("新 X-Csrf-Token（篡改后）:", newCsrfToken);

    // ======================
    // ③ 在新值基础上再改 2 位 → 存入 wrong_X-Csrf-Token
    // ======================

    // 改第 20、40 位（与步骤 ② 不同位置）
    let wrongToken = newCsrfToken.split("");
    [20, 40].forEach(pos => {
        if (pos < wrongToken.length) {
            wrongToken[pos] = hexNext[wrongToken[pos]] || "0";
        }
    });
    pm.environment.set("wrong_X-Csrf-Token", wrongToken.join(""));
} else {
    console.warn("警告：未读取到 X-Csrf-Token，后续变量均未更新");
}

// 调试输出
console.log("========== 已保存变量总览 ==========");
console.log("expired_Cookie         =", pm.environment.get("expired_Cookie"));
console.log("expired_X-Csrf-Token   =", pm.environment.get("expired_X-Csrf-Token"));
console.log("X-Csrf-Token（已覆盖） =", pm.environment.get("X-Csrf-Token"));
console.log("wrong_X-Csrf-Token     =", pm.environment.get("wrong_X-Csrf-Token"));
