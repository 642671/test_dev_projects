// ============================================================
// GET /v2/storage/create/volume 后置脚本
// 解析返回 → 写入模块变量 → 供后续 POST 创建卷使用
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行必须先清理旧的同前缀变量
//   2. 有值就 set，没值就 unset，不允许残留空字符串或 0
//   3. 变量按业务字段命名，不依赖数组下标
// ============================================================

const res = pm.response.json();
const data = res.data || res;

// ------------------------------------------------------------
// 小工具：有值就 set，否则 unset，避免残留空变量
// ------------------------------------------------------------
function setOrUnset(key, val) {
    if (val === undefined || val === null || val === '' || Number.isNaN(val)) {
        pm.moduleVariables.unset(key);
    } else {
        pm.moduleVariables.set(key, val);
    }
}

// ============================================================
// 0. 清理所有旧的 cv_ 变量（动态扫描，防止残留）
// ============================================================
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => k.startsWith('cv_'))
    .forEach(k => pm.moduleVariables.unset(k));

// ============================================================
// 1. 响应合法性校验
// ============================================================
pm.test('响应结构正确', () => {
    pm.expect(res).to.be.an('object');
    pm.expect(data).to.have.property('free_disk');
    pm.expect(data).to.have.property('free_pool');
    pm.expect(data).to.have.property('hype_lock');
    pm.expect(data.free_disk).to.be.an('array');
    pm.expect(data.free_pool).to.be.an('array');
});

// ============================================================
// 2. 空闲磁盘列表 → 提取 name 和设备路径
// ============================================================
const freeDisks = (data.free_disk || []).map(d => ({
    label: `${d.name}(${d.device || ''})`,
    value: (d.device || '').trim(),
    name:  (d.name  || '').trim(),
    capacity: d.capacity || '',
    type: d.type || '',
    status: d.status || '',
}));

if (freeDisks.length > 0) {
    pm.moduleVariables.set('cv_disk_list', JSON.stringify(freeDisks));
}

// 前 3 块空闲磁盘的路径 / 名称
setOrUnset('cv_disk_0_path', freeDisks[0]?.value);
setOrUnset('cv_disk_0_name', freeDisks[0]?.name);
setOrUnset('cv_disk_1_path', freeDisks[1]?.value);
setOrUnset('cv_disk_1_name', freeDisks[1]?.name);
setOrUnset('cv_disk_2_path', freeDisks[2]?.value);
setOrUnset('cv_disk_2_name', freeDisks[2]?.name);

// ============================================================
// 3. 每个存储池按实际名称生成独立变量
// ============================================================
const freePools = (data.free_pool || []).map(p => ({
    label: `${p.name}(${(p.free?.value || 0).toFixed(0)}${p.free?.unit || 'KB'}可用)`,
    value: (p.name || '').trim(),
    uuid: p.uuid || '',
    free: p.free?.value || 0,
    unit: p.free?.unit || 'KB',
    total: p.total?.value || 0,
    level: p.level || '',
    lv_count: p.lv_count || 0,
}));

if (freePools.length > 0) {
    pm.moduleVariables.set('cv_pool_list', JSON.stringify(freePools));
}

freePools.forEach(p => {
    const poolName = p.value;
    if (!poolName) return;
    pm.moduleVariables.set(`cv_${poolName}_name`,    poolName);
    pm.moduleVariables.set(`cv_${poolName}_free_kb`, p.free);
    pm.moduleVariables.set(`cv_${poolName}_free_gb`, Math.floor(p.free / 1024 / 1024));
});

if (freePools.length > 0) {
    setOrUnset('cv_selected_pool_name',    freePools[0].value);
    setOrUnset('cv_selected_pool_free_gb', Math.floor(freePools[0].free / 1024 / 1024));
} else {
    pm.moduleVariables.unset('cv_selected_pool_name');
    pm.moduleVariables.unset('cv_selected_pool_free_gb');
}

// ============================================================
// 4. 自动生成的存储池名（mode=0 新池时用）
// ============================================================
const poolInfo = data.pool_info || {};
setOrUnset('cv_new_pool_name', poolInfo.show_name || poolInfo.uuid);
setOrUnset('cv_new_pool_sort', poolInfo.sort);

// ============================================================
// 5. 自动生成的卷名（前端回显用）
// ============================================================
setOrUnset('cv_new_volume_sort', data.volume_info1?.sort || data.volume_info2?.sort);

// ============================================================
// 6. 是否支持 xfs 文件系统
// ============================================================
const xfsAvailable = !!data.hype_lock;
pm.moduleVariables.set('cv_xfs_available', xfsAvailable);
const fsOptions = ['btrfs', 'ext4'];
if (xfsAvailable) fsOptions.push('xfs');
pm.moduleVariables.set('cv_fs_options', JSON.stringify(fsOptions));
pm.moduleVariables.set('cv_filesystem', 'btrfs');

// ============================================================
// 7. 调试输出
// ============================================================
console.log('==== 创建卷资源一览 ====');
console.log(`空闲磁盘: ${freeDisks.length} 块 → ${freeDisks.map(d => d.label).join(', ') || '无'}`);
console.log(`可选存储池: ${freePools.length} 个 → ${freePools.map(p => p.label).join(', ') || '无'}`);
freePools.forEach(p => {
    console.log(`  cv_${p.value}_name=${p.value}, 剩余=${Math.floor(p.free/1024/1024)}GB`);
});
console.log(`选中池: cv_selected_pool_name=${pm.moduleVariables.get('cv_selected_pool_name') || '(未设置)'}`);
console.log(`自动池名: ${poolInfo.show_name || '(未返回)'}`);
console.log(`xfs 可用: ${xfsAvailable}`);
console.log(`文件系统选项: ${fsOptions.join('/')}`);
