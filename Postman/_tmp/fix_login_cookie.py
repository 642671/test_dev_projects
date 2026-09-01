#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 02 用户登录 的后置脚本改为从登录响应 Set-Cookie 提取会话字段，
替代 Apifox 自动捕获 Cookie 的 pm.variables 读取。可反复运行。"""
import re
import yaml

PATH = r"D:\test_dev_projects\Postman\postman\collections\TEST-TNAS\02 登录\02 用户登录.request.yaml"

OLD = re.compile(
    r"(?s)// 获取变量.*?const csrfToken = pm\.variables\.get\(\"X-Csrf-Token\"\);"
)

NEW = ("// 从登录响应 Set-Cookie 提取会话字段（替代 Apifox 自动捕获 Cookie）\r\n"
       "const setCookie = pm.response.headers.get('Set-Cookie');\r\n"
       "console.log('Set-Cookie:', setCookie);\r\n"
       "console.log('LOGIN-headers:', JSON.stringify(pm.response.headers.toObject()));\r\n"
       "console.log('LOGIN-body:', (pm.response.text() || '').slice(0, 600));\r\n"
       "function cookieVal(name) {\r\n"
       "  if (!setCookie) { return null; }\r\n"
       "  const parts = String(setCookie).split(';');\r\n"
       "  for (const p of parts) {\r\n"
       "    const idx = p.indexOf('=');\r\n"
       "    if (idx < 0) { continue; }\r\n"
       "    const k = p.slice(0, idx).trim();\r\n"
       "    if (k === name) { return p.slice(idx + 1).trim(); }\r\n"
       "  }\r\n"
       "  return null;\r\n"
       "}\r\n"
       "const tmsessname = cookieVal('TMSESSNAME') || pm.variables.get('TMSESSNAME');\r\n"
       "const tosCurrentUsername = cookieVal('tos_current_username') || cookieVal('userName') || pm.variables.get('tos_current_username');\r\n"
       "const csrfToken = cookieVal('X-Csrf-Token') || pm.variables.get('X-Csrf-Token');\r\n"
       "\r\n"
       "console.log('========== 超管登录信息 ==========');\r\n"
       "console.log('TMSESSNAME:', tmsessname);\r\n"
       "console.log('tos_current_username:', tosCurrentUsername);\r\n"
       "console.log('X-Csrf-Token:', csrfToken);")


def raw_str(s):
    # 把脚本写成 YAML 双引号字符串需要转义的反斜杠内容用文本表示
    return s


def main():
    with open(PATH, "r", encoding="utf-8") as fh:
        d = yaml.safe_load(fh)
    scripts = d["scripts"]
    for sc in scripts:
        if sc.get("type") == "afterResponse":
            code = sc["code"]
            if "setCookie" in code and "LOGIN-headers" not in code:
                anchor = "console.log('Set-Cookie:', setCookie);"
                ins = (anchor + "\r\n"
                       "console.log('LOGIN-headers:', JSON.stringify(pm.response.headers.toObject()));\r\n"
                       "console.log('LOGIN-body:', (pm.response.text() || '').slice(0, 600));")
                code = code.replace(anchor, ins)
                sc["code"] = code
                print("injected debug")
            else:
                print("skip (already has debug or no setCookie)")
            # 打印首 400 字符便于核对
            print("---- head ----")
            print(code[:400])
    with open(PATH, "w", encoding="utf-8") as fh:
        yaml.safe_dump(d, fh, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    main()
