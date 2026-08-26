# Codex 第三方模型接入与跨设备同步手册

> 更新日期：2026-08-26（以办公机实测配置为准）
> 用途：记录办公机当前配置，并作为家中电脑 Codex 从零配置的操作手册

## 1. 要解决的问题

- 登录同一个 ChatGPT / Codex 账号后，模型选择器里可以直接使用第三方模型（DeepSeek、GLM、公司网关等），不占用官方 GPT 额度。
- 官方会话与第三方会话在同一个历史列表中，切换模型不丢历史。
- 同一账号在办公机与家中电脑之间同步活跃会话状态。

## 2. 链路与原理

```text
Codex Desktop
  -> CCSwitchMulti 本地代理  http://127.0.0.1:15721/v1
      -> MultiRouter 方案  Codex GPT + DeepSeek
          -> 上游 Provider（按模型路由）
              OpenAI 官方 OAuth / DeepSeek / SiliconFlow / Noontec 网关
```

关键机制：

1. Codex 只连接本地代理，CCSwitchMulti 按模型把请求转发到对应上游；第三方接口不支持 Responses 时，由本地代理完成协议转换（即“需要本地路由映射”）。
2. Provider 保留 `requires_openai_auth = true`，登录态仍挂在官方 ChatGPT 账号上，切换第三方模型不会掉登录。
3. “统一 Codex 会话历史”让官方会话与第三方会话共用同一个历史桶（`custom`），迁移前自动备份到 `~/.cc-switch/backups`，可逆。
4. 同一 ChatGPT 账号下，Codex 的安全中继层会在设备之间同步活跃会话状态与上下文（依据 OpenAI 官方“随时随地使用 Codex”说明）。

## 3. 办公机当前配置（实测）

### 3.1 程序与数据位置

| 项目 | 位置 |
| --- | --- |
| Codex Desktop | `C:\Users\twm\AppData\Local\OpenAI\Codex\` |
| Codex 配置目录 | `C:\Users\twm\.codex\`（`config.toml`、`auth.json`、`models_cache.json`、`cc-switch-model-catalog.json`） |
| Codex 会话历史 | `C:\Users\twm\.codex\sessions\`、`state_5.sqlite`、`session_index.jsonl` |
| CCSwitchMulti | `C:\Users\twm\AppData\Local\CCSwitchMulti\cc-switch.exe` |
| CCSwitchMulti 数据 | `C:\Users\twm\.cc-switch\`（`cc-switch.db`、`settings.json`、`logs\`、`backups\`） |
| Clash Verge | `C:\Program Files\Clash Verge\clash-verge.exe`，规则文件 `profiles\Merge.yaml` |

### 3.2 CCSwitchMulti 中的模型源（Provider）

| Provider 名称 | Base URL | 可用模型 | 协议/映射 |
| --- | --- | --- | --- |
| OpenAI Official | 官方 OAuth | GPT-5.4 / 5.5 / 5.6 系列 | 官方 Responses |
| DeepSeek | `https://api.deepseek.com` | `deepseek-v4-flash`、`deepseek-v4-pro` | Responses |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `zai-org/GLM-5.2` | Chat + 本地路由映射 |
| Noontec 9007 | `http://10.18.10.140:9007/v1`（仅办公网） | `deepseek-v4-flash` | Responses + 本地路由映射 |
| Noontec NewAPI | `http://10.18.2.100/v1`（办公网） | `deepseek-v4-flash` | Chat + 本地路由映射 |

### 3.3 Codex 模型选择器中的条目（节选）

| 显示名 | 上游模型 | 来源 |
| --- | --- | --- |
| `DeepSeek V4 Flash` / `DeepSeek V4 Pro` | `deepseek-v4-flash` / `deepseek-v4-pro` | DeepSeek 官方 |
| `GLM-5.2 (SiliconFlow)` | `zai-org/GLM-5.2` | SiliconFlow |
| `9007deepseek-v4-flash` | `deepseek-v4-flash` | Noontec 9007 |
| `newapi-deepseek-v4-flash` | `deepseek-v4-flash` | Noontec NewAPI |
| `GPT-5.4 / 5.5 / 5.6-*` | 同名 | OpenAI 官方 |

模型条目的关键约定：显示名可以带前缀（如 `newapi-deepseek-v4-flash`），但 `model` / `upstreamModel` 必须是真正的上游模型名（如 `deepseek-v4-flash`），否则远端会拒绝。

### 3.4 Codex 生效配置

`C:\Users\twm\.codex\config.toml` 关键内容：

```toml
model_provider = "codex_model_router_v2"
model = "deepseek-v4-flash"
model_catalog_json = "cc-switch-model-catalog.json"

[model_providers.codex_model_router_v2]
name = "Codex GPT + DeepSeek"
base_url = "http://127.0.0.1:15721/v1"
wire_api = "responses"
supports_websockets = false
requires_openai_auth = true
http_headers = { x-cc-switch-proxy-mode = "router" }
```

### 3.5 CCSwitchMulti 关键设置

| 设置 | 当前值 | 作用 |
| --- | --- | --- |
| `enableLocalProxy` | true | 启用本地代理 |
| `launchOnStartup` / `silentStartup` | true | 开机自启、静默启动 |
| `preserveCodexOfficialAuthOnSwitch` | true | 切换第三方模型时保留官方登录 |
| `unifyCodexSessionHistory` | true | 官方与第三方会话同一历史列表 |
| `unifyCodexMigrateExisting` | true | 已迁移存量官方会话（2026-08-12：21 个会话文件、23 行索引） |
| Codex 本地代理端口 | `127.0.0.1:15721` | Codex 请求入口 |

### 3.6 Clash Verge 分流（办公机）

规则模式，核心规则顺序：

```yaml
rules:
  - IP-CIDR,10.18.10.140/32,DIRECT,no-resolve   # 公司 9007 网关直连
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve        # 公司网段（含 10.18.2.100）直连
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - DOMAIN-SUFFIX,openai.com,代理组
  - DOMAIN-SUFFIX,chatgpt.com,代理组
  - GEOSITE,cn,DIRECT
  - GEOIP,CN,DIRECT
  - MATCH,代理组
```

必须使用规则模式；全局模式会把公司地址也送进代理，导致 `/v1/models` 获取失败。

### 3.7 日志验证（实测）

`C:\Users\twm\.cc-switch\logs\cc-switch.log`：

```text
[Codex] >>> 请求目标: http://10.18.2.100/v1/responses (model=deepseek-v4-flash)
```

`codex-router.log` 中对应请求出现 `route_resolved`、`upstream_url` 和 `status=200`。

## 4. 家中电脑从零配置步骤

目标：家中电脑登录同一 ChatGPT 账号，模型选择器出现第三方模型，历史不丢、活跃会话可跨设备同步。

### 4.1 准备

1. Windows 电脑，安装 Codex Desktop。
2. 能访问 OpenAI 的网络（GPT 模型需要代理；第三方模型如 DeepSeek / SiliconFlow 国内直连即可）。
3. 同一 ChatGPT / Codex 账号。
4. CCSwitchMulti 安装包（GitHub `BigStrongSun/ccswitchmulti` releases）。

### 4.2 登录与授权

1. 先启动 Codex Desktop，用你的 ChatGPT / Codex 账号完成官方登录（每台机器各自登录，不要复制 `~/.codex/auth.json`）。
2. 安装并启动 CCSwitchMulti，进入 `设置 -> 认证`，点击“使用 ChatGPT 登录”完成 OAuth 授权。

### 4.3 添加第三方模型源

在 CCSwitchMulti 的 Codex 面板右上角添加 Provider，建议先加家里一定能访问的公共源：

| Provider | Base URL | 模型 |
| --- | --- | --- |
| DeepSeek | `https://api.deepseek.com` | `deepseek-v4-flash`、`deepseek-v4-pro` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `zai-org/GLM-5.2` |
| 公司网关（可选） | 办公网 `http://10.18.10.140:9007/v1` 或 `http://10.18.2.100/v1`，家里需 VPN 可达才配置 | `deepseek-v4-flash` |

每个 Provider 的填写要点：

1. 填写 Base URL 和 API Key。
2. 打开“需要本地路由映射”。
3. 在模型映射里点“获取模型列表”，确认模型名，填写上下文窗口。
4. 保存。

API Key 只存在 CCSwitchMulti 数据库里，不要写进文档或聊天记录。

### 4.4 创建并启用多模型路由

1. 打开 `Codex 多模型路由` 工作台，点击“创建多路路由”，命名如 `Codex GPT + DeepSeek`。
2. 进入“路由规则”，加入 OpenAI 官方、DeepSeek、SiliconFlow（以及公司网关），确认启用。
3. 需要不同显示名时配置可见别名，例如：canonical `deepseek-v4-flash` -> 显示 `newapi-deepseek-v4-flash`。
4. 认证策略选择 Provider 配置认证或托管 Codex OAuth（只保存引用，不保存 Token）。
5. 保存方案并选中它。

### 4.5 启动路由与历史统一

1. `设置 -> 路由`：打开“路由总开关”和“Codex 路由”，确认本地监听 `127.0.0.1:15721`。
2. `设置 -> 通用 -> Codex 应用增强`：打开“统一 Codex 会话历史”，勾选“同时迁入现有官方会话历史”（迁移前会自动备份）。
3. 确认“切换 Provider 时保留官方认证”已开启。

### 4.6 Clash Verge 分流（家中）

使用规则模式：

```yaml
rules:
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve        # 公司网段（VPN 时直连）
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - DOMAIN-SUFFIX,openai.com,你的代理组
  - DOMAIN-SUFFIX,chatgpt.com,你的代理组
  - DOMAIN-SUFFIX,oaistatic.com,你的代理组
  - GEOSITE,cn,DIRECT
  - GEOIP,CN,DIRECT
  - MATCH,你的代理组
```

家中没有可用代理时，官方 GPT 模型不可用，但 DeepSeek / SiliconFlow 等第三方模型仍可用。

### 4.7 重启并选择模型

1. 完全退出 Codex Desktop（包括托盘进程）后重新打开。
2. 模型选择器里选择第三方模型（如 `DeepSeek V4 Flash`、`newapi-deepseek-v4-flash`）。
3. 发送一条测试消息。

### 4.8 历史记录修复（如列表异常）

`会话管理 -> Codex 历史修复`：点击“加载历史” -> 全选 -> “预览修复” -> 确认写入 -> 重启 Codex。

## 5. 历史记录同步说明

1. 同一 ChatGPT 账号：Codex 安全中继层会在设备之间同步**活跃会话状态和上下文**；文件、凭据、权限保留在 Codex 实际运行的那台机器上。
2. 本机统一历史：开启“统一 Codex 会话历史”后，官方与第三方会话在同一列表；开关关闭时可按备份还原，数据不会丢。
3. 跨供应商续聊限制：旧会话里的加密推理内容只有生成它的后端能解密，用另一个 Provider 续聊可能失败；此时回到原 Provider 续聊，或开新会话。
4. 想在两台机器看到完全相同的本地历史列表，需要手动同步 `~/.codex/sessions`、`state_5.sqlite`、`session_index.jsonl`（先完全退出 Codex 再做，不建议在运行中复制）。
5. 不要在两台机器之间复制 `auth.json`。

## 6. 验证清单

- [ ] Codex 模型选择器出现第三方模型
- [ ] `cc-switch.log` 出现 `请求目标: http://<网关>/v1/responses (model=deepseek-v4-flash)`
- [ ] CCSwitchMulti 状态页显示请求命中正确路由
- [ ] 官方 GPT 模型仍可切换（依赖代理）
- [ ] 官方会话与第三方会话在同一历史列表
- [ ] 历史修复无 pending 或已确认写入
- [ ] 另一台设备能看到活跃会话（同一账号 + 机器在线）

## 7. 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `获取模型列表失败 ... /v1/models` | 网络/规则问题：确认规则模式、公司地址直连、Base URL 与 Key 正确；家里配置 10.18.x 时需 VPN |
| `502 Bad Gateway: CC Switch local proxy failed` | CCSwitchMulti 未运行或端口被占用；重启 CCSwitchMulti，确认 `base_url` 为 `127.0.0.1:15721/v1` |
| 模型选择器没有新模型 | Codex 启动时缓存旧模型目录；完全退出重启，或使用“模型菜单解锁”流程 |
| 把显示名直接发给远端失败 | `model` / `upstreamModel` 必须是上游真名（`deepseek-v4-flash`），显示名仅用于选择器 |
| 切换后历史列表变空 | Provider 桶变化；用“Codex 历史修复”预览并写入，再重启 |
| 家里用不了公司 10.18.x 网关 | 该地址仅办公网可达；家里改用 DeepSeek / SiliconFlow 或公司域名网关（需 VPN） |
| 官方 GPT 报 502 | OpenAI 域名未走代理或代理组不可用；检查 Clash 规则 |

## 8. 安全注意事项

1. API Key、OAuth Token 不写入文档、日志或聊天记录；只存在 CCSwitchMulti / Codex 本地。
2. `~/.codex/auth.json` 不跨机器复制，不分享给任何人。
3. 统一历史迁移会自动备份，可还原；不要手工乱改 `model_provider` 标签，除非先备份。
4. 公司网关地址仅限公司内网使用。
