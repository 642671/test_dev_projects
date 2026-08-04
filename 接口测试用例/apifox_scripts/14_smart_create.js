// ============================================================
// POST /v2/disk/smart_test/schedule 后置脚本
// 功能：从请求体中提取 disks 设备路径，反查模块变量中
//       对应的 diskN_device，将响应的 id 写入 diskN_smart_id
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行先清空本次对应的 diskN_smart_id
//   2. 有值就 set，没值就 unset，不残留空字符串
//   3. 变量命名与磁盘列表接口一致：diskN_smart_id
// ============================================================

const res = pm.response.json();
const data = res.data || res;

function setOrUnset(key, val) {
    if (val === undefined || val === null || val === '' || Number.isNaN(val)) {
        pm.moduleVariables.unset(key);
    } else {
        pm.moduleVariables.set(key, val);
    }
}

// 0. 从请求体中提取 disks 设备路径 → 反查索引 → 先清空
let reqDevice = '';
if (pm.request.body) {
    try {
        const body = JSON.parse(pm.request.body.raw);
        reqDevice = (body.disks || '').trim();
    } catch (e) { /* 请求体非 JSON，忽略 */ }
}

if (!reqDevice) {
    console.warn('未从请求体提取到 disks 参数，跳过变量写入');
}

let diskIndex = null;
if (reqDevice) {
    const allVars = pm.moduleVariables.toObject();
    for (const [key, value] of Object.entries(allVars)) {
        const match = key.match(/^disk(\d+)_device$/);
        if (match && String(value).trim() === reqDevice) {
            diskIndex = parseInt(match[1], 10);
            break;
        }
    }
}

if (diskIndex !== null) {
    pm.moduleVariables.unset(`disk${diskIndex}_smart_id`);
    console.log(`已清空 disk${diskIndex}_smart_id（准备写入新值）`);
} else {
    console.warn(`未在模块变量中找到 device=${reqDevice} 对应的 diskN_device`);
}

// 1. 响应结构校验
pm.test('响应包含 id', () => {
    pm.expect(data).to.have.property('id');
});

// 2. 写入 diskN_smart_id（创建任务后获得的新 ID）
if (diskIndex !== null) {
    setOrUnset(`disk${diskIndex}_smart_id`, data.id);
    console.log(`disk${diskIndex}_smart_id = ${data.id}`);
}

// 3. 调试输出
const updatedVars = pm.moduleVariables.toObject();
const smartVars = Object.keys(updatedVars)
    .filter(k => /^disk\d+_smart_id$/.test(k))
    .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]));

console.log('========== diskN_smart_id 变量明细 ==========');
console.log(smartVars.length ? smartVars.map(k => `${k} = ${updatedVars[k]}`).join('\n') : '(无)');
console.log('SMART 任务 ID 已同步到模块变量。');
