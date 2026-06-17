#!/usr/bin/env python3
"""
向 Qoder 数据库写入自定义模型配置 + 加密存储 API Key
使用 Electron safeStorage 加密格式 (v10 + AES-GCM)
"""

import base64
import json
import os
import sqlite3
import subprocess
import sys
import uuid

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("[✗] 需要 cryptography 库: pip3 install cryptography")
    sys.exit(1)

DB_PATH = os.path.expanduser(
    "~/Library/Application Support/Qoder/User/globalStorage/state.vscdb"
)

# 火山引擎配置
VOLCANO_API_KEY = "ark-b505c5f4-6dbd-4dc3-abc4-79f4a7eabe79-008a8"
VOLCANO_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
PROVIDER = "kimi"
PROVIDER_DISPLAY_NAME = "Kimi"

# 要添加的模型
MODELS = [
    {"model": "glm-5.1", "displayName": "GLM-5.1 (火山引擎)",
     "is_vl": False, "is_reasoning": True, "max_input_tokens": 204800},
    {"model": "doubao-seed-2.0-code", "displayName": "Doubao-Seed-2.0-Code (火山引擎)",
     "is_vl": True, "is_reasoning": True, "max_input_tokens": 229376},
    {"model": "minimax-latest", "displayName": "MiniMax-Latest (火山引擎)",
     "is_vl": False, "is_reasoning": True, "max_input_tokens": 131072},
]


def get_electron_key():
    """从 macOS Keychain 获取 Electron safeStorage 加密密钥"""
    result = subprocess.run(
        ["security", "find-generic-password", "-w",
         "-s", "Qoder Safe Storage", "-a", "Qoder Key"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[✗] 无法获取 Keychain 密钥: {result.stderr}")
        sys.exit(1)

    key_b64 = result.stdout.strip()
    print(f"[*] 获取到 Keychain 密钥 ({len(key_b64)} 字符)")
    return base64.b64decode(key_b64)


def encrypt_secret(key, plaintext):
    """使用 Electron safeStorage 格式加密 (v10 + AES-GCM)"""
    # 生成 12 字节 IV
    iv = os.urandom(12)

    # AES-GCM 加密
    aesgcm = AESGCM(key)
    # AESGCM.encrypt 返回 ciphertext + tag (tag 附加在末尾)
    ciphertext_and_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

    # 格式: v10 + IV (12 bytes) + ciphertext + tag (16 bytes)
    encrypted = b"v10" + iv + ciphertext_and_tag

    # 转换为 {"type":"Buffer","data":[...]} 格式
    buffer_json = json.dumps({
        "type": "Buffer",
        "data": list(encrypted)
    })
    return buffer_json


def main():
    print("=" * 60)
    print("  Qoder 自定义模型 + API Key 写入工具")
    print("=" * 60)
    print()

    # 获取加密密钥
    key = get_electron_key()
    print(f"[*] 密钥长度: {len(key)} 字节")

    # 加密 API Key
    encrypted_key = encrypt_secret(key, VOLCANO_API_KEY)
    print(f"[*] API Key 已加密 ({len(encrypted_key)} 字节)")

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 读取当前自定义模型
    cursor.execute(
        "SELECT value FROM ItemTable WHERE key = 'aicoding.customModels'"
    )
    row = cursor.fetchone()
    current_models = json.loads(row[0]) if row and row[0] else []
    print(f"[*] 当前自定义模型: {len(current_models)} 个")

    # 构造新模型条目
    import time
    now = int(time.time() * 1000)
    new_models = []
    model_ids = []

    for m in MODELS:
        model_id = str(uuid.uuid4())
        model_ids.append(model_id)
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
        print(f"  + {m['model']} (ID: {model_id[:8]}...)")

    # 写入模型配置
    json_str = json.dumps(new_models, ensure_ascii=False)
    cursor.execute(
        "UPDATE ItemTable SET value = ? WHERE key = 'aicoding.customModels'",
        (json_str,)
    )
    print(f"\n[*] 模型配置已写入")

    # 写入加密的 API Key (每个模型一份)
    for model_id, m in zip(model_ids, MODELS):
        secret_key = f"secret://aicoding.customModel.apiKey.{model_id}"

        # 检查是否已存在
        cursor.execute(
            "SELECT key FROM ItemTable WHERE key = ?", (secret_key,)
        )
        if cursor.fetchone():
            cursor.execute(
                "UPDATE ItemTable SET value = ? WHERE key = ?",
                (encrypted_key, secret_key)
            )
        else:
            cursor.execute(
                "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                (secret_key, encrypted_key)
            )
        print(f"  + API Key 已加密存储: {secret_key[:60]}...")

    conn.commit()

    # 验证
    cursor.execute(
        "SELECT value FROM ItemTable WHERE key = 'aicoding.customModels'"
    )
    row = cursor.fetchone()
    written = json.loads(row[0]) if row and row[0] else []

    cursor.execute(
        "SELECT COUNT(*) FROM ItemTable WHERE key LIKE 'secret://aicoding.customModel.apiKey.%'"
    )
    key_count = cursor.fetchone()[0]

    print(f"\n[✓] 验证完成:")
    print(f"    模型数量: {len(written)}")
    print(f"    API Key 条目: {key_count}")
    print(f"    所有模型 hasApiKey: {all(m.get('hasApiKey') for m in written)}")

    conn.close()

    print()
    print("=" * 60)
    print("  操作完成！请按以下步骤操作:")
    print("  1. 完全退出 Qoder (Cmd+Q)")
    print("  2. 重新打开 Qoder")
    print("  3. 设置 → 模型 → 查看自定义模型是否可用")
    print("=" * 60)


if __name__ == "__main__":
    main()
