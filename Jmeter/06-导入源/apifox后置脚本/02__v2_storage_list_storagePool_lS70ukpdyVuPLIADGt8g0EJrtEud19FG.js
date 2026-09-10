// ============================================================
// GET /v2/storage/list/storagePool 后置脚本
// 按池名生成模块变量：
//   avail_{池名}_uuid    → 可用池 UUID
//   corrupt_{池名}_uuid  → 损坏池 UUID
// 每次执行自动刷新，不存在的变量自动删除，不留遗留
// ============================================================

const pools = pm.response.json().data || {};

const availNames = [];
const corruptNames = [];

Object.values(pools).forEach(p => {
    if (p.is_available || p.health === 999) {
        availNames.push(p.name);
        pm.moduleVariables.set(`avail_${p.name}_uuid`, p.uuid);
    } else if (p.health === 0) {
        corruptNames.push(p.name);
        pm.moduleVariables.set(`corrupt_${p.name}_uuid`, p.uuid);
    }
});


// 清理已不存在的变量
const allVars = pm.moduleVariables.toObject();
Object.keys(allVars).forEach(key => {
    const am = key.match(/^avail_(.+)_uuid$/);
    const cm = key.match(/^corrupt_(.+)_uuid$/);
    if (am && !availNames.includes(am[1])) pm.moduleVariables.unset(key);
    if (cm && !corruptNames.includes(cm[1])) pm.moduleVariables.unset(key);
});


// ============================================================
// 控制台输出结果
// ============================================================
console.log('========== 存储池变量同步结果 ==========');
console.log(`可用池(${availNames.length}): ${availNames.map(n => `avail_${n}_uuid`).join(', ') || '无'}`);
console.log(`损坏池(${corruptNames.length}): ${corruptNames.map(n => `corrupt_${n}_uuid`).join(', ') || '无'}`);

// 逐个打印变量名 = 值，便于核对
console.log('---------- 可用池变量明细 ----------');
availNames.forEach(n => {
    const key = `avail_${n}_uuid`;
    console.log(`${key} = ${pm.moduleVariables.get(key)}`);
});

console.log('---------- 损坏池变量明细 ----------');
corruptNames.forEach(n => {
    const key = `corrupt_${n}_uuid`;
    console.log(`${key} = ${pm.moduleVariables.get(key)}`);
});
console.log('=======================================');