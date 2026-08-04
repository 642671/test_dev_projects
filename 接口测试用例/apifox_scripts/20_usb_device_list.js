// ============================================================
// GET /v2/extStorageDevice/DeviceList 后置脚本
// 提取 USB 设备的 name、device_name、分区列表、挂载状态
// ------------------------------------------------------------
// usb{N}_name    → POST /v2/extStorageDevice/MountedDevice（name 参数）
// usb{N}_device  → POST /v2/extStorageDevice/MountedDevice（device 参数）
//                → GET  /v2/extStorageDevice/IsFormating（name 参数）
// usb{N}_z{M}    → POST /v2/extStorageDevice/EditUsbLabel（分区名，如 sda1）
// usb{N}_s{M}    → shared_folders[].shared_name（如 usb_generic_2）
//                  → POST /v2/extStorageDevice/UsbAclAll（folder_names 数组）
//                  → POST /v2/extStorageDevice/SetUsbAclAll（folder 参数）
// usb{N}_mnt     → 已挂载分区 device_name（逗号分隔）
// usb{N}_umnt    → 未挂载分区 device_name（逗号分隔）
// usb{N}_fmt     → 格式化中分区 device_name（逗号分隔）
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

// ============================================================
// 0. 清理所有旧的 usb 变量
// ============================================================
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^usb\d+_/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// ============================================================
// 1. 标准化为数组
// ============================================================
let items;
if (Array.isArray(data)) {
    items = data;
} else if (data && typeof data === 'object') {
    items = [data];
} else {
    items = [];
}

if (items.length === 0) {
    console.log('当前无 USB 设备，所有 usb 变量已清空');
    pm.moduleVariables.set('usb_count', 0);
    return;
}

// ============================================================
// 2. 遍历提取
// ============================================================
items.forEach((item, i) => {
    const idx = i + 1;

    // --- 基本信息 ---
    setOrUnset(`usb${idx}_name`,   (item.name || '').trim());
    setOrUnset(`usb${idx}_device`, (item.device_name || '').trim());

    // --- 设备分区列表（zone_name[]）---
    const zones = item.zone_name || [];
    zones.forEach((z, j) => {
        const zIdx = j + 1;
        setOrUnset(`usb${idx}_z${zIdx}`, (z || '').trim());
    });

    // --- 共享文件夹分类 ---
    const folders = item.shared_folders || [];

    // 提取 shared_name（用于 UsbAclAll / SetUsbAclAll）
    folders.forEach((f, j) => {
        const sIdx = j + 1;
        const shareName = (f.shared_name || '').trim();
        if (shareName) {
            pm.moduleVariables.set(`usb${idx}_s${sIdx}`, shareName);
        } else {
            pm.moduleVariables.unset(`usb${idx}_s${sIdx}`);
        }
    });

    // 按挂载状态分类 device_name
    const mounted   = folders.filter(f => f.status === 1).map(f => (f.device_name || '').trim()).filter(Boolean);
    const unmounted = folders.filter(f => f.status === 2).map(f => (f.device_name || '').trim()).filter(Boolean);
    const formatting= folders.filter(f => f.status === 3).map(f => (f.device_name || '').trim()).filter(Boolean);

    if (mounted.length    > 0) pm.moduleVariables.set(`usb${idx}_mnt`,  mounted.join(','));
    else                        pm.moduleVariables.unset(`usb${idx}_mnt`);

    if (unmounted.length  > 0) pm.moduleVariables.set(`usb${idx}_umnt`, unmounted.join(','));
    else                        pm.moduleVariables.unset(`usb${idx}_umnt`);

    if (formatting.length > 0) pm.moduleVariables.set(`usb${idx}_fmt`,  formatting.join(','));
    else                        pm.moduleVariables.unset(`usb${idx}_fmt`);

    console.log(`usb${idx}_name=${item.name}, usb${idx}_device=${item.device_name}`);
    console.log(`  分区: ${zones.join(', ') || '无'}`);
    console.log(`  共享名: ${folders.map(f=>f.shared_name).filter(Boolean).join(', ') || '无'}`);
    console.log(`  已挂载: ${mounted.join(',') || '无'} | 未挂载: ${unmounted.join(',') || '无'} | 格式化中: ${formatting.join(',') || '无'}`);
});

pm.moduleVariables.set('usb_count', items.length);

// ============================================================
// 3. 调试输出
// ============================================================
console.log(`==== USB 设备同步结果 ====`);
console.log(`USB 设备: ${items.length} 个`);

const updatedVars = pm.moduleVariables.toObject();
const usbVars = Object.keys(updatedVars)
    .filter(k => /^usb\d+_device$/.test(k))
    .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]));

usbVars.forEach(k => {
    const n = k.match(/usb(\d+)_device/)[1];
    console.log(`--- usb${n} ---`);
    console.log(`  name    = ${updatedVars[`usb${n}_name`]}`);
    console.log(`  device  = ${updatedVars[k]}`);
    const zoneVars = Object.keys(updatedVars).filter(v => v.startsWith(`usb${n}_z`) && /^usb\d+_z\d+$/.test(v)).sort();
    console.log(`  分区    = ${zoneVars.map(v => updatedVars[v]).join(', ') || '(无)'}`);
    const shareVars = Object.keys(updatedVars).filter(v => v.startsWith(`usb${n}_s`) && /^usb\d+_s\d+$/.test(v)).sort();
    console.log(`  共享名  = ${shareVars.map(v => updatedVars[v]).join(', ') || '(无)'}`);
    console.log(`  已挂载  = ${updatedVars[`usb${n}_mnt`] || '(无)'}`);
    console.log(`  未挂载  = ${updatedVars[`usb${n}_umnt`] || '(无)'}`);
    console.log(`  格式化中= ${updatedVars[`usb${n}_fmt`] || '(无)'}`);
});
console.log('=======================================');
