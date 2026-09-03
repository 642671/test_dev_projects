# Mini Codex Router — 替代 CCSwitchMulti 的本地双路路由

Codex 桌面端一次启动只能挂一个 Provider。要同时用官方模型和第三方模型，
就必须有一个常驻 `127.0.0.1:15721` 的分发器。本路由只做分发，**不做任何别的**：
不碰 `config.toml`、不写注册表、无托盘、不开机自启。

## 路由规则（与 CCSwitchMulti 原有配置一致）

| 模型（选择器里的名字） | 上游 | 认证 |
|---|---|---|
| `gpt-5.4` … `gpt-5.6-*`（gpt/o1/o3/o4 前缀） | `chatgpt.com/backend-api/codex/responses`（经本机代理 `127.0.0.1:7897`） | Codex 自带登录凭据，原样透传 |
| `deepseek-v4-flash` / `deepseek-v4-flash-vision-exp` / `deepseek-v4-pro` | NewAPI `10.18.2.100/v1`（模型名不变） | `TWM_NEWAPI_API_KEY` |
| `newapi-deepseek-v4-flash` / `newapi-deepseek-v4-flash-vision-exp` | NewAPI（映射为 `deepseek-v4-flash` / `deepseek-v4-flash-vision-exp`） | `TWM_NEWAPI_API_KEY` |
| `deepseek-v4-flash-noontec-newapi` | NewAPI（映射为 `deepseek-v4-flash`） | `TWM_NEWAPI_API_KEY` |

> 与 CCSwitchMulti 的两点差异：
> 1. 老规则里裸名 `deepseek-v4-flash` 走的是 `api.deepseek.com`（旧 Key）；本路由统一改走 NewAPI。
> 2. `deepseek-v4-pro` 在 NewAPI 上并不存在（选择器里它是目录遗留），选中会报错属正常现象。

## 使用

```powershell
# 启动（每台机器启动一次，用完 Ctrl+C）
& 'D:\test_dev_projects\docs\codex-model-integration\scripts\minirouter\start-minirouter.ps1'

# 冒烟测试（另开一个窗口）
& 'D:\test_dev_projects\docs\codex-model-integration\scripts\minirouter\test-minirouter.ps1'
```

顺序：**先启动迷你路由，再启动 Codex Desktop**。CCSwitchMulti 不要同时运行
（它会占住 15721 端口，路由会启动失败并给出提示）。若之前给 cc-switch 开了开机自启，
建议之后关掉（或者干脆在任务管理器/设置里停用），只保留迷你路由。

## 网络前提

- **官方模型**：必须开着本机代理（`127.0.0.1:7897`，Clash 等）——你的网络直连 chatgpt.com 超时。
  代理没开时启动脚本会显示警告，第三方模型不受影响。
- **第三方模型**：直接访问内网 `10.18.2.100`，无需代理。

## 回退

完全不需要任何改动：关掉迷你路由 → 打开 CCSwitchMulti → 一切如旧（它的 profile 都还在）。
目前 `config.toml` 保持路由版（`model_provider = "codex_model_router_v2"` → `127.0.0.1:15721`），
两个软件共用同一份配置，连配置都不用动。

## 文件

- `minirouter.js` — 路由本体（Node 18+，零依赖，~230 行）
- `start-minirouter.ps1` — 启动器（端口检查 / 补环境变量 / 代理状态提示）
- `test-minirouter.ps1` — 冒烟测试（`-DeepTest` 会真实请求一次 NewAPI，消耗极少量令牌）
