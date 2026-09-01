# Zhipu GLM 接入实录（2026-08-27）

> 本文记录把 CCSwitchMulti 中新增的 `Zhipu GLM` Provider 同步到 Codex 模型选择器的完整过程，适合照着做或下次新增其它第三方模型时复用。

## 1. 先理解三层结构

Codex 使用第三方模型时不是直连厂商，而是走三层：

```text
Codex Desktop 模型选择器
  -> C:\Users\twm\.codex\cc-switch-model-catalog.json（选择器启动时加载）
  -> Codex 请求 http://127.0.0.1:15721/v1（CCSwitchMulti 本地代理）
  -> codex-multirouter 按 model 匹配 codexRouting.routes
  -> 命中某个 Provider（例如 Zhipu GLM），转发到它的 Base URL
```

因此“同步一个模型”至少要改两层：

1. **Codex 侧目录**：让选择器认识这个模型。文件是 `C:\Users\twm\.codex\cc-switch-model-catalog.json` 和 `C:\Users\twm\.codex\models_cache.json`。
2. **路由侧**：让 CCSM 知道这个 model 该转发给哪个 Provider。文件是 `C:\Users\twm\.cc-switch\cc-switch.db` 中 `codex-multirouter` 的 `settings_config`。

`config.toml` 里已经有 `model_catalog_json = "cc-switch-model-catalog.json"`，所以只要目录文件里有条目，重启后 Codex 就会认；旧的 `[model_providers.xxx] models = [...]` 是遗留写法，不依赖它。

## 2. 这次遇到的问题

CCSM 里已经新增了 `Zhipu GLM` Provider（Provider id：`28edab80-e107-44da-9d54-e62278cc5ed2`），但：

- `codex-multirouter` 里没有指向它的路由；
- Codex 侧目录/缓存里没有 `glm-5.2` / `glm-5.3`；
- Zhipu 官方 Coding API 只有 `/chat/completions`，没有 `/responses`（实测 `/responses` 返回 404）。

结论：必须新增一条 `apiFormat = "openai_chat"` 的路由，让 CCSM 把 Codex 的 Responses 请求转换成 Chat Completions 再发给 Zhipu。

## 3. 前置只读检查

### 3.1 查 Provider 是否存在

```powershell
$sqlite = "D:\self_install\adb\platform-tools\sqlite3.exe"
& $sqlite "C:\Users\twm\.cc-switch\cc-switch.db" "SELECT id, app_type, name FROM providers WHERE name LIKE '%Zhipu%' OR name LIKE '%GLM%';"
```

应看到 `28edab80-e107-44da-9d54-e62278cc5ed2`、`codex`、`Zhipu GLM`。

### 3.2 查路由是否已存在

```powershell
& $sqlite "C:\Users\twm\.cc-switch\cc-switch.db" "SELECT settings_config FROM providers WHERE id='codex-multirouter';"
```

看 `codexRouting.routes` 里有没有 `targetProviderId = "28edab80-e107-44da-9d54-e62278cc5ed2"`。本次检查时没有，路由数只有 5。

### 3.3 直接测 Zhipu 上游（只读）

用 CCSM 里 Zhipu Provider 的 API Key（不要保存/打印 Key）：

```text
GET  https://open.bigmodel.cn/api/coding/paas/v4/models
POST https://open.bigmodel.cn/api/coding/paas/v4/responses      -> 404
POST https://open.bigmodel.cn/api/coding/paas/v4/chat/completions -> 200
```

`/models` 返回了 `glm-4.5`、`glm-4.6`、`glm-5`、`glm-5.1`、`glm-5.2`、`glm-5.3`、`glm-5.3-flash` 等；`/chat/completions` 用 `glm-5.3` 正常回复。所以路由格式必须选 `openai_chat`。

## 4. 备份

改任何配置前先备份：

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$dir = "C:\Users\twm\.cc-switch\backups\add-zhipu-glm-$ts"
New-Item -ItemType Directory -Path $dir -Force | Out-Null
py -3 -c "import sqlite3; s=r'C:\Users\twm\.cc-switch\cc-switch.db'; d=r'$($dir -replace '\\','/')/cc-switch.db'; a=sqlite3.connect(s); b=sqlite3.connect(d); a.backup(b); b.close(); a.close()"
Copy-Item "C:\Users\twm\.codex\cc-switch-model-catalog.json" "C:\Users\twm\.codex\cc-switch-model-catalog.json.bak-$ts"
Copy-Item "C:\Users\twm\.codex\models_cache.json" "C:\Users\twm\.codex\models_cache.json.bak-$ts"
```

本次备份目录：`C:\Users\twm\.cc-switch\backups\add-zhipu-glm-20260827-154137\`。

## 5. 修改 cc-switch.db

只更新 `codex-multirouter` 的 `settings_config` JSON，保留其它 Provider 和已有路由。

### 5.1 新增路由

在 `codexRouting.routes` 数组里追加：

```json
{
  "id": "router-28edab80-e107-44da-9d54-e62278cc5ed2",
  "label": "Zhipu GLM",
  "enabled": true,
  "targetProviderId": "28edab80-e107-44da-9d54-e62278cc5ed2",
  "match": {
    "models": ["glm-5.2", "glm-5.3"],
    "prefixes": []
  },
  "upstream": {
    "apiFormat": "openai_chat",
    "auth": { "source": "provider_config" }
  },
  "capabilities": {
    "inputModalities": ["text"],
    "textOnly": true
  }
}
```

关键点：

- `match.models` 必须填 Codex 目录里的 ID（`glm-5.2` / `glm-5.3`），不是菜单显示名。
- `apiFormat = "openai_chat"` 会让 CCSM 把 `/responses` 转成 `/chat/completions`。若错填 `openai_responses`，Zhipu 会返回 404。
- `targetProviderId` 指向 CCSM 里 Zhipu GLM Provider 的 id，这样认证和 Base URL 都从该 Provider 读取。

### 5.2 新增模型目录

在 `modelCatalog.models` 里追加：

```json
{"model": "glm-5.2", "upstreamModel": "glm-5.2", "displayName": "GLM-5.2 (Zhipu)", "contextWindow": 200000, "inputModalities": ["text"], "input_modalities": ["text"], "supportsImage": false, "supports_image": false, "textOnly": true}
{"model": "glm-5.3", "upstreamModel": "glm-5.3", "displayName": "GLM-5.3 (Zhipu)", "contextWindow": 200000, "inputModalities": ["text"], "input_modalities": ["text"], "supportsImage": false, "supports_image": false, "textOnly": true}
```

同时把 `glm-5.2`、`glm-5.3` 加入 `modelCatalog.spawnAgentModels`，这样子代理也能选到。

### 5.3 写回

```python
con.execute(
    "UPDATE providers SET settings_config=? WHERE id=?",
    (json.dumps(cfg, ensure_ascii=False), "codex-multirouter"),
)
con.commit()
```

## 6. 修改 Codex 侧目录

两个文件都要加：

- `C:\Users\twm\.codex\cc-switch-model-catalog.json`
- `C:\Users\twm\.codex\models_cache.json`

做法：从已有的 `zai-org/GLM-5.2` 条目复制一份完整对象，只改以下字段，避免手写缺字段导致 Codex 解析失败：

```text
model / slug / id            = glm-5.2 或 glm-5.3
displayName / display_name   = GLM-5.2 (Zhipu) 或 GLM-5.3 (Zhipu)
description                 = 同上
contextWindow / context_window = 200000
maxContextWindow / max_context_window = 200000
inputModalities / input_modalities = ["text"]
supportsImageDetailOriginal / supports_image_detail_original = false
webSearchToolType / web_search_tool_type = "text"
```

不需要改 `auth.json`，也不要把 API Key 写进任何 Codex 文件。

## 7. 验证（不需要重启 Codex）

### 7.1 本地代理是否认识新模型

```powershell
$auth = Get-Content "$env:USERPROFILE\.codex\auth.json" -Raw | ConvertFrom-Json
curl.exe -s "http://127.0.0.1:15721/v1/models" `
  -H "Authorization: Bearer $($auth.tokens.access_token)" `
  -H "x-cc-switch-proxy-mode: router" `
  -H "ChatGPT-Account-Id: $($auth.tokens.account_id)"
```

返回里应能看到 `glm-5.2`、`glm-5.3`。裸请求不带这三个头会返回 403。

### 7.2 真实请求

```powershell
curl.exe -s -X POST "http://127.0.0.1:15721/v1/responses" `
  -H "Authorization: Bearer $($auth.tokens.access_token)" `
  -H "x-cc-switch-proxy-mode: router" `
  -H "ChatGPT-Account-Id: $($auth.tokens.account_id)" `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"glm-5.3\",\"input\":\"say hi\",\"stream\":false}'
```

`glm-5.3`、`glm-5.2` 非流式和流式都实测返回 200。

### 7.3 看路由日志

```text
C:\Users\twm\.cc-switch\logs\codex-router.log
```

关键行应类似：

```text
route_id=router-28edab80-e107-44da-9d54-e62278cc5ed2
upstream_url=https://open.bigmodel.cn/api/coding/paas/v4/chat/completions
responses_to_chat=true
status=200
```

看到 `responses_to_chat=true` + `chat/completions` + `status=200` 才算真正路由成功。

## 8. 最后一步：完全退出 Codex 再启动

`model_catalog_json` 只在 Codex 启动时加载一次，所以：

1. 关闭所有 Codex 窗口；
2. 右键系统托盘里的 Codex 图标，选择退出，确保没有 ChatGPT/codex 进程残留；
3. 重新打开 Codex；
4. 在模型选择器里选择 `GLM-5.3 (Zhipu)` 或 `GLM-5.2 (Zhipu)`。

本次用户重启后确认已可用；ChatGPT 新进程启动时间晚于配置修改时间。

## 9. 下次新增第三方模型的通用清单

1. 在 CCSM 添加/确认 Provider（Base URL、Key、模型名）。
2. 直接测上游：确认它支持 `/responses` 还是只支持 `/chat/completions`，从而决定 `apiFormat`。
3. 备份 `cc-switch.db` 和两个 Codex 目录文件。
4. 在 `codex-multirouter` 加路由 + `modelCatalog` + `spawnAgentModels`。
5. 在 `cc-switch-model-catalog.json` 和 `models_cache.json` 加条目（从已有第三方条目复制改字段）。
6. 用 `/v1/models` 和真实 `/v1/responses`（含流式）验证，看 `codex-router.log`。
7. 完全退出 Codex（含托盘）再启动，确认选择器可见。

## 10. 常见坑

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 选择器里没有新模型 | 只改了路由，没改 Codex 侧目录/缓存，或没重启 Codex | 两个 JSON 都加条目；完全退出（含托盘）后重启 |
| 请求 404 | 上游不支持 `/responses`，但路由填了 `openai_responses` | 改成 `openai_chat`，由 CCSM 转换 |
| 请求落回官方 GPT | 路由 `match.models` 没填目录 ID | 填 Codex 目录 ID，不是显示名 |
| `/v1/models` 403 | 裸请求缺少认证头 | 带 Codex Authorization、`x-cc-switch-proxy-mode: router`、`ChatGPT-Account-Id` |
| 选择器有模型但报错 | 上游模型名与目录 ID 不一致 | 用 `upstreamModel` 或路由 `modelMap` 映射真实上游名 |
