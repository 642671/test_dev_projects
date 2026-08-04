// ============================================================
// GET /v2/storage/list/storagePool 后置脚本
// 按池名生成模块变量：
//   avail_{池名}_uuid    → 可用池 UUID
//   avail_{池名}_disk    → 可用池磁盘设备名（去 /dev/ 前缀）
//   corrupt_{池名}_uuid  → 损坏池 UUID
//   corrupt_{池名}_disk  → 损坏池磁盘设备名（去 /dev/ 前缀）
// 每次执行自动刷新，不存在的变量自动删除，不留遗留
// ============================================================

const pools = pm.response.json().data || {};

const availNames = [];
const corruptNames = [];

Object.values(pools).forEach(p => {
    if (p.is_available || p.health === 999) {
        availNames.push(p.name);
        pm.moduleVariables.set(`avail_${p.name}_uuid`, p.uuid);
        // 提取磁盘设备名（从 decated_required_disk[0].device 中取，去掉 /dev/ 前缀）
        const diskDevice = (p.decated_required_disk?.[0]?.device || p.device || '').replace(/^\/dev\//, '');
        if (diskDevice) {
            pm.moduleVariables.set(`avail_${p.name}_disk`, diskDevice);
        } else {
            pm.moduleVariables.unset(`avail_${p.name}_disk`);
        }
    } else if (p.health === 0) {
        corruptNames.push(p.name);
        pm.moduleVariables.set(`corrupt_${p.name}_uuid`, p.uuid);
        const diskDevice = (p.decated_required_disk?.[0]?.device || p.device || '').replace(/^\/dev\//, '');
        if (diskDevice) {
            pm.moduleVariables.set(`corrupt_${p.name}_disk`, diskDevice);
        } else {
            pm.moduleVariables.unset(`corrupt_${p.name}_disk`);
        }
    }
});

// 清理已不存在的变量（含 uuid 和 disk 两类后缀）
const allVars = pm.moduleVariables.toObject();
Object.keys(allVars).forEach(key => {
    const amUuid = key.match(/^avail_(.+)_uuid$/);
    const amDisk = key.match(/^avail_(.+)_disk$/);
    const cmUuid = key.match(/^corrupt_(.+)_uuid$/);
    const cmDisk = key.match(/^corrupt_(.+)_disk$/);
    if (amUuid && !availNames.includes(amUuid[1])) pm.moduleVariables.unset(key);
    if (amDisk && !availNames.includes(amDisk[1])) pm.moduleVariables.unset(key);
    if (cmUuid && !corruptNames.includes(cmUuid[1])) pm.moduleVariables.unset(key);
    if (cmDisk && !corruptNames.includes(cmDisk[1])) pm.moduleVariables.unset(key);
});

// ============================================================
// 控制台输出结果
// ============================================================
console.log('========== 存储池变量同步结果 ==========');
console.log(`可用池(${availNames.length}): ${availNames.map(n => `avail_${n}_uuid`).join(', ') || '无'}`);
console.log(`损坏池(${corruptNames.length}): ${corruptNames.map(n => `corrupt_${n}_uuid`).join(', ') || '无'}`);

console.log('---------- 可用池变量明细 ----------');
availNames.forEach(n => {
    console.log(`avail_${n}_uuid = ${pm.moduleVariables.get(`avail_${n}_uuid`)}`);
    console.log(`avail_${n}_disk = ${pm.moduleVariables.get(`avail_${n}_disk`) || '(无)'}`);
});

console.log('---------- 损坏池变量明细 ----------');
corruptNames.forEach(n => {
    console.log(`corrupt_${n}_uuid = ${pm.moduleVariables.get(`corrupt_${n}_uuid`)}`);
    console.log(`corrupt_${n}_disk = ${pm.moduleVariables.get(`corrupt_${n}_disk`) || '(无)'}`);
});
console.log('=======================================');
