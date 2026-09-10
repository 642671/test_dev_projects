# enc 加解密脚本索引

整理日期：2026-09-03

## 已整理的可复用脚本

| 文件 | 用途 | 算法/格式 |
|---|---|---|
| `tos_frontend_enc.py` | TOS7 前端请求体 `{"enc":"..."}` 的加密、解密 | AES-256-GCM；12 字节 nonce + 密文 + 16 字节 tag，输出十六进制 |
| `encryption_utils.py` | 平台通用字符串加密、解密 | AES-GCM；Base64（nonce + tag + ciphertext） |
| `crypto_utils.py` | 开发者中心下架接口的混合加密 | AES-256-GCM + RSA-OAEP-SHA256，字段均为 Base64 |

这些副本不包含账号密码、Cookie、运行时 Token 或私钥。使用前请通过环境变量、密钥文件或命令行安全注入密钥，不要把真实密钥写入脚本或报告。

## 仓库中的原始实现路径

- TOS7 `enc` 独立脚本：`scripts/tos_frontend_enc.py`
- 平台通用 AES：`common/encryption_utils.py`
- TOS7 登录服务中的 RSA/AES 实现：`backend/app/services/tos7_auth.py`
  - RSA 密码加密：`encrypt_tos7_request_password`、`_rsa_encrypt_from_public_key_text`
  - 请求体 AES-GCM：`_aes_gcm_encrypt`
- TOS7 项目 RSA 公钥加密核心：`workspace/tos7_project/internal_core/RSA_encryption_utils.py`
- TOS7 项目 RSA 调用存根：`workspace/tos7_project/utils/RSA_encryption_utils.py`
- 浏览器端完整工具（同时含 `enc`、curpass、密码 RSA 解密）：`web/src/utils/tosEncDecrypt.js`

## 使用示例

### TOS7 `enc`（从设备获取 Date 和 X-Rsa-Token）

```bash
python scripts/tos_frontend_enc.py encrypt \
  --base-url https://<tos-host>:<port> --insecure \
  --json '{"path":"/data","name":"test"}'
```

解密历史密文时，必须提供生成该密文时对应的公钥文本和 HTTP `Date`：

```bash
python scripts/tos_frontend_enc.py decrypt \
  --public-key-file /path/to/rsa_public.pem \
  --server-date 'Wed, 02 Sep 2026 08:30:00 GMT' \
  --enc '<hex-enc>'
```

### 平台通用 AES

```python
from encryption_utils import encrypt_aes, decrypt_aes

ciphertext = encrypt_aes("示例明文", "0123456789abcdef")
plaintext = decrypt_aes(ciphertext, "0123456789abcdef")
```

依赖：`pycryptodome`；`tos_frontend_enc.py` 另外需要 `requests`。

## 注意事项

- `workspace/tos7_project/internal_core/encryption_utils.py` 中存在硬编码且长度不足的示例 key（会用 `0` 补齐），不作为当前可用实现，未复制到本目录。
- `web/src/utils/tosEncDecrypt.js` 中存在 `DEFAULT_TOS_RSA_PRIVATE_KEY` 常量。该文件应视为敏感源码，不要再复制到共享文档、工单或外部仓库；如该私钥用于真实环境，应尽快轮换。
- AES-GCM 解密会校验认证标签；密文、nonce、tag 或密钥任一被修改都会失败。
