def role = (Parameters ?: '').trim()
if (!role) {
    throw new Exception('JSR223 参数值未设置角色，例如：super_admin / admin / user')
}

def responseHeaders = prev.getResponseHeaders() ?: ''
def requestHeaders = prev.getRequestHeaders() ?: ''

def setCookies = [:]
def setCookieMatcher = responseHeaders =~ /(?i)Set-Cookie:\s*([^;\r\n=]+)=([^;\r\n]+)/
while (setCookieMatcher.find()) {
    setCookies[setCookieMatcher.group(1).trim()] = setCookieMatcher.group(2).trim()
}

String responseCsrf = ''
responseHeaders.eachLine { line ->
    def m = line =~ /(?i)^\s*X-Csrf-Token:\s*(.+)$/
    if (m.find()) {
        responseCsrf = m.group(1).trim()
    }
}

def reqCookies = [:]
String cookieLine = ''
requestHeaders.eachLine { line ->
    def m = line =~ /(?i)^\s*Cookie:\s*(.+?)\s*$/
    if (m.find()) {
        cookieLine = m.group(1).trim()
    }
}
cookieLine.split(';').each { part ->
    def kv = part.trim().split('=', 2)
    if (kv.length == 2) {
        reqCookies[kv[0].trim()] = kv[1].trim()
    }
}

String userName = reqCookies['userName'] ?: setCookies['userName'] ?: vars.get("${role}_username") ?: 'NOT_FOUND'
String tms = setCookies['TMSESSNAME'] ?: reqCookies['TMSESSNAME'] ?: 'NOT_FOUND'
String csrf = responseCsrf ?: setCookies['X-Csrf-Token'] ?: reqCookies['X-Csrf-Token'] ?: vars.get("${role}_csrf_token") ?: 'NOT_FOUND'
String loginStatus = reqCookies['loginStatus'] ?: setCookies['loginStatus'] ?: 'true'
String tosUser = setCookies['tos_current_username'] ?: reqCookies['tos_current_username'] ?: userName

def cookieValue = "userName=${userName}; TMSESSNAME=${tms}; X-Csrf-Token=${csrf}; loginStatus=${loginStatus}; tos_current_username=${tosUser}"

vars.put("${role}_cookie_userName", userName)
vars.put("${role}_cookie_TMSESSNAME", tms)
vars.put("${role}_csrf_token", csrf)
vars.put("${role}_cookie_loginStatus", loginStatus)
vars.put("${role}_cookie_tos_current_username", tosUser)
vars.put("${role}_cookie", cookieValue)

if (csrf == 'NOT_FOUND') {
    log.warn("${role} 未提取到 X-Csrf-Token")
}
if (tms == 'NOT_FOUND') {
    log.warn("${role} 未提取到 TMSESSNAME")
}
log.info("${role} Cookie 提取完成，TMSESSNAME=" + tms)
