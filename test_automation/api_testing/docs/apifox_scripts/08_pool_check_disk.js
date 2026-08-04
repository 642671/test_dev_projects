// ============================================================
// GET /v2/storage/edit/pool/{uuid} 后置脚本（其二）
// 按池名生成 {池名}_check_disk，空就删
// ============================================================

const data = pm.response.json().data;

const freeDevices = (data.free_disk || [])
    .map(d => d.device);

console.log('池名:', data.name);
console.log('空闲磁盘:', freeDevices);

if (freeDevices.length > 0) {
    pm.environment.set(`${data.name}_check_disk`, freeDevices.join(','));
    console.log(`已设置 ${data.name}_check_disk = ${freeDevices.join(',')}`);
} else {
    pm.environment.unset(`${data.name}_check_disk`);
    console.log(`已删除 ${data.name}_check_disk`);
}
