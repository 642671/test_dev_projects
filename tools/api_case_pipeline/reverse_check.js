// ============================================================
// 反向完整性对账：Excel每行(除方法错误) → main对应端点是否存在同名用例
// ============================================================
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

const ROOT = path.resolve(__dirname, '..', '..');
const SETTINGS = path.join(ROOT, '.apifox', 'settings.json');
const PROJECT = String(JSON.parse(fs.readFileSync(SETTINGS, 'utf8')).projectId);
const EXCEL = path.join(ROOT, '接口测试用例', '单个接口测试用例', '存储管理单接口测试用例.xlsx');
const ENDPOINTS = path.join(__dirname, 'data', 'endpoints_dump.json');
const OUTPUT = path.join(ROOT, 'temp_scripts', '_reverse_check.json');
const SHEETS = ['概要', '卷', '存储池', '热备盘', '磁盘', '虚拟磁盘', 'HyperCache', 'USB设备'];
const methodErrRe = /错误的请求类型|请求方法错误|方法错误/;

function apifoxJson(cmd) {
    for (let attempt = 1; attempt <= 3; attempt++) {
        try {
            const raw = execSync(cmd, { encoding: 'utf8', maxBuffer: 100 * 1024 * 1024 });
            const cleaned = raw.replace(/^\uFEFF/, '').replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '');
            return JSON.parse(cleaned.slice(cleaned.indexOf('{')));
        } catch (err) {
            const detail = String(err.stdout || '') + String(err.stderr || '') + String(err.message || '');
            if (attempt === 3 || !/502|503|504/.test(detail)) throw err;
            console.log('Apifox临时错误，重试 ' + attempt + '/3');
            Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, attempt * 1000);
        }
    }
}

const eps = JSON.parse(fs.readFileSync(ENDPOINTS, 'utf8'));
const epIdx = new Map(), epByPath = new Map();
for (const e of eps) {
    epIdx.set(e.path + '|' + e.method.toLowerCase(), e);
    if (!epByPath.has(e.path)) epByPath.set(e.path, []);
    epByPath.get(e.path).push(e);
}

const wb = XLSX.readFile(EXCEL);
const rows = [];
const funcEp = new Map();
for (const sn of SHEETS) {
    const ws = wb.Sheets[sn];
    if (!ws) continue;
    const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    for (let i = 1; i < data.length; i++) {
        const r = data[i];
        const func = (r[3] || '').toString().trim();
        const title = (r[8] || '').toString().trim();
        if (!func || !title) continue;
        if (!funcEp.has(sn + '|' + func)) {
            const p = (r[2] || '').toString().trim().split('?')[0].replace(/:\w+$/, '');
            const m = (r[5] || '').toString().trim().toLowerCase();
            let ep = epIdx.get(p + '|' + m);
            if (!ep && epByPath.has(p) && epByPath.get(p).length === 1) ep = epByPath.get(p)[0];
            funcEp.set(sn + '|' + func, ep || null);
        }
        rows.push({ sheet: sn, row: i + 1, func, title, isMethodErr: methodErrRe.test(title) });
    }
}
const total = rows.length;
const methodErrCnt = rows.filter(r => r.isMethodErr).length;
console.log('Excel总用例: ' + total + ' (方法错误类不可导入: ' + methodErrCnt + ')');

// 拉每端点用例名
const epIds = [...new Set([...funcEp.values()].filter(x => x).map(x => x.id))];
const epNames = new Map();
let n = 0;
for (const id of epIds) {
    const j = apifoxJson('apifox test-case list --project ' + PROJECT + ' --endpoint ' + id + ' --page-size 500');
    const arr = Array.isArray(j.data) ? j.data : (j.data.list || []);
    epNames.set(id, arr.map(c => (c.name || '').trim()));
    n++;
    if (n % 30 === 0) console.log('拉取进度: ' + n + '/' + epIds.length);
}

// 对账（同名多行的Excel行需要端点上有同等数量的同名用例吗？先按存在性检查+数量对比）
const missing = [];
const usedCnt = new Map(); // epId|title → excel次数
rows.forEach(r => {
    if (r.isMethodErr) return;
    const ep = funcEp.get(r.sheet + '|' + r.func);
    if (!ep) { missing.push({ ...r, reason: '端点未匹配' }); return; }
    const k = ep.id + '|' + r.title;
    usedCnt.set(k, (usedCnt.get(k) || 0) + 1);
    if (!epNames.get(ep.id).includes(r.title)) missing.push({ ...r, reason: '端点无同名用例', epPath: ep.path });
});

console.log('\n===== 反向对账结果 =====');
console.log('应在main的用例数: ' + (total - methodErrCnt));
console.log('缺失: ' + missing.length);
const bySheet = {};
missing.forEach(m => { bySheet[m.sheet] = (bySheet[m.sheet] || 0) + 1; });
console.log('缺失按Sheet: ' + JSON.stringify(bySheet));
missing.slice(0, 30).forEach(m => console.log('  [' + m.sheet + ' 行' + m.row + '] ' + m.func + ' | ' + m.title.substring(0, 40) + ' | ' + m.reason));
fs.writeFileSync(OUTPUT, JSON.stringify(missing, null, 1), 'utf8');

// main端总数统计
let mainTotal = 0;
epNames.forEach(v => mainTotal += v.length);
console.log('main侧(96接口相关端点)用例总数: ' + mainTotal);
