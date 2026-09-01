#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 *.request.yaml 前置脚本里的 Apifox 加密调用改成 Postman 可用的
pm.rsaEncryptPassword（集合级已注入）。仅作一次性迁移。"""
import glob
import re
import os
import yaml

ROOT = r"D:\test_dev_projects\Postman\postman\collections\TEST-TNAS"

ATOB = re.compile(r"require\s*\(\s*['\"]atob['\"]\s*\)\s*\(\s*(\w+)\s*\)")
EXEC = re.compile(r"await\s+pm\.executeAsync\s*\(\s*['\"]encoderLoginPassword\.go['\"]\s*,\s*\[\s*([^,\]]+)\s*,\s*([^\]]+)\s*\]\s*\)")


def fix(js):
    js = ATOB.sub(r"\1", js)         # require('atob')(base64Key) -> base64Key
    js = EXEC.sub(lambda m: "pm.rsaEncryptPassword(%s, %s)" % (m.group(1).strip(), m.group(2).strip()), js)
    # 去掉孤立 `await `（pm.rsaEncryptPassword 是同步函数）
    js = js.replace("await pm.rsaEncryptPassword", "pm.rsaEncryptPassword")
    return js


def main():
    changed = []
    for path in glob.glob(os.path.join(ROOT, "**", "*.request.yaml"), recursive=True):
        with open(path, "r", encoding="utf-8") as fh:
            d = yaml.safe_load(fh)
        if not isinstance(d, dict):
            continue
        hit = False
        for sc in d.get("scripts") or []:
            if not isinstance(sc, dict):
                continue
            code = sc.get("code")
            if isinstance(code, str) and ("executeAsync" in code or "encoderLoginPassword" in code):
                sc["code"] = fix(code)
                hit = True
        if hit:
            with open(path, "w", encoding="utf-8") as fh:
                yaml.safe_dump(d, fh, allow_unicode=True, sort_keys=False)
            changed.append(path)
    print("changed:", len(changed))
    for p in changed:
        print(" -", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
