// ============================================================
// GET /v2/disk/IhmInfoList 后置脚本
// 解析返回 → 写入模块变量 → 供后续健康扫描接口引用磁盘路径
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行必须先清理旧的同前缀变量（正则 /^Ihm\d+_/ 动态扫描）
//   2. 有值就 set，没值就 unset，不允许残留空字符串或 0
//   3. 变量按索引命名：Ihm1_device / Ihm1_name，索引从 1 起
//   4. 兼容空数组：当前环境仅 1 块可扫描盘，未来可能多块或 0 块
// ------------------------------------------------------------
// 变量使用方：
//   POST /v2/disk/ManualTest    （手动测试IHM，device 参数）
//   GET  /v2/disk/ExportIhmLog  （导出IHM日志，device 参数）
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
// 0. 清理所有旧的 IhmN_ 变量（动态扫描，防止拔盘后残留）
// ============================================================
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^Ihm\d+_/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// ============================================================
// 1. 响应合法性校验（仅断言 data 为数组，允许空数组）
// ============================================================
pm.test('响应结构正确（data 为数组）', () => {
    pm.expect(data).to.be.an('array');
});

// ============================================================
// 2. 标准化为数组（兼容对象 / 数组 / 空数组 / null）
// ============================================================
let ihmDisks;
if (Array.isArray(data)) {
    ihmDisks = data;
} else if (data && typeof data === 'object') {
    ihmDisks = [data];
} else {
    ihmDisks = [];
}

// 提取字段（.trim 防 %20）
const disks = ihmDisks.map(d => ({
    name:        (d.name       || '').trim(),   // HDD1
    device:      (d.device     || '').trim(),   // /dev/sde
    model:       (d.model      || '').trim(),   // ST2000VN004-2E4164
    drive_type:  (d.drive_type || '').trim(),   // IRONWOLF
    health:      (d.health     || '').trim(),   // Healthy
    capacity:    (d.capacity   || '').trim(),   // 2.00 TB
}));

// ============================================================
// 3. 汇总变量 + 按索引 1 起生成 IhmN_device / IhmN_name
// ============================================================
pm.moduleVariables.set('Ihm_count', disks.length);
if (disks.length > 0) {
    pm.moduleVariables.set('Ihm_disk_list', JSON.stringify(disks));
} else {
    pm.moduleVariables.unset('Ihm_disk_list');
}

disks.forEach((d, i) => {
    const idx = i + 1;                                  // 索引从 1 起
    setOrUnset(`Ihm${idx}_device`, d.device);           // Ihm1_device = /dev/sde
    setOrUnset(`Ihm${idx}_name`,   d.name);             // Ihm1_name   = HDD1
    setOrUnset(`Ihm${idx}_model`,  d.model);            // Ihm1_model  = ST2000VN004-2E4164
    setOrUnset(`Ihm${idx}_health`, d.health);           // Ihm1_health = Healthy
});

// ============================================================
// 4. 调试输出（结构化格式）
// ============================================================
console.log('====================================');
console.log(`共发现 ${disks.length} 块可执行健康扫描的磁盘`);
console.log('====================================');
console.log('========== IhmN_ 变量明细 ==========');
if (disks.length > 0) {
    disks.forEach((d, i) => {
        const idx = i + 1;
        console.log(`Ihm${idx}_device = ${d.device}`);
        console.log(`Ihm${idx}_name = ${d.name}`);
        console.log(`Ihm${idx}_model = ${d.model}`);
        console.log(`Ihm${idx}_health = ${d.health}`);
    });
} else {
    console.log('(无可扫描磁盘，所有 IhmN_ 变量已清空)');
}
console.log('=======================================');
console.log('所有 IHM 磁盘信息已同步到模块变量。');
console.log('=======================================');
