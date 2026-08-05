"""按 prepare_reconcile_repairs.js 生成的精确清单修改 Excel。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api_case_pipeline" / "config" / "storage_scope.json"
CHANGE_FILE = ROOT / "temp_scripts" / "apifox_reconcile_payloads_20260805" / "excel_changes.json"


def normalize_newlines(value: str) -> str:
    normalized = value.replace("_x000D_", "\r").replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n+", "\n", normalized)


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    plan = json.loads(CHANGE_FILE.read_text(encoding="utf-8"))
    excel_file = ROOT / config["excel"]
    workbook = load_workbook(excel_file)

    applied = []
    for change in plan["changes"]:
        sheet = workbook[change["sheet"]]
        cell = sheet[change["cell"]]
        current = "" if cell.value is None else str(cell.value)
        current_normalized = normalize_newlines(current)
        before_normalized = normalize_newlines(change["before"])
        after_normalized = normalize_newlines(change["after"])
        if current_normalized == after_normalized:
            continue
        if current_normalized != before_normalized:
            raise RuntimeError(
                f"单元格已发生计划外变化: {change['sheet']}!{change['cell']}\n"
                f"计划前值: {change['before']!r}\n当前值: {current!r}"
            )
        cell.value = after_normalized
        applied.append(f"{change['sheet']}!{change['cell']}")

    # 零修改时不重写工作簿，避免 openpyxl 无意义地重排/膨胀 ZIP 内容。
    if applied:
        workbook.save(excel_file)
    print(json.dumps({"excel": str(excel_file), "applied": len(applied), "cells": applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
