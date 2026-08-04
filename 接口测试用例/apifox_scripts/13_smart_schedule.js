// ============================================================
// GET /v2/disk/smart_test/schedule 后置脚本
// 功能：遍历 SMART 任务，按 device 反查 diskN 编号，
//       写入 diskN_smart_id，兼容对象/数组/空数组
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

// 0. 清空所有旧的 diskN_smart_id 变量
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^disk\d+_smart_id$/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 统一标准化为数组
let tasks;
if (Array.isArray(data)) {
    tasks = data;
} else if (data && typeof data === 'object') {
    tasks = [data];
} else {
    tasks = [];
}

if (tasks.length === 0) {
    console.log('无 SMART 任务，已清空所有 diskN_smart_id 变量');
    pm.moduleVariables.set('smart_task_count', 0);
    return;
}

// 2. 构建 device → 编号 反查映射
const deviceToIndex = {};
for (const [key, value] of Object.entries(allModuleVars)) {
    const match = key.match(/^disk(\d+)_device$/);
    if (match) {
        const idx = parseInt(match[1], 10);
        const devPath = String(value).trim();
        if (devPath) deviceToIndex[devPath] = idx;
    }
}

// 3. 遍历写入 diskN_smart_id
tasks.forEach(item => {
    const diskPath = (item.disks || '').trim();
    const smartId = item.id;
    if (!diskPath) return;
    const idx = deviceToIndex[diskPath];
    if (idx !== undefined) {
        setOrUnset(`disk${idx}_smart_id`, smartId);
        console.log(`disk${idx} (${diskPath}) → smart_id=${smartId}`);
    } else {
        console.warn(`${diskPath} (id=${smartId}) 无法匹配磁盘列表`);
    }
});

pm.moduleVariables.set('smart_task_count', tasks.length);

console.log(`共 ${tasks.length} 个 SMART 任务已同步`);
