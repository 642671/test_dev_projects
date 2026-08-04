/**
 * ==========================================================
 * GET /v2/storage/list/storagePool 后置脚本（其一）
 * 功能：同步存储池 UUID 到模块变量
 * ==========================================================
 *
 * 生成变量：
 *   vg{N}_uuid - 按 sort 排序后的第 N 个存储池 UUID
 *   vg_count   - 存储池总数
 *
 * 后续接口可直接使用 vg0_uuid, vg1_uuid, ...
 * ==========================================================
 */

const res = pm.response.json();

if (!res.data) {
    console.log("响应 data 为空，停止生成存储池变量。");
    return;
}

const storagePools = Object.values(res.data)
    .sort((a, b) => a.sort - b.sort);

// 清理历史变量（防止存储池删除后变量残留）
for (let i = 0; i < 50; i++) {
    pm.moduleVariables.unset(`vg${i}_uuid`);
}

// 重新生成（sort-1 零基映射，删除中间池后不会错位）
storagePools.forEach((pool) => {
    const sortIndex = pool.sort - 1;
    const variableName = `vg${sortIndex}_uuid`;
    pm.moduleVariables.set(variableName, pool.uuid);
    console.log(`${variableName} = ${pool.uuid}`);
});

pm.moduleVariables.set("vg_count", storagePools.length);

console.log(`共发现 ${storagePools.length} 个存储池`);
console.log("所有存储池 UUID 已同步到模块变量。");
