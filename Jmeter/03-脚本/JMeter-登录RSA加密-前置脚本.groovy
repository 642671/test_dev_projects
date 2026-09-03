import java.security.KeyFactory
import java.security.spec.X509EncodedKeySpec
import java.util.Base64
import javax.crypto.Cipher

def role = (Parameters ?: '').trim()
if (!role) {
    throw new Exception('JSR223 参数值未设置角色，例如：super_admin / admin / user')
}

String base64Pem = vars.get("${role}_public_key")
if (base64Pem == null || base64Pem.isEmpty() || base64Pem == 'NOT_FOUND') {
    throw new Exception("${role} 未获取到 X-Rsa-Token 公钥")
}

String pem = new String(Base64.getMimeDecoder().decode(base64Pem), 'UTF-8')

boolean inKey = false
StringBuilder pemBody = new StringBuilder()
pem.eachLine { line ->
    String trimmed = line.trim()
    if (trimmed.startsWith('-----BEGIN')) {
        inKey = true
        return
    }
    if (trimmed.startsWith('-----END')) {
        inKey = false
        return
    }
    if (inKey && trimmed) {
        pemBody.append(trimmed)
    }
}

String body = pemBody.toString()
if (!body) {
    throw new Exception("${role} PEM 正文为空")
}

byte[] der = Base64.getMimeDecoder().decode(body)
KeyFactory keyFactory = KeyFactory.getInstance('RSA')
def publicKey = keyFactory.generatePublic(new X509EncodedKeySpec(der))

Cipher cipher = Cipher.getInstance('RSA/ECB/PKCS1Padding')
cipher.init(Cipher.ENCRYPT_MODE, publicKey)

String plainPassword = vars.get("${role}_password")
if (plainPassword == null || plainPassword.isEmpty()) {
    throw new Exception("${role} 未配置密码")
}

byte[] encrypted = cipher.doFinal(plainPassword.getBytes('UTF-8'))
vars.put("${role}_encrypted_password", Base64.getEncoder().encodeToString(encrypted))
log.info("${role} RSA 登录密码加密成功，PEM正文长度=" + body.length() + "，密文长度=" + encrypted.length)
