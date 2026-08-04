// ======================================
// 密码验证接口后置脚本（POST /v2/otp/verify_pwd）
// 功能：
// 1. 从响应中提取 X-Curpass-Token
// 2. 修改 base64 字符第 5、15 位 → 存入 wrong_X-Curpass-Token
// 3. 供"token 不一致"负向测试用例使用
// ======================================

// 读取当前环境变量中的 X-Curpass-Token（由验证接口返回后设置）
const curpassToken = pm.environment.get("X-Curpass-Token");

console.log("========== X-Curpass-Token 快照 ==========");
console.log("X-Curpass-Token:", curpassToken);

if (curpassToken) {
    // base64 字符循环映射（A→B → … → /→A）
    const b64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const b64Next = {};
    for (let i = 0; i < b64chars.length; i++) {
        b64Next[b64chars[i]] = b64chars[(i + 1) % b64chars.length];
    }

    // 去掉末尾 = 填充，在有效字符范围内改第 5、15 位
    const padding = curpassToken.match(/=+$/)?.[0] || "";
    let tokenBody = curpassToken.replace(/=+$/, "");
    let charArray = tokenBody.split("");

    [5, 15].forEach(pos => {
        if (pos < charArray.length) {
            charArray[pos] = b64Next[charArray[pos]] || "A";
        }
    });

    const wrongToken = charArray.join("") + padding;
    pm.environment.set("wrong_X-Curpass-Token", wrongToken);

    console.log("wrong_X-Curpass-Token =", wrongToken);
} else {
    console.warn("警告：未读取到 X-Curpass-Token，wrong_X-Curpass-Token 未更新");
}
