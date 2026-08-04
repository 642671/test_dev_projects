// ============================================================
// 22_hc_cache_list.js
// GET /v2/lvmCache/CacheLvsInfo 后置脚本（获取SSD缓存列表）
// 产出（全量同步 + 按状态/RAID级别/盘类型分类 + 空值清除）：
//   hc{N}_uuid              缓存逻辑卷UUID（供 DeleteCacheLv 的 lv_uuid）
//   hc_md1_uuid             降阶的RAID1缓存阵列UUID
//   hc_md5_uuid             降阶的RAID5缓存阵列UUID
//   hc_md_ok_uuid           正常状态的RAID1缓存阵列UUID
//   hc_md_ok0_uuid          正常状态的RAID0缓存阵列UUID
//   hc_md_bad1_uuid         损坏状态的RAID1缓存阵列UUID
//   hc_md_bad0_uuid         损坏状态的RAID0缓存阵列UUID
//   hc_md_repair_uuid       修复中的缓存阵列UUID
//   hc_md_mix_uuid          由SSD+NVMe混合组成的缓存阵列UUID
//   hc_md_ssd_uuid          仅由SSD组成的缓存阵列UUID
//   hc_md_nvme_uuid         仅由NVMe组成的缓存阵列UUID
//   deleted_hc_uuid         已删除的缓存UUID（通常列表不含，保留占位）
//   creating_hc_uuid        创建中的缓存UUID
// 编码模式：前缀扫描清理 + 状态/级别/类型条件分类
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

// 0. 清理上一轮所有 hc* 变量
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^hc\d+_uuid$/.test(k) || /^hc_md_|^deleted_hc_uuid$|^creating_hc_uuid$/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 标准化数组
let items = Array.isArray(data) ? data : (data && data.caches ? data.caches : []);
if (!Array.isArray(items) && data && typeof data === 'object') items = [data];

if (items.length === 0) {
    console.log('当前无SSD缓存，hc* 变量已清空');
    return;
}

// 2. 逐项提取
items.forEach((item, i) => {
    const idx = i + 1;
    // 兼容字段：lv_uuid/uuid/cache_uuid/lv_name 中的 uuid
    const uuid = (item.lv_uuid || item.uuid || item.cache_uuid || '').toString().trim();
    if (uuid) setOrUnset(`hc${idx}_uuid`, uuid);
    else setOrUnset(`hc${idx}_uuid`, null);

    // 状态字段（兼容 status/health/state）：degraded=降阶 normal/ok=正常 corrupt/broken=损坏 repairing=修复中 creating=创建中 deleted=已删除
    const statusRaw = (item.status !== undefined ? String(item.status) : (item.health || item.state || '')).toString().toLowerCase();
    // RAID级别（兼容 raid_level/level/raid）
    const raidRaw = (item.raid_level !== undefined ? String(item.raid_level) : (item.level || item.raid || '')).toString().toLowerCase();
    // 盘类型（兼容 disk_type/device_type/type）
    const typeRaw = (item.disk_type || item.device_type || item.type || '').toString().toLowerCase();

    const isDegraded = /degrad|降阶|1$|5$/.test(statusRaw) && !/ok|normal|corrupt|repair|creat/.test(statusRaw);
    const isNormal = /ok|normal|healthy|0$/.test(statusRaw);
    const isBad = /corrupt|broken|bad|damage/.test(statusRaw);
    const isRepairing = /repair|fix/.test(statusRaw);
    const isCreating = /creat|building/.test(statusRaw);
    const isDeleted = /deleted|gone/.test(statusRaw);

    // RAID级别归一
    const isRaid1 = /1/.test(raidRaw) && !/10/.test(raidRaw);
    const isRaid5 = /5/.test(raidRaw);
    const isRaid0 = /0/.test(raidRaw) && !/10/.test(raidRaw);

    // 盘类型
    const hasNvme = /nvme/.test(typeRaw);
    const hasSsd = /ssd|sata/.test(typeRaw);
    const hasHdd = /hdd|normal/.test(typeRaw);

    // 3. 状态 + 级别 → 专用变量（仅首个匹配写入，保持幂等）
    if (isDegraded && isRaid1 && !pm.moduleVariables.has('hc_md1_uuid')) setOrUnset('hc_md1_uuid', uuid);
    if (isDegraded && isRaid5 && !pm.moduleVariables.has('hc_md5_uuid')) setOrUnset('hc_md5_uuid', uuid);
    if (isNormal && isRaid1 && !pm.moduleVariables.has('hc_md_ok_uuid')) setOrUnset('hc_md_ok_uuid', uuid);
    if (isNormal && isRaid0 && !pm.moduleVariables.has('hc_md_ok0_uuid')) setOrUnset('hc_md_ok0_uuid', uuid);
    if (isBad && isRaid1 && !pm.moduleVariables.has('hc_md_bad1_uuid')) setOrUnset('hc_md_bad1_uuid', uuid);
    if (isBad && isRaid0 && !pm.moduleVariables.has('hc_md_bad0_uuid')) setOrUnset('hc_md_bad0_uuid', uuid);
    if (isRepairing && !pm.moduleVariables.has('hc_md_repair_uuid')) setOrUnset('hc_md_repair_uuid', uuid);
    if (isCreating && !pm.moduleVariables.has('creating_hc_uuid')) setOrUnset('creating_hc_uuid', uuid);
    if (isDeleted && !pm.moduleVariables.has('deleted_hc_uuid')) setOrUnset('deleted_hc_uuid', uuid);

    // 4. 盘类型组合（多盘阵列：字段可能是数组或逗号分隔串）
    const types = Array.isArray(item.disks) ? item.disks.map(d => (d.type || d.disk_type || '').toString().toLowerCase()).join(',')
        : typeRaw;
    const mixSsdNvme = /ssd|sata/.test(types) && /nvme/.test(types);
    const onlySsd = /ssd|sata/.test(types) && !/nvme/.test(types) && !/hdd|normal/.test(types);
    const onlyNvme = /nvme/.test(types) && !/ssd|sata/.test(types) && !/hdd|normal/.test(types);

    if (mixSsdNvme && !pm.moduleVariables.has('hc_md_mix_uuid')) setOrUnset('hc_md_mix_uuid', uuid);
    if (onlySsd && !pm.moduleVariables.has('hc_md_ssd_uuid')) setOrUnset('hc_md_ssd_uuid', uuid);
    if (onlyNvme && !pm.moduleVariables.has('hc_md_nvme_uuid')) setOrUnset('hc_md_nvme_uuid', uuid);
});

console.log('CacheLvsInfo 同步完成，hc* 变量已更新');
