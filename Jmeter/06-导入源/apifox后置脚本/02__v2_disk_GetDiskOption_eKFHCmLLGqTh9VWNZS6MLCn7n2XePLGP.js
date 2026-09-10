// ============================================================
// GET /v2/disk/list 后置脚本（示例路径，请按实际接口路径调整注释）
// 解析返回 → 写入模块变量 → 供后续接口引用磁盘路径
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行必须先清理旧的同前缀变量
//   2. 有值就 set，没值就 unset，不允许残留空字符串或 0
//   3. 磁盘变量按索引命名：disk1_device / disk1_name（索引从 1 起）
// ============================================================

const res = pm.response.json();
const data = res.data || res;       // 此接口 data 直接是数组

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
// 0. 清理所有旧的 diskN_ 变量（动态扫描，防止残留）
//    匹配 disk1_device / disk2_name / disk12_device 等
// ============================================================
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^disk\d+_/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// ============================================================
// 1. 响应合法性校验
// ============================================================
pm.test('响应结构正确（data 为数组）', () => {
    pm.expect(data).to.be.an('array');
});

pm.test('至少存在一个磁盘', () => {
    pm.expect(data.length).to.be.above(0);
});

pm.test('每个磁盘元素包含 name 和 device', () => {
    data.forEach(item => {
        pm.expect(item).to.have.property('name');
        pm.expect(item).to.have.property('device');
    });
});

// ============================================================
// 2. 提取磁盘列表 → 按索引 1 起生成 diskN_device / diskN_name
// ============================================================
const disks = (data || []).map(d => ({
    name:   (d.name   || '').trim(),
    device: (d.device || '').trim(),
}));

// 汇总变量
if (disks.length > 0) {
    pm.moduleVariables.set('disk_count', disks.length);
    pm.moduleVariables.set('disk_list', JSON.stringify(disks));
}

// 按索引为每一块磁盘生成独立变量（索引从 1 起）
disks.forEach((d, i) => {
    const idx = i + 1;                              // 索引 1 起
    setOrUnset(`disk${idx}_device`, d.device);      // disk1_device = /dev/sda
    setOrUnset(`disk${idx}`,   d.name);        // disk1_name   = HDD3
});

// ============================================================
// 3. 调试输出
// ============================================================
console.log('==== 磁盘列表资源一览 ====');
console.log(`磁盘总数: ${disks.length} 块`);
disks.forEach((d, i) => {
    console.log(`  disk${i + 1}_device=${d.device}, disk${i + 1}=${d.name}`);
});