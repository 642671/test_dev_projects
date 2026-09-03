# Codex 第三方模型接入统一文档

> 适用机器：本机（Windows）。最近更新：2026-09-01。
> 本目录统一收编 Codex 接入第三方模型相关的说明；配置文件本身的真实位置不变，文档负责索引、解释与排障。

> 当前 NewAPI、默认模型、历史 provider 兼容和重启验收基线，以 `07_NewAPI稳定修复与重启验收.md` 为准。较早文件保留历史接入背景，部分已移除 Provider/route 只作为历史记录。

## 背景一句话

Codex 不直连模型厂商，而是先走 CCSwitchMulti 本地代理（`http://127.0.0.1:15721/v1`），由代理按模型名路由到 OpenAI 官方、DeepSeek、SiliconFlow、Zhipu GLM、公司 9007 网关或 Noontec NewAPI。

## 目录结构

| 文件 | 内容 |
| --- | --- |
| `README.md` | 本页：总览、关键文件速查、启动顺序、安全约定 |
| `01_架构与关键文件.md` | 请求链路、各层配置归属、关键文件作用 |
| `02_模型目录与路由.md` | 模型目录条目、路由匹配规则、如何新增模型 |
| `03_操作与验证.md` | 日常使用、切换模型、连通性验证、网络分流规则 |
| `04_故障排查与历史修复.md` | 常见故障表 + 左侧历史记录修复 Skill 用法 |
| `05_9007公司模型接入手册.md` | 公司 9007 模型从零接入完整手册（由原 guides 目录迁移） |
| `06_ZhipuGLM接入实录.md` | Zhipu GLM 从 Provider 到 Codex 选择器的完整同步实录（2026-08-27） |
| `07_NewAPI稳定修复与重启验收.md` | NewAPI、`max` 推理、图片能力、旧任务 provider 修复、备份及重启后验收基线 |
| `scripts/verify-newapi-after-restart.ps1` | 重启前后逐项比较并真实请求两个 NewAPI 模型的只读脚本 |

## 关键文件速查

| 文件 | 作用 |
| --- | --- |
| `C:\Users\twm\.codex\config.toml` | Codex 生效配置：provider、默认模型、`base_url` |
| `C:\Users\twm\.codex\cc-switch-model-catalog.json` | Codex 模型目录（14 个模型条目） |
| `C:\Users\twm\.codex\models_cache.json` | 模型缓存，目录更新后需刷新/清理 |
| `C:\Users\twm\.cc-switch\cc-switch.db` | CCSwitchMulti 数据库：Provider、路由、模型映射 |
| `C:\Users\twm\.cc-switch\settings.json` | CCSwitchMulti 设置（本地代理、开机自启、历史迁移） |
| `C:\Users\twm\.cc-switch\logs\cc-switch.log` | 转发日志（实际请求目标） |
| `C:\Users\twm\.cc-switch\logs\codex-router.log` | 路由日志（模型最终到哪个上游、状态码） |
| `D:\self_install\CCSwitchMulti\CCSwitchMulti.exe` | CCSwitchMulti 程序本体 |
| `C:\Users\twm\.codex\skills\codex-history-repair\` | 左侧历史记录修复 Skill |
| `D:\test_dev_projects\ccsm_route_test.ps1` | 本地代理路由冒烟脚本 |
| `D:\test_dev_projects\fix-catalog.ps1` | 旧版历史目录修复脚本（Skill 的前身，会强退 Codex，日常不推荐） |

## 当前生效配置

- provider：`codex_model_router_v2`，`base_url = http://127.0.0.1:15721/v1`，`wire_api = responses`
- 路由开关：`codexRouting.enabled = true`；NewAPI route 为 `router-universal-codex-newapi-noontec`
- 默认目录 ID：`newapi-deepseek-v4-flash-vision-exp`，实际上游模型 `deepseek-v4-flash-vision-exp`，推理强度 `max`，支持文字与图片
- 备选目录 ID：`deepseek-v4-flash-noontec-newapi`，显示名 `newapi-deepseek-v4-flash`，实际上游模型 `deepseek-v4-flash`，推理强度 `max`
- `Noontec NewAPI` 当前上游：`http://10.18.2.100/v1`，由 CCSwitchMulti 将 Codex Responses 请求转换为 Chat Completions
- 为旧任务保留 `[model_providers.cc-switch-official]` 兼容定义；当前活动 provider 仍为 `codex_model_router_v2`

## 启动顺序

1. CCSwitchMulti（已配置开机自启、静默启动）
2. Clash Verge（规则模式，不要用全局模式）
3. Codex Desktop

## 安全约定

1. 公司认证 Key 属于内网凭据，本文档不明文保存；完整值只存在于本机 CCSwitchMulti Provider 配置中。
2. 9007 网关 `10.18.10.140` 仅公司网段可达；离开公司网络时请切回 GPT 等可用模型。
3. 修改 config / 模型目录 / 路由后，需要刷新模型缓存并重启 Codex 才生效；修复历史记录请优先使用 Skill 的在线方式，不要随意强退 Codex。
