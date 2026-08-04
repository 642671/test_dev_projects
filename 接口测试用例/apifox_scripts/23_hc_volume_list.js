// ============================================================
// 23_hc_volume_list.js
// GET /v2/lvmCache/GetVolumeList 后置脚本（获取可加速卷列表）
// 产出（全量同步 + 按状态分类 + 空值清除）：
//   hc_lv_path         可加速卷的设备路径（供 CreateCacheLv 的 main_lv）
//   hc_lv_cached       已有缓存的卷路径
//   corrupt_lv_path    损坏状态的卷路径
//   unmount_lv_path    未挂载的卷路径
//   big_lv_path        大容量卷路径（容量大于缓存阵列组成容量）
// 编码模式：前缀扫描清理 + 状态条件分类
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
['hc_lv_path', 'hc_lv_cached', 'corrupt_lv_path', 'unmount_lv_path', 'big_lv_path']
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 标准化数组（兼容 data 数组 / data.volumes / data.lvs）
let items = Array.isArray(data) ? data : (data && (data.volumes || data.lvs) ? (data.volumes || data.lvs) : []);
if (!Array.isArray(items) && data && typeof data === 'object') items = [data];

if (items.length === 0) {
    console.log('当前无卷，lv_path 变量已清空');
    return;
}

// 提取卷路径：优先 lv_path/mnt_path/device，其次由 vg+lv 拼 /dev/mapper/vgX-lvX
function getPath(item) {
    const direct = (item.lv_path || item.mnt_path || item.device || item.path || '').toString().trim();
    if (direct) return direct;
    const vg = (item.vg || item.vg_name || item.pool || '').toString().trim();
    const lv = (item.lv || item.lv_name || item.name || '').toString().trim();
    if (vg && lv) return `/dev/mapper/${vg}-${lv}`;
    return '';
}

items.forEach(item => {
    // 状态（兼容 status/health/cache_status）：cached=已有缓存 corrupt/broken=损坏 unmount=未挂载
    const statusRaw = (item.status !== undefined ? String(item.status) : (item.health || item.cache_status || '')).toString().toLowerCase();
    const hasCache = /cache|cached/.test(statusRaw);
    const isCorrupt = /corrupt|broken|bad|damage/.test(statusRaw);
    const isUnmount = /unmount|not.?mounted|umount/.test(statusRaw);
    const isBig = /big|large|full/.test(statusRaw) ||
        (Number(item.capacity) > 0 && Number(item.capacity) > 1000); // 容量>1TB视为大卷（按实际环境调整）

    const p = getPath(item);
    if (!p) return;

    if (hasCache && !pm.moduleVariables.has('hc_lv_cached')) setOrUnset('hc_lv_cached', p);
    if (isCorrupt && !pm.moduleVariables.has('corrupt_lv_path')) setOrUnset('corrupt_lv_path', p);
    if (isUnmount && !pm.moduleVariables.has('unmount_lv_path')) setOrUnset('unmount_lv_path', p);
    if (isBig && !pm.moduleVariables.has('big_lv_path')) setOrUnset('big_lv_path', p);
    if (!hasCache && !isCorrupt && !pm.moduleVariables.has('hc_lv_path')) setOrUnset('hc_lv_path', p); // 首条正常可加速卷
});

console.log('GetVolumeList 同步完成，lv_path 变量已更新');
