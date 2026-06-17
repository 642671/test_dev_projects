#!/usr/bin/env python3
"""
直接向 Qoder 数据库写入自定义模型配置
绕过 GUI 验证，直接设置 baseUrl 为火山引擎 API 端点
"""

import json
import sqlite3
import time
import uuid

DB_PATH = "/Users/miaoqi/Library/Application Support/Qoder/User/globalStorage/state.vscdb"

# 火山引擎 Coding Plan 配置
VOLCANO_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
PROVIDER = "kimi"
PROVIDER_DISPLAY_NAME = "Kimi"

# 要添加的三个模型
MODELS = [
    {
        "model": "glm-5.1",
        "displayName": "GLM-5.1 (火山引擎)",
        "is_vl": False,
        "is_reasoning": True,
        "max_input_tokens": 204800,
    },
    {
        "model": "doubao-seed-2.0-code",
        "displayName": "Doubao-Seed-2.0-Code (火山引擎)",
        "is_vl": True,
        "is_reasoning": True,
        "max_input_tokens": 229376,
    },
    {
        "model": "minimax-latest",
        "displayName": "MiniMax-Latest (火山引擎)",
        "is_vl": False,
        "is_reasoning": True,
        "max_input_tokens": 131072,
    },
]


def main():
    print("=" * 60)
    print("  Qoder 自定义模型数据库写入工具")
    print("=" * 60)
    print()

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 读取当前自定义模型
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'aicoding.customModels'")
    row = cursor.fetchone()
    current_models = json.loads(row[0]) if row and row[0] else []

    print(f"[*] 当前自定义模型数量: {len(current_models)}")

    # 如果已有模型，先清空
    if current_models:
        print(f"[*] 清空现有模型...")
        current_models = []

    # 构造新模型条目
    now = int(time.time() * 1000)  # JavaScript Date.now() 格式（毫秒）
    new_models = []

    for m in MODELS:
        model_id = str(uuid.uuid4())
        entry = {
            "id": model_id,
            "provider": PROVIDER,
            "providerDisplayName": PROVIDER_DISPLAY_NAME,
            "model": m["model"],
            "displayName": m["displayName"],
            "baseUrl": VOLCANO_BASE_URL,
            "visible": True,
            "hasApiKey": True,
            "is_vl": m["is_vl"],
            "is_reasoning": m["is_reasoning"],
            "max_input_tokens": m["max_input_tokens"],
            "createTime": now,
        }
        new_models.append(entry)
        print(f"  + {m['model']} → {VOLCANO_BASE_URL}")
        print(f"    ID: {model_id}")

    # 写入数据库
    updated_models = current_models + new_models
    json_str = json.dumps(updated_models, ensure_ascii=False)

    cursor.execute(
        "UPDATE ItemTable SET value = ? WHERE key = 'aicoding.customModels'",
        (json_str,)
    )
    conn.commit()

    # 验证写入
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'aicoding.customModels'")
    row = cursor.fetchone()
    written = json.loads(row[0]) if row and row[0] else []

    print()
    print(f"[✓] 已写入 {len(written)} 个自定义模型到数据库")
    print()
    print("=" * 60)
    print("  重要提示:")
    print("  1. 请先完全退出 Qoder (Cmd+Q)")
    print("  2. 然后重新打开 Qoder")
    print("  3. 在设置 → 模型中查看是否出现新模型")
    print("  4. 如果模型显示需要 API Key，点击编辑并输入:")
    print("     ark-b505c5f4-6dbd-4dc3-abc4-79f4a7eabe79-008a8")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
