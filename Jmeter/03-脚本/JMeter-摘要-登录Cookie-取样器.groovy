def role = (Parameters ?: '').trim()
def lines = []

def body = prev?.getResponseDataAsString() ?: ''
def isLogin = '未知'
def business = ''
try {
    def json = new groovy.json.JsonSlurper().parseText(body)
    isLogin = String.valueOf(json.is_login)
    business = String.valueOf(json.data ?: json.msg ?: '')
} catch (Exception e) {
    business = '响应不是 JSON'
}

def cookieValue = vars.get("${role}_cookie")
def csrfValue = vars.get("${role}_csrf_token")
def tmsValue = vars.get("${role}_cookie_TMSESSNAME")
def userNameValue = vars.get("${role}_cookie_userName")
def loginStatusValue = vars.get("${role}_cookie_loginStatus")
def tosUserValue = vars.get("${role}_cookie_tos_current_username")

lines.add("===== ${role} /v2/login 登录接口：本次新增变量 =====")
lines.add('接口响应 is_login = ' + isLogin)
lines.add('接口响应业务提示 = ' + business)
lines.add("${role}_cookie = " + (cookieValue ?: 'NOT_FOUND'))
lines.add("${role}_csrf_token = " + (csrfValue ?: 'NOT_FOUND'))
lines.add("${role}_cookie_TMSESSNAME = " + (tmsValue ?: 'NOT_FOUND'))
lines.add("${role}_cookie_userName = " + (userNameValue ?: 'NOT_FOUND'))
lines.add("${role}_cookie_loginStatus = " + (loginStatusValue ?: 'NOT_FOUND'))
lines.add("${role}_cookie_tos_current_username = " + (tosUserValue ?: 'NOT_FOUND'))

def hasValue = cookieValue && cookieValue != 'NOT_FOUND' && csrfValue && csrfValue != 'NOT_FOUND' && tmsValue && tmsValue != 'NOT_FOUND'
def status = hasValue ? 'OK' : 'FAIL'
lines.add('变量提取状态 = ' + status + '（仅表示变量提取状态）')
SampleResult.setResponseData(lines.join('\n'), 'UTF-8')
SampleResult.setResponseMessage('新增变量摘要 ' + status)
SampleResult.setSuccessful(hasValue)
