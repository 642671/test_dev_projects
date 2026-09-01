#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 Postman 本地文件工作区（目录树）中的集合导出为可被 `postman collection run`
直接运行的 V3 (v2.1 schema) 集合 JSON。

用法（在项目根执行，需要 PyYAML，本机用 py -3）:
    py -3 build_postman_collection.py <集合目录> [-o <输出.json>]
默认输出到 <集合目录>.collection.json（与集合目录同级）。

说明：
  - 集合/文件夹级脚本来自 .resources/definition.yaml 的 scripts
  - 请求级脚本来自 *.request.yaml 的 scripts
  - 保留 order 排序；支持 json / formdata / text 三种 body
  - pathVariables(:name) 会转成 url.variable
"""
import argparse
import json
import os
import sys
import uuid

try:
    import yaml
except ImportError:
    print("缺少 PyYAML，请先安装: py -3 -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)


SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
BIG = 10 ** 9


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _scripts_to_events(scripts):
    events = []
    for sc in scripts or []:
        stype = sc.get("type", "")
        code = sc.get("code", "") or ""
        lines = code.split("\n")
        lines = [ln.rstrip("\r") for ln in lines]
        clean = []
        for ln in lines:
            clean.append(ln)
        # 去掉首尾多余空行，但不影响脚本可读性
        if stype in ("beforeRequest", "http:beforeRequest", "prerequest"):
            events.append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": clean}})
        elif stype in ("afterResponse", "http:afterResponse", "test"):
            events.append({"listen": "test", "script": {"type": "text/javascript", "exec": clean}})
    return events


def _variables_to_arr(variables):
    if variables is None:
        return []
    if isinstance(variables, list):
        out = []
        for v in variables:
            if isinstance(v, dict):
                out.append({"key": v.get("key", ""), "value": v.get("value", ""), "type": v.get("type", "string"), "enabled": True})
            else:
                out.append({"key": v, "value": "", "type": "string", "enabled": True})
        return out
    # 形如 {X-Csrf-Token: ""}
    return [{"key": k, "value": v, "type": "string", "enabled": True} for k, v in variables.items()]


def _build_url(raw, path_vars):
    raw = (raw or "").strip()
    var_map = {pv.get("key"): pv.get("value", "") for pv in (path_vars or []) if isinstance(pv, dict)}

    # 拆 query
    base = raw
    query = []
    if "?" in raw:
        base, qs = raw.split("?", 1)
        for pair in qs.split("&"):
            if not pair:
                continue
            kv = pair.split("=", 1)
            query.append({"key": kv[0], "value": kv[1] if len(kv) > 1 else "", "disabled": False})

    # 拆 host / path。首个 segment 是 host（可能是 {{baseUrl}} 或 http://host）
    segs = base.split("/")
    hostpart = segs[0]
    path = [s for s in segs[1:] if s != ""]
    host = [hostpart]

    variable = []
    clean_path = []
    for p in path:
        if p.startswith(":"):
            key = p[1:]
            variable.append({"key": key, "value": var_map.get(key, ""), "description": None})
            clean_path.append(p)
        else:
            clean_path.append(p)

    url = {"raw": raw, "host": host, "path": clean_path, "query": query}
    if variable:
        url["variable"] = variable
    return url


def _parse_request(yaml_path):
    d = _load_yaml(yaml_path)
    name = os.path.basename(yaml_path)
    if name.endswith(".request.yaml"):
        name = name[: -len(".request.yaml")]

    req = {"method": (d.get("method") or "GET").upper()}

    # headers
    header = []
    for h in d.get("headers", []) or []:
        if not isinstance(h, dict):
            continue
        entry = {"key": h.get("key", ""), "value": h.get("value", ""), "type": "text"}
        if "description" in h and h.get("description"):
            entry["description"] = h["description"]
        header.append(entry)
    req["header"] = header

    # url
    req["url"] = _build_url(d.get("url", ""), d.get("pathVariables", []))

    # auth
    auth = d.get("auth")
    if auth and isinstance(auth, dict):
        atype = auth.get("type")
        if atype == "noauth":
            req["auth"] = {"type": "noauth"}
        elif atype:
            out = {"type": atype}
            # 常见字段透传
            for f in ("apikey", "basic", "bearer", "digest", "oauth2", "aws", "hawk"):
                if f in auth:
                    out[f] = auth[f]
            req["auth"] = out

    # body
    body = d.get("body")
    if body and isinstance(body, dict):
        btype = body.get("type")
        if btype == "json":
            content = body.get("content", "")
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            req["body"] = {"mode": "raw", "raw": content, "options": {"raw": {"language": "json"}}}
        elif btype == "formdata":
            formdata = []
            for item in body.get("content", []) or []:
                if not isinstance(item, dict):
                    continue
                fd = {"key": item.get("key"), "value": item.get("value", ""), "type": item.get("type", "text"), "enabled": True}
                if item.get("description"):
                    fd["description"] = item["description"]
                formdata.append(fd)
            req["body"] = {"mode": "formdata", "formdata": formdata}
        elif btype == "text":
            req["body"] = {"mode": "raw", "raw": body.get("content", "")}
        else:
            content = body.get("content", "")
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            req["body"] = {"mode": "raw", "raw": content}

    item = {"name": name, "request": req}

    # scripts -> event
    events = _scripts_to_events(d.get("scripts", []))
    if events:
        item["event"] = events

    order = d.get("order")
    return item, order


def _build_folder(dir_path):
    def_path = os.path.join(dir_path, ".resources", "definition.yaml")
    fdef = _load_yaml(def_path) if os.path.exists(def_path) else {}

    children = []
    for entry in sorted(os.listdir(dir_path)):
        if entry.startswith(".") or entry == ".resources":
            continue
        full = os.path.join(dir_path, entry)
        if os.path.isdir(full):
            child_item = _build_folder(full)
            order = child_item.get("order")
            children.append((order if order is not None else BIG, 1, child_item["item"]))
        elif entry.endswith(".request.yaml"):
            item, order = _parse_request(full)
            children.append((order if order is not None else BIG, 0, item))

    children.sort(key=lambda x: (x[0], x[1], x[2]["name"]))
    items = [c[2] for c in children]

    folder_item = {"name": fdef.get("name") or os.path.basename(dir_path), "item": items}
    events = _scripts_to_events(fdef.get("scripts", []))
    if events:
        folder_item["event"] = events
    vars_arr = _variables_to_arr(fdef.get("variables"))
    if vars_arr:
        folder_item["variable"] = vars_arr

    return {"order": fdef.get("order"), "item": folder_item}


def convert(root):
    root = os.path.abspath(root)
    rootdef = _load_yaml(os.path.join(root, ".resources", "definition.yaml"))

    children = []
    for entry in sorted(os.listdir(root)):
        if entry.startswith(".") or entry == ".resources":
            continue
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            child = _build_folder(full)
            order = child.get("order")
            children.append((order if order is not None else BIG, 1, child["item"]))
        elif entry.endswith(".request.yaml"):
            item, order = _parse_request(full)
            children.append((order if order is not None else BIG, 0, item))

    children.sort(key=lambda x: (x[0], x[1], x[2]["name"]))
    items = [c[2] for c in children]

    coll = {
        "info": {
            "name": rootdef.get("name") or os.path.basename(root),
            "_postman_id": "51111111-1111-4111-8111-111111111111",
            "description": rootdef.get("description") or "",
            "schema": SCHEMA,
        },
        "item": items,
    }
    events = _scripts_to_events(rootdef.get("scripts", []))
    if events:
        coll["event"] = events
    vars_arr = _variables_to_arr(rootdef.get("variables"))
    if vars_arr:
        coll["variable"] = vars_arr
    return coll


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", help="集合目录（本地文件工作区）")
    ap.add_argument("-o", "--output", help="输出 JSON 路径")
    args = ap.parse_args()

    root = os.path.abspath(args.collection)
    if not os.path.isdir(root):
        print(f"集合目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    coll = convert(root)
    output = args.output or (root.rstrip(os.sep) + ".collection.json")
    with open(output, "w", encoding="utf-8") as fh:
        json.dump(coll, fh, ensure_ascii=False, indent=2)
    print(f"OK -> {output}")
    print(f"顶层目录/请求数: {len(coll['item'])}")
    n = [0]
    _count(coll["item"], n)
    print(f"请求总数: {n[0]}")


def _count(items, n):
    for it in items or []:
        if "request" in it:
            n[0] += 1
        elif "item" in it:
            _count(it["item"], n)


if __name__ == "__main__":
    main()
