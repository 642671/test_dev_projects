def role = (Parameters ?: '').trim()
def lines = []
def publicValue = vars.get("${role}_public_key")
def csrfValue = vars.get("${role}_csrf_token")
lines.add("===== ${role} /tos/ 获取公钥与令牌：本次新增变量 =====")
lines.add("${role}_public_key = " + (publicValue ?: 'NOT_FOUND'))
lines.add("${role}_csrf_token = " + (csrfValue ?: 'NOT_FOUND'))
def hasValue = publicValue && publicValue != 'NOT_FOUND' && csrfValue && csrfValue != 'NOT_FOUND'
def status = hasValue ? 'OK' : 'FAIL'
lines.add('状态 = ' + status + '（仅表示变量提取状态）')
SampleResult.setResponseData(lines.join('\n'), 'UTF-8')
SampleResult.setResponseMessage('新增变量摘要 ' + status)
SampleResult.setSuccessful(hasValue)
