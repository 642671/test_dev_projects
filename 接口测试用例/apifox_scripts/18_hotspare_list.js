// ============================================================
// GET /v2/hotsparedisk/GetHotSpareList 后置脚本
// 提取已有热备盘的 device 和 device_name，
// 生成 hsp{N}_device 和 hsp{N}_blk（N 从 1 起）
// ------------------------------------------------------------
// hsp{N}_device → POST /v2/hotsparedisk/DelHotSpare（删除热备盘）
// hsp{N}_blk    → POST /v2/hotsparedisk/ModifyArray（修改关联阵列）
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

// ============================================================
// 0. 清理所有旧的 hsp 变量
// ============================================================
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^hsp\d+_/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// ============================================================
// 1. 标准化为数组
// ============================================================
let items;
if (Array.isArray(data)) {
    items = data;
} else if (data && typeof data === 'object') {
    items = [data];
} else {
    items = [];
}

if (items.length === 0) {
    console.log('当前无已有热备盘，所有 hsp 变量已清空');
    pm.moduleVariables.set('hsp_count', 0);
    return;
}

// ============================================================
// 2. 提取 device 和 device_name，按数组顺序从 1 起编号
// ============================================================
items.forEach((item, i) => {
    const idx = i + 1;
    setOrUnset(`hsp${idx}_device`, (item.device || '').trim());
    setOrUnset(`hsp${idx}_blk`,    (item.device_name || '').trim());
    console.log(`hsp${idx}_device = ${item.device}, hsp${idx}_blk = ${item.device_name} (${item.name || ''})`);
});

pm.moduleVariables.set('hsp_count', items.length);

// ============================================================
// 3. 调试输出
// ============================================================
console.log(`==== 已有热备盘同步结果 ====`);
console.log(`已有热备盘: ${items.length} 个`);

const updatedVars = pm.moduleVariables.toObject();
const hspVars = Object.keys(updatedVars)
    .filter(k => /^hsp\d+_device$/.test(k))
    .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]));

if (hspVars.length > 0) {
    console.log('---------- hsp{N} 明细 ----------');
    hspVars.forEach(k => {
        const n = k.match(/hsp(\d+)_device/)[1];
        console.log(`${k} = ${updatedVars[k]}`);
        console.log(`hsp${n}_blk  = ${updatedVars[`hsp${n}_blk`] || '(无)'}`);
    });
} else {
    console.log('(无)');
}
console.log('=======================================');
