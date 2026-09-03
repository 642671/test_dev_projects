# Codex 桌面版双路模型方案说明（迷你路由）

- 适用环境: Windows 11 / Codex Desktop build 26.825 / Node 24.14
- 文档日期: 2026-09-02
- 脚本目录: `D:\test_dev_projects\docs\codex-model-integration\scripts\minirouter\`

---

## 一、背景与问题

Codex Desktop 是**单供应商架构**：全局只有一个 `model_provider` + 一个 `model_catalog_json`，
目录里的模型不区分上游。而实际需求有两类上游：

| 上游 | 访问方式 | 认证 | 网络要求 |
|---|---|---|---|
| ChatGPT 官方（gpt-5.x / o1/o3/o4） | `chatgpt.com/backend-api/codex/responses` | 透传 Codex 自带登录凭据 | **必须**经本机代理 `127.0.0.1:7897`（Clash Verge），直连会超时 |
| Noontec NewAPI（deepseek-v4 系） | `http://10.18.2.100/v1`，`wire_api=responses` | `Bearer TWM_NEWAPI_API_KEY` | 内网直连，与代理无关 |

最初由 CCSwitchMulti 承担分路由。为摆脱对它的依赖（自启动抢端口、行为不可控），改为**自建迷你路由**：

```
Codex Desktop ──→ 127.0.0.1:15721（迷你路由，Node 零依赖）
                     ├─ gpt/o1/o3/o4*  → 代理 7897 → chatgpt.com（认证原样透传）
                     └─ 其它模型       → NewAPI 10.18.2.100（换 key + 模型名映射）
```

路由无托盘、无状态、**不写任何配置文件/注册表**，只做透明转发。

## 二、过程中解决的核心 Bug（重点）

**症状**：发消息后轮次完成（`task_complete`）但没有回复；或页面直接报
`请求体不是 JSON: Unexpected token '(', "(�/�" ...`。

**根因**：Codex Desktop 把发给本地路由的请求体用 **zstd 压缩**（zstd 帧头 `28 B5 2F FD`，
以 UTF-8 显示就是乱码 `(�/�`）。旧版路由未解压直接 `JSON.parse` → 400 → app 无内容可显示。
旧版路由 400 还不写日志，导致排查完全无痕。

**修复**（`minirouter.js`，2026-09-02）：
- 按 zstd 魔数或 `content-encoding: zstd` 识别 → `zlib.zstdDecompressSync` 解压；
- **官方路**：解压仅用于取模型名，转发时**原始字节 + 原始压缩头原样透传**（chatgpt.com 原生处理链不受影响）；
- **NewAPI 路**：解压 → 改写 `model` → 转**明文 JSON** 发出（并去掉 `content-encoding` 头，防网关误读）；
- 所有 4xx/解析失败现在都写入 `router.log`（每笔请求都有记录）。

**附带发现**：官方路可用性绑定机场（Clash Verge 的代理节点）稳定性——09:15 的事件中
机场日本节点拨号 `context canceled` 持续失败，导致官方模型大面积不可用。节点恢复后即正常。
**官方模型偶发失败首选动作：在 Clash Verge 里切换/重载节点。**

**模型命名**：catalog 中 `id/model/slug` 三处 `deepseek-v4-flash-noontec-newapi`
已统一更名为 `newapi-deepseek-v4-flash`（选择器显示名不变）。

## 三、文件清单

| 文件 | 作用 |
|---|---|
| `scripts\minirouter\minirouter.js` | 迷你路由本体（监听 15721） |
| `scripts\minirouter\start-minirouter.ps1` | 启动器（自动补环境变量/查端口冲突/提示代理状态） |
| `scripts\minirouter\test-minirouter.ps1` | 明文冒烟测试；`-DeepTest` 发真实 NewAPI 请求 |
| `scripts\minirouter\zstd-smoke.js` | **zstd 压缩请求冒烟测试**（模拟 app 请求，最贴近真实） |
| `scripts\minirouter\watch-codex.ps1` | 后台监听（配置压缩/路由掉线/新请求） |
| `scripts\minirouter\router.log` | 运行日志（每笔请求：模型/去向/耗时/状态码） |
| `C:\Users\twm\.codex\config.toml` | 指向 `127.0.0.1:15721`（`codex_model_router_v2` provider） |
| `C:\Users\twm\.codex\cc-switch-model-catalog.json` | 模型目录（11 个模型，含 `newapi-deepseek-v4-flash*`） |
| `C:\Users\twm\.cc-switch\settings.json` | cc-switch 配置（**launchOnStartup 已置 false**） |

**cc-switch 自动启动已禁用**（2026-09-02）：
- 注册表 `HKCU\...\Run` 的 `CCSwitchMulti` 值已删除；
- `.cc-switch\settings.json` 的 `launchOnStartup` 置 `false`（防止应用自己重新注册）；
- 单机版 cc-switch 与计划任务本无自启动项，无需处理。

**备份**：`D:\test_dev_projects\docs\codex-model-integration\backups\cleanup-20260902-094612\`
（config.toml / catalog / auth.json / cc-switch.db / settings.json / 脚本全套；
**auth.json 与 codex_oauth_auth.json 含凭据，切勿对外发送**）。
历史备份保留在 `.cc-switch\backups\` 与 `.codex\`（`config.toml.bak-*` 等），直至确认稳定后再清理。

## 四、使用说明

### 前置条件
1. Node.js ≥ 22.15（本机 24.14，自带 zstd 解压）；
2. 用户环境变量 `TWM_NEWAPI_API_KEY`（启动脚本会从注册表自动补上，不打印不落盘）；
3. **Clash Verge 运行且 127.0.0.1:7897 处于监听** —— 官方模型必须；NewAPI 模型不受影响；
4. NewAPI `10.18.2.100:80` 内网可达（本机局域网）。

### 启动（顺序：代理 → 路由 → 应用）
```powershell
# ① Clash Verge 打开并确认系统代理/7897 在线
Test-NetConnection 127.0.0.1 -Port 7897 -InformationLevel Quiet   # 应为 True

# ② 启动迷你路由（双击或本命令）
& 'D:\test_dev_projects\docs\codex-model-integration\scripts\minirouter\start-minirouter.ps1'

# ③ 打开 Codex Desktop
```

**新版生效标志**：启动日志末尾必须出现
`请求体: zstd/gzip 自动解压（兼容 Codex Desktop 的压缩请求）`。
没这行 = 旧实例（先 Ctrl+C 再重启）。

停止：路由窗口 `Ctrl+C` 即可；**不需要先退出 Codex**，也**不需要关闭 Clash Verge**。

### 日常
- 开机后手动启动路由（未注册自启动，保持手动可控）；建议把 ② 加个桌面快捷方式。
- 每笔请求可在 `router.log` 查看：`POST ... visible=<模型> -> 去向` 与 `<- 状态码 (耗时ms)`。

## 五、常见问题排查

| 现象 | 排查方向 |
|---|---|
| 页面报「请求体不是 JSON」 | router.log 里该笔请求**无** `(解压)` 标记 → 跑的还是旧路由，Ctrl+C 重启 |
| 官方模型无回复 | router.log：无 `<- 模型` 完成行 → 查 7897 在线 + Clash Verge 节点；有且耗时 1–2s → 机场节点问题，切节点 |
| NewAPI 模型无回复 | router.log 状态码：502=内网不通；401/403=网关 key；500=环境变量缺失（用 start 脚本启动） |
| 启动提示「端口 15721 已被占用」 | cc-switch 又开了自启动（检查第四节两个开关）或另一个 node 实例；退出后重试 |
| 需要看应用侧证据 | `C:\Users\twm\.codex\sessions\2026\09\02\*.jsonl`：`turn_context.model` = 实际用模型；末尾 `response_item.content` = 真实回答 |

**三个证据源**：router.log（路由侧）→ Clash Verge `logs\service\`（网络侧）→ `sessions\*.jsonl`（应用侧）。

## 六、回滚（随时退回 cc-switch 方案）

本方案是**叠加式**的：`config.toml`、catalog、注册表、凭据自始至终未被路由进程改动过
（只有 catalog 模型名更名，cc-switch 以同一 catalog 为准，无影响）。
退回：`Ctrl+C` 关闭路由 → 正常打开 CCSwitchMulti 应用（其 `codex-multirouter` profile
与 provider 数据仍完好存于 `cc-switch.db`）→ 在应用里切换即可。
恢复自启动：用备份目录中的 `reg-HKCU-Run-export.reg` 恢复注册表，
并把 settings.json 的 `launchOnStartup` 手动改回 `true`。

## 七、验证记录（2026-09-02）

| 项目 | 结果 |
|---|---|
| zstd 压缩请求 → NewAPI（烟雾） | `HTTP 200`，`model=deepseek-v4-flash` ✓ |
| Codex 实测 `newapi-deepseek-v4-flash-vision-exp` | 260ms，回答「1」 ✓ |
| Codex 实测 `gpt-5.6-sol`（官方+机场） | 19.9s，回答「1」 ✓ |
| 15:00 前旧版本同请求 | `HTTP 400`（zstd 未解压，即报错 `(�/�`） ✗（修复前） |
