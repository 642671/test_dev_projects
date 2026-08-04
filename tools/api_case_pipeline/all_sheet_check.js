// ============================================================
// 全Sheet通用复查：必填列/组内重名/行序回头/通用场景顺序/ID连续/步骤一致性/密码头
// 用法: node _all_sheet_check.js [Sheet名(可选,缺省全部)]
// ============================================================
const XLSX = require('xlsx');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const EXCEL = path.join(ROOT, '接口测试用例', '单个接口测试用例', '存储管理单接口测试用例.xlsx');
const wb = XLSX.readFile(EXCEL);

const SHEETS = process.argv[2] ? [process.argv[2]] : ['概要', '卷', '存储池', '热备盘', '磁盘', '虚拟磁盘', 'HyperCache', 'USB设备'];
const CURPASS_FUNCS = new Set(['移除磁盘', '开始安全擦除', '开始抹除磁盘', '新增系统盘', '删除系统盘', '迁移系统盘', '初始化系统盘']);
const authRe = /未登录|Token\s*失效|CSRF|Csrf|无权限|不相同/;

function genericRank(t) {
    if (/未登录/.test(t)) return 1;
    if (/Token\s*失效/i.test(t)) return 2;
    if (/CSRF|Csrf|不相同/.test(t)) return 3;
    if (/无权限/.test(t)) return 4;
    if (/超时/.test(t)) return 5;
    if (/畸形|版本号错误/.test(t)) return 6;
    if (/错误的请求类型|请求方法错误/.test(t)) return 7;
    return 0;
}

let grandIssues = 0;
for (const sn of SHEETS) {
    const ws = wb.Sheets[sn];
    if (!ws) { console.log('[' + sn + '] Sheet不存在'); continue; }
    const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    const issues = [];
    const seenTitle = new Map();
    const seenFunc = new Set();
    let prevFunc = null, prevRank = 0, rowCnt = 0, idOk = true, scattered = 0;

    for (let i = 1; i < data.length; i++) {
        const r = data[i]; const row = i + 1;
        const c = n => (r[n - 1] || '').toString();
        const c4 = c(4).trim(), c9 = c(9).trim();
        if (!c4) continue;
        rowCnt++;
        const m = c(1).trim().match(/(\d+)$/);
        if (!m || parseInt(m[1]) !== rowCnt) { idOk = false; }
        // 必填列
        if (!c(2).trim()) issues.push(row + ' 所属模块空');
        if (!c(3).trim()) issues.push(row + ' 接口地址空');
        if (!c(5).trim()) issues.push(row + ' 优先级空');
        if (!c(6).trim()) issues.push(row + ' 请求类型空');
        if (!c(7).trim()) issues.push(row + ' 请求头空');
        else if (!c(7).toLowerCase().includes('content-type') && !/缺少\s*Content-Type|不携带\s*Content-Type/i.test(c9)) {
            issues.push(row + ' 请求头缺Content-Type');
        }
        if (!c(8).trim()) issues.push(row + ' 请求参数空');
        if (!c9) issues.push(row + ' 用例标题空');
        if (!c(10).trim()) issues.push(row + ' 前置条件空');
        if (!c(11).trim()) issues.push(row + ' 操作步骤空');
        // 组内重名
        const tk = c4 + '|' + c9;
        if (seenTitle.has(tk)) issues.push(row + ' 组内重名[' + c4 + '] "' + c9.substring(0, 30) + '" 与行' + seenTitle.get(tk));
        else seenTitle.set(tk, row);
        // 回头
        if (c4 !== prevFunc) {
            if (seenFunc.has(c4)) { scattered++; issues.push(row + ' 功能回头: ' + c4); }
            seenFunc.add(c4); prevFunc = c4; prevRank = 0;
        }
        // 通用场景顺序
        const rank = genericRank(c9);
        if (rank > 0 && prevRank > rank) issues.push(row + ' 通用顺序异常[' + c4 + '] ' + c9.substring(0, 30));
        if (rank > 0) prevRank = rank;
        if (rank === 0 && prevRank > 0) issues.push(row + ' 非通用在通用后[' + c4 + '] ' + c9.substring(0, 30));
        // 密码头（仅磁盘的7个接口）
        if (CURPASS_FUNCS.has(c4) && !authRe.test(c9) && !/curpass/i.test(c(7))) {
            issues.push(row + ' [' + c4 + '] 非认证行缺X-Curpass-Token头');
        }
        // 步骤第1步一致性（跳过方法错误/超时/畸形/版本号）
        if (!/错误的请求类型|请求方法错误|超时|畸形|版本号/.test(c9)) {
            const s1 = c(11).split(/\r?\n/)[0] || '';
            const mm = s1.match(/使用\s+(\S+)\s+请求访问\s+(\S+)/);
            if (mm) {
                if (mm[1].toUpperCase() !== c(6).trim().toUpperCase()) issues.push(row + ' 步1方法(' + mm[1] + ')≠请求类型(' + c(6).trim() + ')');
                const expectedPath = c(3).trim();
                const pathWithEmptyParam = expectedPath.replace(/\{[^}]+\}/g, '');
                const intentionalEmptyPath =
                    mm[2] === pathWithEmptyParam &&
                    /参数为空|缺少.*参数/.test(c9);
                if (mm[2] !== expectedPath && !intentionalEmptyPath) issues.push(row + ' 步1路径≠接口地址');
            }
        }
    }
    grandIssues += issues.length;
    console.log('[' + sn + '] 数据' + rowCnt + '行 接口' + seenFunc.size + ' 回头' + scattered + ' ID连续=' + idOk + ' 问题=' + issues.length);
    issues.slice(0, 15).forEach(x => console.log('    ' + x));
    if (issues.length > 15) console.log('    ...+' + (issues.length - 15));
}
console.log('\n总问题数: ' + grandIssues);
