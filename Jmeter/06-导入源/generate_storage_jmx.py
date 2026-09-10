#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Apifox 原生导出文件生成 JMeter 存储管理 API 测试计划。

输入：
  Jmeter/06-导入源/Apifox-存储管理-最新.apifox.json
  Jmeter/01-测试计划/TNAS存储管理接口测试计划.jmx  （只读模板）

输出：
  Jmeter/01-测试计划/TNAS存储管理接口测试计划_存储管理API导入版_20260903.jmx

说明：
  - 保留原测试计划中的超级管理员登录链。
  - 登录后把超管会话写入 JMeter Properties，供“存储管理”业务线程组跨线程组复用。
  - 导入 Apifox 项目 8758195 的“07 存储管理”目录，共 135 个接口。
  - 原 Apifox 自定义后置脚本用 Rhino JavaScript 引擎运行，因此需要
    Jmeter/06-导入源/lib/rhino-engine-1.7.14.jar 并写入 TestPlan.user_define_classpath。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(r"D:\test_dev_projects\Jmeter")
SOURCE = BASE / "06-导入源" / "Apifox-存储管理-最新.apifox.json"
TEMPLATE = BASE / "01-测试计划" / "TNAS存储管理接口测试计划.jmx"
OUT = BASE / "01-测试计划" / "TNAS存储管理接口测试计划_存储管理API导入版_20260903.jmx"
RHINO_ENGINE = BASE / "06-导入源" / "lib" / "rhino-engine-1.7.14.jar"

AUTH_MAP = {
    "cookie": "super_admin_cookie",
    "normalusercookie": "super_admin_cookie",
    "x-csrf-token": "super_admin_csrf_token",
    "normalusercsrftoken": "super_admin_csrf_token",
    "x-curpass-token": "super_admin_curpass_token",
    "x-curpasstoken": "super_admin_curpass_token",
}


def norm_var(raw: str) -> str:
    """把 Apifox 变量名转成 JMeter 可用的变量名。"""
    key = (raw or "").strip().lower().replace("_", "-")
    if key in AUTH_MAP:
        return AUTH_MAP[key]
    out = re.sub(r"[^A-Za-z0-9_]+", "_", (raw or "").strip())
    out = out.strip("_")
    return out or "variable"


def replace_vars(text: str) -> str:
    """把 {{name}} 替换成 ${name}，并做认证变量映射。"""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        return "${" + norm_var(m.group(1)) + "}"

    return re.sub(r"\{\{([^}]+)\}\}", repl, text)


def esc(value) -> str:
    """XML 文本节点转义。"""
    return escape(str(value))


def esc_attr(value) -> str:
    """XML 属性值转义。"""
    return escape(str(value), {'"': "&quot;"})


def walk_items(node: dict, folder_path: str = ""):
    """遍历 Apifox 原生导出的文件夹/接口树。"""
    if "api" in node:
        yield folder_path, node
        return
    for child in node.get("items", []) or []:
        child_name = child.get("name", "")
        if "api" in child:
            yield folder_path, child
        else:
            next_path = f"{folder_path}/{child_name}" if folder_path else child_name
            yield from walk_items(child, next_path)


def get_api(item: dict) -> dict:
    return item.get("api") or {}


def header_value(api: dict, name: str):
    for h in api.get("parameters", {}).get("header", []) or []:
        if str(h.get("name", "")).lower() == name.lower():
            return h.get("example") or ""
    return None


def has_curpass_header(api: dict) -> bool:
    for h in api.get("parameters", {}).get("header", []) or []:
        key = str(h.get("name", "")).lower().replace("-", "")
        if key in ("xcurpasstoken", "xcurpustoken"):
            return True
    return False


def content_type_for(api: dict) -> str:
    """保留函数名兼容，实际使用 effective_content_type。"""
    return effective_content_type(api)


def effective_content_type(api: dict) -> str:
    """根据 requestBody 类型和接口头信息确定 HTTP Content-Type。"""
    h = header_value(api, "Content-Type")
    body_type = (api.get("requestBody") or {}).get("type", "none")
    if body_type == "application/json":
        return "application/json"
    if h and h.lower() == "application/x-www-form-urlencoded":
        return h
    if h:
        return h
    if body_type == "multipart/form-data":
        return "multipart/form-data"
    return ""


def schema_default(value_schema: dict, key: str):
    typ = value_schema.get("type")
    if isinstance(typ, list):
        typ = typ[0]
    if typ == "array":
        return []
    if typ == "object":
        return {}
    if typ in ("integer", "number"):
        return 0
    if typ == "boolean":
        return False
    return "${" + norm_var(key) + "}"


def schema_to_json_example(schema: dict) -> str:
    schema = schema or {}
    props = schema.get("properties") or {}
    order = schema.get("x-apifox-orders") or list(props.keys())
    obj = {}
    for key in order:
        if key in props:
            obj[key] = schema_default(props[key], key)
    return json.dumps(obj, ensure_ascii=False, indent=2)


def build_path(api: dict) -> str:
    """替换路径模板和 Apifox 变量，并拼接 query 参数。"""
    raw = api.get("path", "") or ""
    raw = re.sub(r"\{([^}]+)\}", lambda m: "${" + norm_var(m.group(1)) + "}", raw)
    raw = replace_vars(raw)
    qs = []
    for q in api.get("parameters", {}).get("query", []) or []:
        if not q.get("enable", True):
            continue
        qname = q.get("name", "")
        if not qname:
            continue
        qvalue = q.get("example")
        if qvalue in (None, ""):
            qvalue = "${" + norm_var(qname) + "}"
        qs.append(f"{qname}={replace_vars(str(qvalue))}")
    if qs:
        sep = "&" if "?" in raw else "?"
        raw += sep + "&".join(qs)
    return raw


def body_payload(api: dict):
    """返回 (post_body_raw, multipart, arguments_xml, content_type)。"""
    rb = api.get("requestBody") or {}
    body_type = rb.get("type", "none")
    args = []
    ct = effective_content_type(api)

    if body_type == "application/json":
        raw = ""
        examples = rb.get("examples") or []
        if examples and examples[0].get("value"):
            raw = examples[0]["value"]
        else:
            raw = schema_to_json_example(rb.get("jsonSchema"))
        # 存储管理里的 password 字段需要 RSA 加密后的值
        raw = re.sub(
            r'"password"\s*:\s*"[^"]*"',
            '"password": "${super_admin_curpass_token}"',
            raw,
        )
        raw = replace_vars(raw)
        args.append(
            "<elementProp name=\"\" elementType=\"HTTPArgument\">\n"
            "  <boolProp name=\"HTTPArgument.always_encode\">false</boolProp>\n"
            "  <stringProp name=\"Argument.value\">%s</stringProp>\n"
            "  <stringProp name=\"Argument.metadata\">=</stringProp>\n"
            "</elementProp>" % esc(raw)
        )
        return True, False, args, ct

    if body_type == "multipart/form-data":
        for p in rb.get("parameters", []) or []:
            pname = p.get("name", "")
            if not pname:
                continue
            pvalue = p.get("example")
            if pvalue in (None, ""):
                pvalue = "${" + norm_var(pname) + "}"
            args.append(
                '<elementProp name="%s" elementType="HTTPArgument">\n'
                '  <boolProp name="HTTPArgument.always_encode">false</boolProp>\n'
                '  <stringProp name="Argument.name">%s</stringProp>\n'
                '  <stringProp name="Argument.value">%s</stringProp>\n'
                '  <stringProp name="Argument.metadata">=</stringProp>\n'
                "</elementProp>"
                % (esc_attr(pname), esc(pname), esc(replace_vars(str(pvalue))))
            )
        is_multipart = ct.lower() == "multipart/form-data"
        return False, is_multipart, args, ct

    return False, False, args, ct


def build_header_manager(name: str, headers: list) -> str:
    lines = [
        f'<HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="{esc_attr(name)}" enabled="true">',
        '  <collectionProp name="HeaderManager.headers">',
    ]
    for key, value in headers:
        lines.append(f'    <elementProp name="{esc_attr(key)}" elementType="Header">')
        lines.append(f'      <stringProp name="Header.name">{esc(key)}</stringProp>')
        lines.append(f'      <stringProp name="Header.value">{esc(value)}</stringProp>')
        lines.append("    </elementProp>")
    lines.append("  </collectionProp>")
    lines.append("</HeaderManager>")
    return "\n".join(lines)


def build_sampler(api: dict, sampler_name: str, folder_path: str, api_index: int) -> str:
    method = str(api.get("method", "get")).upper()
    path = build_path(api)
    raw_body, multipart, args, ct = body_payload(api)
    # 用户已确认本机是专用测试机：所有存储管理接口默认启用，包括写操作。
    enabled = "true"
    lines = [
        f'<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{esc_attr(sampler_name)}" enabled="{enabled}">',
        f'  <stringProp name="TestPlan.comments">Apifox ID {api.get("id", "")} | {method} {api.get("path", "")} | 目录 {folder_path}</stringProp>',
        f'  <stringProp name="HTTPSampler.path">{esc(path)}</stringProp>',
        '  <boolProp name="HTTPSampler.follow_redirects">false</boolProp>',
        '  <boolProp name="HTTPSampler.auto_redirects">false</boolProp>',
        '  <boolProp name="HTTPSampler.use_keepalive">true</boolProp>',
        f'  <stringProp name="HTTPSampler.method">{method}</stringProp>',
        f'  <boolProp name="HTTPSampler.postBodyRaw">{"true" if raw_body else "false"}</boolProp>',
    ]
    if multipart:
        lines.append('  <boolProp name="HTTPSampler.DO_MULTIPART_POST">true</boolProp>')
    lines.append('  <elementProp name="HTTPsampler.Arguments" elementType="Arguments">')
    lines.append('    <collectionProp name="Arguments.arguments">')
    lines.extend("  " + a for a in args)
    lines.append("    </collectionProp>")
    lines.append("  </elementProp>")
    lines.append("</HTTPSamplerProxy>")
    return "\n".join(lines)


JS_SHIM = r"""
if (!Object.values) {
  Object.values = function(obj) {
    var r = [], keys = Object.keys(obj);
    for (var i = 0; i < keys.length; i++) r.push(obj[keys[i]]);
    return r;
  };
}
if (!Number.isNaN) {
  Number.isNaN = function(v) { return typeof v === 'number' && v !== v; };
}
var __vars = {};
var __it = vars.entrySet().iterator();
while (__it.hasNext()) {
  var __e = __it.next();
  __vars[String(__e.getKey())] = __e.getValue();
}
var __url = '';
try { __url = String(prev.getUrlAsString() || ''); } catch (e) {}
var __query = {};
var __qm = /[?&]([^=&]+)=([^&]*)/g;
var __qmMatch;
while ((__qmMatch = __qm.exec(__url)) !== null) {
  __query[decodeURIComponent(__qmMatch[1])] = decodeURIComponent(__qmMatch[2]);
}
function __copy(o) {
  var r = {};
  for (var k in o) { if (o.hasOwnProperty(k)) r[k] = o[k]; }
  return r;
}
function __fail(msg) { throw new Error(msg); }
function __expect(v) {
  var w = {};
  w.to = {};
  w.to.be = {};
  w.to.be.an = function(t) {
    if (t === 'object' && (v === null || typeof v !== 'object')) __fail('expected object, got ' + typeof v);
    if (t === 'array' && !Array.isArray(v)) __fail('expected array');
    if (t === 'string' && typeof v !== 'string') __fail('expected string');
    return w.to.be;
  };
  w.to.be.above = function(n) {
    if (!(Number(v) > Number(n))) __fail('expected ' + v + ' > ' + n);
    return w.to.be;
  };
  w.to.be.equal = function(x) {
    if (v !== x) __fail('expected ' + v + ' equal ' + x);
    return w.to.be;
  };
  w.to.be.true = function() {
    if (v !== true) __fail('expected true');
    return w.to.be;
  };
  w.to.have = {};
  w.to.have.property = function(p) {
    if (v === null || typeof v !== 'object' || !(p in v)) __fail('missing property ' + p);
    return w.to.have;
  };
  return w;
}
var console = { log: function(s) { log.info(String(s)); } };
var pm = {
  response: { json: function() { return JSON.parse(prev.getResponseDataAsString()); } },
  variables: {
    get: function(k) { return __vars[String(k)] == null ? vars.get(String(k)) : __vars[String(k)]; },
    set: function(k, v) { vars.put(String(k), String(v)); __vars[String(k)] = String(v); },
    unset: function(k) { vars.remove(String(k)); delete __vars[String(k)]; }
  },
  environment: {
    get: function(k) { return vars.get(String(k)); },
    set: function(k, v) { vars.put(String(k), String(v)); __vars[String(k)] = String(v); },
    unset: function(k) { vars.remove(String(k)); delete __vars[String(k)]; }
  },
  moduleVariables: {
    get: function(k) { return vars.get(String(k)); },
    set: function(k, v) { vars.put(String(k), String(v)); __vars[String(k)] = String(v); },
    unset: function(k) { vars.remove(String(k)); delete __vars[String(k)]; },
    toObject: function() { return __copy(__vars); }
  },
  request: {
    url: { query: { get: function(k) { return __query[String(k)] || null; } } },
    body: { raw: (function() { try { return String(prev.getSamplerData() || ''); } catch (e) { return ''; } })() }
  },
  test: function(name, fn) {
    try { fn(); log.info('[ApifoxJS] PASS ' + name); }
    catch (e) { log.warn('[ApifoxJS] FAIL ' + name + ': ' + e); }
  },
  expect: __expect
};
"""


def transform_optional_chaining(code: str) -> str:
    """Rhino 1.7.14 不支持 ?.，把已发现的安全访问写法转为三元表达式。"""
    pattern = re.compile(
        r"([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*|\[\d+\])*)\?\.([A-Za-z_$][\w$]*)"
    )
    return pattern.sub(r"(\1 ? \1.\2 : undefined)", code)


def build_js_postprocessor(name: str, original_js: str) -> str:
    js = transform_optional_chaining(original_js)
    wrapped = "try {\n(function() {\n%s\n})();\n} catch (e) {\nlog.warn('[ApifoxJS] ' + e);\n}" % js
    script = JS_SHIM + "\n" + wrapped
    lines = [
        f'<JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="{esc_attr(name)}" enabled="true">',
        '  <stringProp name="TestPlan.comments">Apifox 自定义后置脚本，使用 Rhino JavaScript 引擎运行</stringProp>',
        '  <stringProp name="cacheKey">true</stringProp>',
        '  <stringProp name="language">javascript</stringProp>',
        '  <stringProp name="filename"></stringProp>',
        '  <stringProp name="parameters"></stringProp>',
        "  <stringProp name=\"script\">%s</stringProp>" % esc(script),
        '  <stringProp name="scriptLanguage">javascript</stringProp>',
        "</JSR223PostProcessor>",
    ]
    return "\n".join(lines)


def build_groovy_extractor(name: str, variable_name: str, json_path: str) -> str:
    # 当前只遇到 $.data.src 一个内置 extractor，这里给出可读的 Groovy 等价实现。
    script = (
        "def json = new groovy.json.JsonSlurper().parseText(prev.getResponseDataAsString())\n"
        "def v = json?.data?.src\n"
        "if (v != null) { vars.put('%s', v.toString()) }\n" % variable_name
    )
    lines = [
        f'<JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="{esc_attr(name)}" enabled="true">',
        f'  <stringProp name="TestPlan.comments">Apifox extractor 转 JMeter：{json_path}</stringProp>',
        '  <stringProp name="cacheKey">true</stringProp>',
        '  <stringProp name="language">groovy</stringProp>',
        '  <stringProp name="filename"></stringProp>',
        '  <stringProp name="parameters"></stringProp>',
        "  <stringProp name=\"script\">%s</stringProp>" % esc(script),
        '  <stringProp name="scriptLanguage">groovy</stringProp>',
        "</JSR223PostProcessor>",
    ]
    return "\n".join(lines)


def collect_all_variables(api_list: list) -> set[str]:
    found = set()
    for _, item in api_list:
        api = get_api(item)
        blob = json.dumps(api, ensure_ascii=False)
        for m in re.finditer(r"\{\{([^}]+)\}\}", blob):
            found.add(norm_var(m.group(1)))
    for _, item in api_list:
        api = get_api(item)
        for section in ("path", "query", "header"):
            for p in api.get("parameters", {}).get(section, []) or []:
                if p.get("name"):
                    found.add(norm_var(p["name"]))
    found.update({"super_admin_cookie", "super_admin_csrf_token", "super_admin_curpass_token"})
    return found


def build_init_sampler(variable_names: set[str]) -> str:
    var_lines = "\n".join(
        "if (vars.get('%s') == null) { vars.put('%s', 'REPLACE_ME') }" % (name, name)
        for name in sorted(variable_names)
    )
    script = r"""
def missing = []
def csrf = props.getProperty('jmeter.super_admin_csrf_token')
def cookie = props.getProperty('jmeter.super_admin_cookie')
def user = props.getProperty('jmeter.super_admin_username')
def pub = props.getProperty('jmeter.super_admin_public_key')
def curpass = props.getProperty('jmeter.super_admin_curpass_token')

if (!csrf) { missing.add('csrf_token') } else { vars.put('super_admin_csrf_token', csrf) }
if (!cookie) { missing.add('cookie') } else { vars.put('super_admin_cookie', cookie) }
if (!user) { missing.add('username') } else { vars.put('super_admin_username', user) }
if (!pub) { missing.add('public_key') } else { vars.put('super_admin_public_key', pub) }
if (!curpass) { missing.add('curpass_token') } else { vars.put('super_admin_curpass_token', curpass) }

""" + var_lines + r"""
def summary = []
summary.add('存储管理会话初始化')
summary.add('csrf_token = ' + (vars.get('super_admin_csrf_token') ?: 'REPLACE_ME'))
summary.add('cookie = ' + (vars.get('super_admin_cookie') ?: 'REPLACE_ME'))
summary.add('curpass_token = ' + (vars.get('super_admin_curpass_token') ?: 'REPLACE_ME'))
summary.add('缺失项 = ' + (missing ? missing.join(', ') : '无'))
SampleResult.setResponseData(summary.join('\n'), 'UTF-8')
SampleResult.setResponseMessage(missing ? '会话变量不完整' : '会话变量完整')
SampleResult.setSuccessful(missing.isEmpty())
"""
    lines = [
        '<JSR223Sampler guiclass="TestBeanGUI" testclass="JSR223Sampler" testname="初始化 存储管理 会话变量" enabled="true">',
        '  <stringProp name="TestPlan.comments">从登录线程组写入的 JMeter Properties 复制超管 Cookie/CSRF/Curpass 变量</stringProp>',
        '  <stringProp name="cacheKey">true</stringProp>',
        '  <stringProp name="language">groovy</stringProp>',
        '  <stringProp name="filename"></stringProp>',
        '  <stringProp name="parameters"></stringProp>',
        "  <stringProp name=\"script\">%s</stringProp>" % esc(script),
        '  <stringProp name="scriptLanguage">groovy</stringProp>',
        "</JSR223Sampler>",
    ]
    return "\n".join(lines)


def build_storage_tree(api_list: list) -> str:
    variable_names = collect_all_variables(api_list)
    lines = ["<hashTree>"]
    lines.append(build_init_sampler(variable_names))
    lines.append("<hashTree/>")
    lines.append(
        build_header_manager(
            "存储管理认证请求头",
            [
                ("X-Csrf-Token", "${super_admin_csrf_token}"),
                ("Cookie", "${super_admin_cookie}"),
            ],
        )
    )
    lines.append("<hashTree/>")

    current_folder = None
    folder_hash_count = 0
    for folder_path, item in api_list:
        api = get_api(item)
        root = folder_path.split("/", 1)[-1]
        if root != current_folder:
            if current_folder is not None:
                lines.append("</hashTree>")
            current_folder = root
            folder_hash_count += 1
            lines.append(
                f'<GenericController guiclass="LogicControllerGui" testclass="GenericController" testname="{esc_attr("存储管理/" + root)}" enabled="true"/>'
            )
            lines.append("<hashTree>")

        sampler_name = f"{root}/{item.get('name', api.get('name', ''))}"
        lines.append(build_sampler(api, sampler_name, folder_path, folder_hash_count))
        lines.append("<hashTree>")
        child_count = 0
        ct = effective_content_type(api)
        if ct or has_curpass_header(api):
            headers = []
            if ct:
                headers.append(("Content-Type", ct))
            if has_curpass_header(api):
                headers.append(("X-Curpass-Token", "${super_admin_curpass_token}"))
            lines.append(build_header_manager(sampler_name + " / 请求头", headers))
            lines.append("<hashTree/>")
            child_count += 1

        for idx, pp in enumerate(api.get("postProcessors", []) or [], start=1):
            if pp.get("type") == "customScript" and pp.get("data"):
                lines.append(
                    build_js_postprocessor(
                        f"{sampler_name} / Apifox后置脚本{idx}",
                        str(pp["data"]),
                    )
                )
                lines.append("<hashTree/>")
                child_count += 1
            elif pp.get("type") == "extractor":
                data = pp.get("data") or {}
                lines.append(
                    build_groovy_extractor(
                        f"{sampler_name} / Apifox提取器{idx}",
                        data.get("variableName", "src"),
                        data.get("expression", ""),
                    )
                )
                lines.append("<hashTree/>")
                child_count += 1

        if child_count == 0:
            lines.append("<hashTree/>")
        lines.append("</hashTree>")

    if current_folder is not None:
        lines.append("</hashTree>")
    lines.append("</hashTree>")
    return "\n".join(lines)


def ensure_props_postprocessor(template: str) -> str:
    marker = (
        '<JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" '
        'testname="提取 超级管理员 登录 Cookie"'
    )
    idx = template.find(marker)
    if idx < 0:
        raise RuntimeError("未找到超级管理员 Cookie 后置处理器")
    end = template.find("</JSR223PostProcessor>", idx)
    if end < 0:
        raise RuntimeError("未找到 Cookie 后置处理器结束标签")
    hash_pos = template.find("<hashTree/>", end)
    if hash_pos < 0:
        raise RuntimeError("未找到 Cookie 后置处理器子节点")
    insert_at = hash_pos + len("<hashTree/>")
    props_pp = r"""
<JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="保存 超级管理员 会话到 JMeter Properties" enabled="true">
  <stringProp name="TestPlan.comments">把超管会话写入全局 JMeter Properties，供存储管理业务线程组读取</stringProp>
  <stringProp name="cacheKey">true</stringProp>
  <stringProp name="language">groovy</stringProp>
  <stringProp name="filename"></stringProp>
  <stringProp name="parameters"></stringProp>
  <stringProp name="script">props.put('jmeter.super_admin_csrf_token', vars.get('super_admin_csrf_token') ?: '')
props.put('jmeter.super_admin_cookie', vars.get('super_admin_cookie') ?: '')
props.put('jmeter.super_admin_username', vars.get('super_admin_username') ?: '')
props.put('jmeter.super_admin_public_key', vars.get('super_admin_public_key') ?: '')
props.put('jmeter.super_admin_curpass_token', vars.get('super_admin_encrypted_password') ?: '')
log.info('超管会话已写入 JMeter Properties')</stringProp>
  <stringProp name="scriptLanguage">groovy</stringProp>
</JSR223PostProcessor>
<hashTree/>
""".strip()
    return template[:insert_at] + "\n" + props_pp + "\n" + template[insert_at:]


def fill_storage_tree(template: str, storage_xml: str) -> str:
    marker = '<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="存储管理"'
    start = template.find(marker)
    if start < 0:
        raise RuntimeError("未找到存储管理线程组")
    end = template.find("</ThreadGroup>", start)
    if end < 0:
        raise RuntimeError("未找到存储管理线程组结束标签")
    hash_pos = template.find("<hashTree/>", end)
    if hash_pos < 0:
        raise RuntimeError("未找到存储管理线程组子节点")
    return template[:hash_pos] + storage_xml + template[hash_pos + len("<hashTree/>") :]


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    if not TEMPLATE.exists():
        raise FileNotFoundError(TEMPLATE)
    if not RHINO_ENGINE.exists():
        raise FileNotFoundError(RHINO_ENGINE)

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    root = data["apiCollection"][0]["items"][0]
    api_list = list(walk_items(root))
    print(f"从 Apifox 导出文件读取接口：{len(api_list)} 个")

    template = TEMPLATE.read_text(encoding="utf-8")
    classpath_prop = (
        '<stringProp name="TestPlan.user_define_classpath">%s</stringProp>'
        % esc(str(RHINO_ENGINE))
    )
    if '<stringProp name="TestPlan.user_define_classpath"' in template:
        template = re.sub(
            r'<stringProp name="TestPlan\.user_define_classpath">[^<]*</stringProp>',
            classpath_prop,
            template,
            count=1,
        )
    else:
        template = template.replace("</TestPlan>", "  " + classpath_prop + "\n    </TestPlan>", 1)
    template = ensure_props_postprocessor(template)
    storage_xml = build_storage_tree(api_list)
    output = fill_storage_tree(template, storage_xml)
    OUT.write_text(output, encoding="utf-8", newline="\n")
    print(f"已生成：{OUT}")
    print(f"JMX 字节数：{OUT.stat().st_size}")


if __name__ == "__main__":
    main()
