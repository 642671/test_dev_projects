// ============================================================
// GET /v2/disk/GetDiskDetailData 后置脚本
// 功能：根据请求参数 device 反查磁盘索引 N，
//       先清空 diskN_model / diskN_serial，再写入新值
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行先清空本次对应的 diskN_model / diskN_serial
//   2. 有值就 set，没值就 unset，不残留空字符串
//   3. 变量命名与磁盘列表接口一致：diskN_model / diskN_serial
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

// 0. 从请求中提取 device → 反查索引 → 先清空对应变量
let reqDevice = '';
const queryDevice = pm.request.url.query.get('device');
if (queryDevice) {
    reqDevice = (typeof queryDevice === 'string') ? queryDevice : queryDevice.toString();
}
if (!reqDevice && pm.request.body) {
    try {
        const body = JSON.parse(pm.request.body.raw);
        reqDevice = (body.device || '').trim();
    } catch (e) { /* 忽略 */ }
}

let diskIndex = null;
if (reqDevice) {
    const allVars = pm.moduleVariables.toObject();
    for (const [key, value] of Object.entries(allVars)) {
        const match = key.match(/^disk(\d+)_device$/);
        if (match && String(value).trim() === reqDevice.trim()) {
            diskIndex = parseInt(match[1], 10);
            break;
        }
    }
}

if (diskIndex !== null) {
    pm.moduleVariables.unset(`disk${diskIndex}_model`);
    pm.moduleVariables.unset(`disk${diskIndex}_serial`);
    pm.moduleVariables.unset(`disk${diskIndex}_type`);
    pm.moduleVariables.unset(`disk${diskIndex}_capacity`);
    pm.moduleVariables.unset(`disk${diskIndex}_slot`);
    console.log(`已清空 disk${diskIndex}_model / disk${diskIndex}_serial（准备写入新值）`);
} else {
    console.warn(`未在模块变量中找到 device=${reqDevice} 对应的 diskN_device，跳过清理`);
}

// 1. 响应结构校验
pm.test('响应结构正确（包含 model 和 serial）', () => {
    pm.expect(data).to.have.property('model');
    pm.expect(data).to.have.property('serial');
});

// 2. 写入 diskN_model / diskN_serial（及补充字段）
if (diskIndex !== null) {
    setOrUnset(`disk${diskIndex}_model`,    (data.model  || '').trim());
    setOrUnset(`disk${diskIndex}_serial`,   (data.serial || '').trim());
    setOrUnset(`disk${diskIndex}_type`,     (data.type   || '').trim());
    setOrUnset(`disk${diskIndex}_capacity`, data.factory_capacity || '');
    setOrUnset(`disk${diskIndex}_slot`,     data.slot);

    console.log(`disk${diskIndex}_model  = ${data.model}`);
    console.log(`disk${diskIndex}_serial = ${data.serial}`);
}
