#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml

PATH = r"D:\test_dev_projects\Postman\postman\collections\TEST-TNAS\02 登录\02 用户登录.request.yaml"

with open(PATH, "r", encoding="utf-8") as fh:
    d = yaml.safe_load(fh)

for sc in d["scripts"]:
    if sc.get("type") == "afterResponse":
        code = sc["code"]
        # 每行去掉 LOGIN-headers / LOGIN-body 调试日志
        lines = [ln for ln in code.split("\n")
                 if "LOGIN-headers" not in ln and "LOGIN-body" not in ln]
        sc["code"] = "\n".join(lines)
        print("cleaned debug lines")

with open(PATH, "w", encoding="utf-8") as fh:
    yaml.safe_dump(d, fh, allow_unicode=True, sort_keys=False)
