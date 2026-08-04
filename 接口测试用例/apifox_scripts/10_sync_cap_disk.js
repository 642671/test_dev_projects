/**
 * ==========================================================
 * GET /v2/disk/GetDiskOption 后置脚本（其一）
 * 功能：同步磁盘设备名到模块变量（CheckAvailablePool 专用）
 * ==========================================================
 *
 * 生成变量：
 *   cap_disk{N}    - 第 N 个磁盘设备名（去掉 /dev/ 前缀）
 *   cap_disk_count - 磁盘总数
 *
 * 用于接口：/v2/storage/CheckAvailablePool/{{cap_disk0}}
 * ==========================================================
 */

const res = pm.response.json();

if (!res.data) {
    console.log("响应 data 为空，停止生成磁盘变量。");
    return;
}

const disks = res.data.map(d => d.device.replace(/^\/dev\//, ''));

for (let i = 0; i < 50; i++) {
    pm.moduleVariables.unset(`cap_disk${i}`);
}

disks.forEach((disk, index) => {
    const variableName = `cap_disk${index}`;
    pm.moduleVariables.set(variableName, disk);
    console.log(`${variableName} = ${disk}`);
});

pm.moduleVariables.set("cap_disk_count", disks.length);

console.log(`共发现 ${disks.length} 个磁盘`);
console.log("所有磁盘设备名已同步到模块变量。");
