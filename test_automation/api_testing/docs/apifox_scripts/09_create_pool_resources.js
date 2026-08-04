// ============================================================
// GET /v2/storage/create/pool 后置脚本
// 解析返回 → 写入模块变量 → 供后续 POST 创建存储池使用
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行必须先清理旧的同前缀变量（动态扫描 cp_ 前缀）
//   2. 有值就 set，没值就 unset，不允许残留空字符串或 0
//   3. 磁盘变量按索引 cp_disk_N_* 铺开，不限数量（适配大盘位机器）
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

// 0. 清理所有旧的 cp_ 变量
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => k.startsWith('cp_'))
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 响应合法性校验
pm.test('响应结构正确', () => {
    pm.expect(res).to.be.an('object');
    pm.expect(data).to.have.property('pool_info');
    pm.expect(data).to.have.property('free_disk');
    pm.expect(data.free_disk).to.be.an('array');
});

pm.test('至少存在一个空闲磁盘（POST disks 必填 ≥1 item）', () => {
    pm.expect(data.free_disk.length).to.be.above(0);
});

// 2. 空闲磁盘列表 → 提取 name / 设备路径 / 类型 / 容量
const freeDisks = (data.free_disk || []).map(d => ({
    label: `${d.name}(${d.device || ''}, ${d.capacity || ''})`,
    value: (d.device || '').trim(),
    name:  (d.name  || '').trim(),
    slot:  d.slot || 0,
    type:  d.type || '',
    capacity: d.capacity || '',
    bytes: d.bytes?.value || 0,
    status: d.status || '',
}));

// 2.1 汇总变量
if (freeDisks.length > 0) {
    pm.moduleVariables.set('cp_disk_list', JSON.stringify(freeDisks));
    pm.moduleVariables.set('cp_disk_count', freeDisks.length);
}

// 2.2 按索引为每一块空闲磁盘生成独立变量
freeDisks.forEach((d, i) => {
    setOrUnset(`cp_disk_${i}_path`,     d.value);
    setOrUnset(`cp_disk_${i}_name`,     d.name);
    setOrUnset(`cp_disk_${i}_type`,     d.type);
    setOrUnset(`cp_disk_${i}_capacity`, d.capacity);
    setOrUnset(`cp_disk_${i}_slot`,     d.slot);
});

// 3. 新建存储池信息
const poolInfo = data.pool_info || {};
setOrUnset('cp_new_pool_show_name',   poolInfo.show_name);
setOrUnset('cp_new_pool_sort',        poolInfo.sort);
setOrUnset('cp_new_pool_uuid',        poolInfo.uuid);
setOrUnset('cp_new_pool_description', poolInfo.description);
setOrUnset('cp_new_pool_compression', poolInfo.compression);

if (typeof poolInfo.sort === 'number' && poolInfo.sort >= 1) {
    pm.moduleVariables.set('cp_new_pool_vg_name', `vg${poolInfo.sort - 1}`);
} else {
    pm.moduleVariables.unset('cp_new_pool_vg_name');
}

// 4. 调试输出
console.log('==== 创建存储池资源一览 ====');
console.log(`空闲磁盘: ${freeDisks.length} 块`);
freeDisks.forEach((d, i) => {
    console.log(`  cp_disk_${i}_path=${d.value}, name=${d.name}, type=${d.type}, capacity=${d.capacity}`);
});
console.log(`新池: show_name=${poolInfo.show_name || '(未返回)'}, sort=${poolInfo.sort}, vg=${pm.moduleVariables.get('cp_new_pool_vg_name') || '?'}`);
