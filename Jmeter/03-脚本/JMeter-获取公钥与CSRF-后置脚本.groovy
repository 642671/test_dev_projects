def role = (Parameters ?: '').trim()
if (!role) {
    throw new Exception('JSR223 参数值未设置角色，例如：super_admin / admin / user')
}

def headers = prev.getResponseHeaders()
String publicKey = ''
String csrf = ''

headers.eachLine { line ->
    def mRsa = line =~ /(?i)^\s*X-Rsa-Token:\s*(.+)$/
    if (mRsa.find()) {
        publicKey = mRsa.group(1).trim()
    }

    def mHeaderCsrf = line =~ /(?i)^\s*X-Csrf-Token:\s*(.+)$/
    if (mHeaderCsrf.find()) {
        csrf = mHeaderCsrf.group(1).trim()
    }

    def mSetCsrf = line =~ /(?i)^\s*Set-Cookie:\s*X-Csrf-Token=([^;]+)/
    if (mSetCsrf.find()) {
        csrf = mSetCsrf.group(1).trim()
    }
}

vars.put("${role}_public_key", publicKey ? publicKey : 'NOT_FOUND')
vars.put("${role}_csrf_token", csrf ? csrf : 'NOT_FOUND')
log.info("${role} 公钥长度=" + publicKey.length())
log.info("${role} CSRF=" + csrf)
