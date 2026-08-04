// ============================================================
// POST /v2/extStorageDevice/MountedDevice 前置脚本
// 调用 encoderLoginPassword.go 加密 password
// ============================================================

var plainPassword = pm.environment.get('usb_password') || 'Admin123';
var base64Key = pm.environment.get('RSA_PUBLIC_KEY');

if (!base64Key) {
    console.log('RSA_PUBLIC_KEY 未设置，跳过加密');
} else {
    var publicKey = require('atob')(base64Key);
    var encrypted = await pm.executeAsync('encoderLoginPassword.go', [plainPassword, publicKey]);
    console.log('加密完成，长度:', encrypted.length);

    // 遍历 formdata 并构造新数组（避免引用未生效）
    var fd = pm.request.body.formdata;
    if (fd) {
        var newFd = [];
        for (var i = 0; i < fd.length; i++) {
            var item = { key: fd[i].key, value: fd[i].value, type: fd[i].type || 'text' };
            if (item.key === 'password') {
                item.value = encrypted;
                console.log('password 已替换');
            }
            newFd.push(item);
        }
        pm.request.body.formdata = newFd;
    } else {
        console.log('formdata 不存在, mode=', pm.request.body.mode);
    }
}
