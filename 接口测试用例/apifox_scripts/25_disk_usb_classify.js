// ============================================================
// 25_disk_usb_classify.js
// GET /v2/disk/GetDiskOption 后置脚本（其三：USB/SD外设分类）
// 产出（全量同步 + 类型条件分类 + 空值清除）：
//   usb_disk_device / usb_disk_name        通用USB磁盘（第一块）
//   usb_sata_device/model/serial           USB接口中的SATA盘
//   usb_nvme_device/model/serial           USB接口中的NVMe盘
//   usb_other_device/model/serial          USB其他类型设备
//   sdtf_device/model/serial               SD/TF卡
//   usb_ssd_device                         USB中的SSD（HyperCache用）
// 编码模式：前缀扫描清理 + 类型条件分类（兼容 model/serial 缺省）
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

// 0. 清理上一轮所有 usb_*/sdtf_* 变量（注意保留 usb{N}_* 编号变量，勿误清）
const allModuleVars = pm.moduleVariables.toObject();
Object.keys(allModuleVars)
    .filter(k => /^usb_(disk|sata|nvme|other|ssd)_/.test(k) || /^sdtf_/.test(k))
    .forEach(k => pm.moduleVariables.unset(k));

// 1. 标准化数组
let items = Array.isArray(data) ? data : [];
if (!Array.isArray(items) && data && typeof data === 'object') items = [data];

if (items.length === 0) {
    console.log('GetDiskOption 无数据，usb_*/sdtf_* 变量已清空');
    return;
}

// 2. 逐项分类
let usbDiskIdx = 0;
items.forEach(item => {
    const name = (item.name || '').toString().trim();
    const device = (item.device || '').toString().trim();
    const model = (item.model || '').toString().trim();
    const serial = (item.serial || '').toString().trim();
    if (!name && !device) return;

    // 类型判定（兼容 type/interface/bus 字段）
    const typeRaw = [item.type, item.interface, item.bus, item.model, item.name]
        .filter(Boolean).join(' ').toString().toLowerCase();

    const isUsb = /usb/.test(typeRaw);
    const isSd = /sd|mmc|tf|sdtf|card/.test(typeRaw) && !isUsb;

    if (isSd) {
        if (!pm.moduleVariables.has('sdtf_device')) setOrUnset('sdtf_device', device || name);
        if (model && !pm.moduleVariables.has('sdtf_model')) setOrUnset('sdtf_model', model);
        if (serial && !pm.moduleVariables.has('sdtf_serial')) setOrUnset('sdtf_serial', serial);
        return;
    }

    if (isUsb) {
        // USB 第一块通用磁盘
        if (usbDiskIdx === 0) {
            setOrUnset('usb_disk_device', device || name);
            setOrUnset('usb_disk_name', name || device);
        }
        usbDiskIdx++;

        // 细分：NVMe / SATA / 其他
        const isNvme = /nvme/.test(typeRaw);
        const isSata = /sata|ata/.test(typeRaw);

        if (isNvme) {
            if (!pm.moduleVariables.has('usb_nvme_device')) setOrUnset('usb_nvme_device', device || name);
            if (model && !pm.moduleVariables.has('usb_nvme_model')) setOrUnset('usb_nvme_model', model);
            if (serial && !pm.moduleVariables.has('usb_nvme_serial')) setOrUnset('usb_nvme_serial', serial);
        } else if (isSata) {
            if (!pm.moduleVariables.has('usb_sata_device')) setOrUnset('usb_sata_device', device || name);
            if (model && !pm.moduleVariables.has('usb_sata_model')) setOrUnset('usb_sata_model', model);
            if (serial && !pm.moduleVariables.has('usb_sata_serial')) setOrUnset('usb_sata_serial', serial);
        } else {
            if (!pm.moduleVariables.has('usb_other_device')) setOrUnset('usb_other_device', device || name);
            if (model && !pm.moduleVariables.has('usb_other_model')) setOrUnset('usb_other_model', model);
            if (serial && !pm.moduleVariables.has('usb_other_serial')) setOrUnset('usb_other_serial', serial);
        }
    }
});

// 3. usb_ssd_device：USB中的SSD（优先取 usb_sata 或 usb_other，供 HyperCache 候选场景）
const ssd = pm.moduleVariables.has('usb_sata_device')
    ? pm.moduleVariables.get('usb_sata_device')
    : pm.moduleVariables.has('usb_other_device')
        ? pm.moduleVariables.get('usb_other_device')
        : pm.moduleVariables.get('usb_disk_device');
setOrUnset('usb_ssd_device', ssd);

console.log('GetDiskOption USB/SD分类同步完成');
