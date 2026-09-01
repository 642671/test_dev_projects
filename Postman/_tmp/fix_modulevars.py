#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把集合脚本里 Apifox 遗留的 pm.moduleVariables 全部替换为 Postman 的
pm.collectionVariables（prerequest/test 均可用，且每次 CLI 运行自动隔离 IP）。"""
import glob
import os
import yaml

ROOT = r"D:\test_dev_projects\Postman\postman\collections\TEST-TNAS"


def main():
    changed = 0
    targets = glob.glob(os.path.join(ROOT, "**", "*"), recursive=True)
    # 只改 yaml（.request.yaml 与 .resources/definition.yaml）
    files = [p for p in targets if p.endswith(".yaml")]
    for path in files:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        if "pm.moduleVariables" not in raw:
            continue
        new = raw.replace("pm.moduleVariables", "pm.collectionVariables")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        changed += 1
    print("changed files:", changed)


if __name__ == "__main__":
    main()
