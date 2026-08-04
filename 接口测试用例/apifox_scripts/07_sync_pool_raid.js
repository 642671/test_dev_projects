/**
 * ==========================================================
 * GET /v2/storage/edit/pool/{uuid} 后置脚本（其一）
 * 功能：同步存储池 RAID设备到模块变量
 * ==========================================================
 *
 * 生成变量：
 *   vg{N}_raid      - 存储池的 RAID 设备路径（如 /dev/md1）
 *   vg{N}_md        - 存储池的 md 设备名（如 md0）
 *   vg_raid_count   - RAID 设备数量
 *   vg_md_count     - md 设备数量
 * ==========================================================
 */

const res = pm.response.json();

// 清理历史 RAID 变量及 md 变量
for (let i = 0; i < 50; i++) {
    pm.moduleVariables.unset(`vg${i}_raid`);
    pm.moduleVariables.unset(`vg${i}_md`);
}
pm.moduleVariables.unset("vg_raid_count");
pm.moduleVariables.unset("vg_md_count");
console.log("历史RAID变量及md变量清理完成。");

if (!res.data) {
    console.log("响应 data 为空，停止生成RAID变量。");
    return;
}

const vgName = res.data.name;
const pvs = res.data.pvs;

if (!pvs || pvs.length === 0) {
    console.log("pvs为空，不生成新的RAID变量。");
    pm.moduleVariables.set("vg_raid_count", 0);
} else {
    const raidVariableName = `${vgName}_raid`;
    pm.moduleVariables.set(raidVariableName, pvs[0]);
    console.log(`${raidVariableName} = ${pvs[0]}`);
    pm.moduleVariables.set("vg_raid_count", pvs.length);
}

// 提取 raidname（md设备名）
const volumes = res.data.volumes;
if (!volumes || volumes.length === 0) {
    console.log("volumes为空，不生成md变量。");
    pm.moduleVariables.set("vg_md_count", 0);
} else {
    const mdSet = new Set();
    for (const vol of volumes) {
        if (vol.raidname && vol.raidname.length > 0) {
            for (const md of vol.raidname) mdSet.add(md);
        }
    }
    if (mdSet.size === 0) {
        console.log("所有卷的raidname为空，不生成md变量。");
        pm.moduleVariables.set("vg_md_count", 0);
    } else {
        const mdName = [...mdSet][0];
        const mdVariableName = `${vgName}_md`;
        pm.moduleVariables.set(mdVariableName, mdName);
        console.log(`${mdVariableName} = ${mdName}`);
        pm.moduleVariables.set("vg_md_count", mdSet.size);
    }
}

console.log(`存储池：${vgName}`);
console.log("RAID设备变量及md变量同步完成。");
