// ============================================================
// 24_hc_free_ssds.js
// GET /v2/lvmCache/FreeSSDs 后置脚本（获取空闲SSD列表）
// 产出（全量同步 + 按盘类型分类 + 空值清除）：
//   hc_cand_ssd         候选SSD设备路径（供 CreateCacheLv 的 fast_devices / FixLvmCache 的 disk_list）
//   hc_cand_ssd2        第2块候选SSD
//   hc_cand_ssd3        第3块候选SSD
//   hc_cand_nvme        候选NVMe设备路径
//   hc_cand_hdd         候选HDD设备路径（用于类型不匹配场景）
// 编码模式：前缀扫描清理 + 类型条件分类
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

// 0. 清理上一轮变量
['hc_cand_ssd', 'hc_cand_ssd2', 'hc_cand_ssd3', 'hc_cand_nvme', 'hc_cand_hdd']
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 标准化数组（兼容 data 数组 / data.ssds / data.disks）
let items = Array.isArray(data) ? data : (data && (data.ssds || data.disks) ? (data.ssds || data.disks) : []);
if (!Array.isArray(items) && data && typeof data === 'object') items = [data];

if (items.length === 0) {
    console.log('当前无空闲SSD，hc_cand_* 变量已清空');
    return;
}

let ssdIdx = 0;
items.forEach(item => {
    // 兼容字段：device/device_name/path + type/disk_type
    const dev = (item.device || item.device_name || item.path || '').toString().trim();
    if (!dev) return;
    const typeRaw = (item.type || item.disk_type || '').toString().toLowerCase();

    if (/nvme/.test(typeRaw)) {
        if (!pm.moduleVariables.has('hc_cand_nvme')) setOrUnset('hc_cand_nvme', dev);
    } else if (/hdd|normal/.test(typeRaw)) {
        if (!pm.moduleVariables.has('hc_cand_hdd')) setOrUnset('hc_cand_hdd', dev);
    } else {
        // 默认视为SSD（含 type=ssd / sata 或无type标记）
        ssdIdx++;
        const key = ssdIdx === 1 ? 'hc_cand_ssd' : ssdIdx === 2 ? 'hc_cand_ssd2' : ssdIdx === 3 ? 'hc_cand_ssd3' : null;
        if (key && !pm.moduleVariables.has(key)) setOrUnset(key, dev);
    }
});

console.log('FreeSSDs 同步完成，hc_cand_* 变量已更新');
