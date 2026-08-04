// ============================================================
// GET /v2/disk/GetDiskOption 后置脚本（其二）
// 解析返回 → 写入模块变量 → 供后续接口引用磁盘路径
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行必须先清理旧的同前缀变量
//   2. 有值就 set，没值就 unset，不允许残留空字符串或 0
//   3. 磁盘变量按索引命名：disk1_device / disk1（name），索引从 1 起
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

// 0. 清理所有旧的 diskN_ 变量
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^disk\d+_/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 响应合法性校验
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

// 2. 提取磁盘列表 → 按索引 1 起生成 diskN_device / diskN
const disks = (data || []).map(d => ({
    name:   (d.name   || '').trim(),
    device: (d.device || '').trim(),
}));

if (disks.length > 0) {
    pm.moduleVariables.set('disk_count', disks.length);
    pm.moduleVariables.set('disk_list', JSON.stringify(disks));
}

disks.forEach((d, i) => {
    const idx = i + 1;
    setOrUnset(`disk${idx}_device`, d.device);
    setOrUnset(`disk${idx}`,        d.name);
});

// 3. 调试输出
console.log('==== 磁盘列表资源一览 ====');
console.log(`磁盘总数: ${disks.length} 块`);
disks.forEach((d, i) => {
    console.log(`  disk${i + 1}_device=${d.device}, disk${i + 1}=${d.name}`);
});
