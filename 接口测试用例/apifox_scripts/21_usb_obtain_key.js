// ============================================================
// 21_usb_obtain_key.js
// POST /v2/extStorageDevice/ObtainSecretKey 后置脚本
// 产出 usb_key_data：Base64密钥文件路径（供 DownloadSecretKey 的 data 参数）
// 编码模式：全量同步（单值）+ 空值清除
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

// 兼容多种响应形态：data 可能是字符串、{data:...}、{path:...}、{key:...}、{secret_key:...}
let keyData = '';
if (typeof data === 'string') {
    keyData = data.trim();
} else if (data && typeof data === 'object') {
    keyData = (data.data || data.path || data.key || data.secret_key || data.file_path || data.url || '').toString().trim();
}

// 先清旧值再写（若新值为空则保持未设置）
pm.moduleVariables.unset('usb_key_data');
setOrUnset('usb_key_data', keyData);

console.log('usb_key_data = ' + (keyData ? keyData.substring(0, 40) + '...' : '(空/未设置)'));
