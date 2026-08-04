/**
 * ==========================================================
 * GET /v2/storage/list/volume 后置脚本
 * 功能：同步卷 UUID 到模块变量
 * ==========================================================
 *
 * 生成变量：
 *   lv{N}_uuid       - 按 sort 排序后的第 N 个卷 UUID
 *   lv{N}_filesystem - 对应卷的文件系统类型
 *   lv_count         - 卷总数
 *
 * 后续接口可使用 lv0_uuid, lv1_uuid, ...
 * ==========================================================
 */

const res = pm.response.json();

if (!res.data) {
    console.log("响应 data 为空，停止生成模块变量。");
    return;
}

const volumes = Object.values(res.data)
    .sort((a, b) => a.sort - b.sort);

// 清理历史变量（防止卷删除后变量残留）
for (let i = 0; i < 50; i++) {
    pm.moduleVariables.unset(`lv${i}_uuid`);
    pm.moduleVariables.unset(`lv${i}_filesystem`);
}

// 重新生成（sort-1 零基映射，删除中间卷后不会错位）
volumes.forEach((volume) => {
    const sortIndex = volume.sort - 1;
    const uuidVar = `lv${sortIndex}_uuid`;
    const fsVar = `lv${sortIndex}_filesystem`;

    pm.moduleVariables.set(uuidVar, volume.uuid);
    pm.moduleVariables.set(fsVar, volume.filesystem);

    console.log(`${uuidVar} = ${volume.uuid}`);
    console.log(`${fsVar} = ${volume.filesystem}`);
});

pm.moduleVariables.set("lv_count", volumes.length);

console.log(`共发现 ${volumes.length} 个卷`);
console.log("所有 UUID、filesystem 已同步到模块变量。");
