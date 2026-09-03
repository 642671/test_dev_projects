# NewAPI 稳定修复与重启验收

> 修复日期：2026-09-01
>
> 当前阶段：重启前基线已建立并通过。等待用户重启 Codex 后执行第二轮验收。
>
> 本文是本机 NewAPI 与历史任务兼容问题的当前记录；若旧文档与本文冲突，以本文和实时配置为准。

## 1. 本次目标

1. 确认 Noontec NewAPI 分组是否真实可用，而不是只看模型列表。
2. 默认使用 `deepseek-v4-flash-vision-exp` 上游模型，支持图片，推理强度为 `max`。
3. 备选显示名称为 `newapi-deepseek-v4-flash`，上游模型为 `deepseek-v4-flash`，推理强度为 `max`。
4. 修复旧任务因 `Model provider cc-switch-official not found` 无法继续的问题。
5. 在重启前留下可恢复备份和语义基线，重启后逐项检查是否被覆盖。

## 2. 根因与修复

### 2.1 旧任务无法打开

旧任务的会话元数据曾记录 provider `cc-switch-official`，而 CCSwitchMulti 后来把当前 provider 切换为 `codex_model_router_v2`。当 `config.toml` 只定义新名称时，旧任务恢复阶段找不到原 provider，于是直接报错，尚未进入模型请求阶段。

已完成：

- 使用 `codex-history-repair` 将 3 条残留历史任务的活动 provider 标签统一为 `codex_model_router_v2`。
- 修复后 `state_5.sqlite` 中 101 条未归档任务均使用 `codex_model_router_v2`。
- 在 `config.toml` 保留 `[model_providers.cc-switch-official]` 兼容定义，并让它继续进入 `http://127.0.0.1:15721/v1` 合并路由。
- 未删除或重写历史对话正文，未修改 `auth.json`。

### 2.2 NewAPI 可用，但备选模型可能回退到 high

Noontec NewAPI 实际可用，因此没有替换用户提供的备用连接或密钥。问题出在模型能力元数据：Provider 条目虽然有 `defaultReasoningEffort = max` 等扁平字段，但 CCSwitchMulti 合并路由编译器读取的是模型条目内的 `reasoning` 能力对象。别名 `deepseek-v4-flash-noontec-newapi` 在编译时拿不到 reasoning 能力，目录生成器便回落到默认 `high`。

已完成：

- 在 Noontec NewAPI Provider 的两个模型条目中加入正式 `reasoning` 声明。
- 在 `codex-multirouter` 的对应模型条目中同步同一声明。
- 支持档位固定为 `low / high / max`，默认值固定为 `max`。
- 同步 `config.toml` 与 `cc-switch-model-catalog.json`，备选模型的三种默认字段均为 `max`。
- vision 模型保留 `input_modalities = ["text", "image"]`。

## 3. 重启前正确基线

| 检查项 | 预期值 |
| --- | --- |
| 当前 Codex provider | `codex_model_router_v2` |
| 旧 provider 兼容定义 | `[model_providers.cc-switch-official]` 必须存在 |
| 本地入口 | `http://127.0.0.1:15721/v1` |
| 默认目录 ID | `newapi-deepseek-v4-flash-vision-exp` |
| 默认上游模型 | `deepseek-v4-flash-vision-exp` |
| 默认推理强度 | `max` |
| 默认输入能力 | `text,image` |
| 备选目录 ID | `deepseek-v4-flash-noontec-newapi` |
| 备选显示名称 | `newapi-deepseek-v4-flash` |
| 备选上游模型 | `deepseek-v4-flash` |
| 备选推理强度 | `max` |
| NewAPI route | `router-universal-codex-newapi-noontec`，启用 |
| NewAPI 当前上游 | `http://10.18.2.100/v1` |
| Responses 转换 | CCSwitchMulti 转为 `/v1/chat/completions` |
| 未归档历史任务旧标签数 | `cc-switch-official = 0` |
| 未归档历史任务当前标签数 | `codex_model_router_v2 = 101`（重启后允许随新任务增加） |

可见默认模型带 `newapi-` 前缀，是为了保证选择器明确命中 NewAPI 路由；实际发送给上游的模型名仍是 `deepseek-v4-flash-vision-exp`。

## 4. 重启前验证证据

2026-09-01 12:01 执行只读验收脚本，共 34 项，结果为 `34 passed / 0 failed`：

- 本地 `/v1/models` 返回 HTTP 200，两个目标目录 ID 均存在。
- vision 模型携带真实 PNG 与 `reasoning.effort = max` 请求，返回 HTTP 200。
- 备选模型携带 `reasoning.effort = max` 请求，返回 HTTP 200。
- 路由日志显示两者均命中 `Noontec_NewAPI`，上游状态为 200。
- 当前 Provider 的认证对象与备份逐项一致；脚本只比较结果，不输出认证内容。
- `config.toml` 可以被 Codex CLI 正常解析。

验证脚本：

```powershell
& D:\test_dev_projects\docs\codex-model-integration\scripts\verify-newapi-after-restart.ps1
```

脚本只读检查配置和数据库；实时请求会从本机 `auth.json` 读取已有登录令牌，但不会打印或保存令牌。

## 5. 重启前备份

完整基线目录：

```text
C:\Users\twm\.cc-switch\backups\stable-newapi-pre-restart-20260901_115905
```

| 文件 | 用途 |
| --- | --- |
| `cc-switch.db` | SQLite 一致性备份，包含 Provider、合并路由与 reasoning 声明 |
| `config.toml` | 重启前 Codex 生效配置 |
| `cc-switch-model-catalog.json` | 重启前模型目录 |
| `models_cache.json` | 重启前模型缓存 |
| `history-provider-state.tsv` | 不含对话正文的历史任务 provider 映射 |
| `catalog-provider-state.tsv` | 不含标题和正文的侧栏目录 provider 映射 |
| `pre-restart-verification.json` | 重启前 34 项检查结果 |
| `SHA256SUMS.txt` | 备份文件 SHA-256 校验值 |
| `verify-newapi-after-restart.ps1` | 重启后使用的只读验收脚本副本 |
| `07_NewAPI稳定修复与重启验收.md` | 本记录的备份副本 |

`cc-switch.db` 含现有 Provider 认证配置，只能保留在本机，不得发送、上传或粘贴到聊天中。备份不包含 `auth.json`、日志全文或对话正文。

## 6. 用户重启后的检查顺序

用户完全退出并重新打开 Codex 后，回到本任务说明“已经重启”。随后由 Codex 执行：

1. 确认 `config.toml` 仍能解析，并比较 active provider、兼容 alias 和全局 `max`。
2. 比较默认模型与备选模型的目录字段，检查 vision 仍包含 `image`。
3. 读取 `cc-switch.db`，确认源 Provider 与合并路由中的 reasoning 声明未被覆盖。
4. 在内存中比较当前与备份的 Provider 认证对象，只报告是否一致。
5. 检查历史数据库中是否重新出现 `cc-switch-official` 活动标签，并尝试打开原报错任务。
6. 请求 `/v1/models`，确认两个目标 ID 都存在。
7. 发送 vision 图片请求和备选文本请求，二者都显式使用 `max`。
8. 检查 `codex-router.log` 的 `model`、`effective_name`、`effective_endpoint`、`upstream_url` 和 HTTP 状态。
9. 若有差异，先报告具体字段，再做最小恢复；不得直接覆盖整个数据库。

## 7. 恢复原则

- 不因为文件哈希变化就直接恢复。SQLite 中用量、时间戳和日志索引会正常变化，必须比较语义字段。
- `config.toml` 或模型目录被覆盖时，先备份重启后的版本，再恢复对应单文件。
- Provider/路由被覆盖时，先确认 CCSwitchMulti 当前进程和数据库，再从基线数据库提取目标 Provider/route；不要盲目覆盖整个 `cc-switch.db`。
- 历史标签再次异常时，优先运行：

```powershell
py -3 C:\Users\twm\.codex\skills\codex-history-repair\scripts\repair_history.py --status
py -3 C:\Users\twm\.codex\skills\codex-history-repair\scripts\repair_history.py --apply
```

- 任何恢复动作都不得输出认证信息，也不得删除历史任务。

## 8. 2026-09-01 重启后实际验收结果

### 8.1 已通过项目

- Codex Desktop 已重启，CCSwitchMulti 后续又由用户正常退出并启动两次。
- CCSwitchMulti 新进程能够监听 `127.0.0.1:15721`，官方模型路由持续可用。
- NewAPI 源 Provider、MultiRouter 投影和协议兼容性记录均保留 `openai_responses`。
- NewAPI 两个模型的协议兼容性记录已补齐 `readiness = partial` 与 `selected_transport = open_ai_responses`。
- 默认模型仍是 `newapi-deepseek-v4-flash-vision-exp`，推理强度仍为 `max`，目录输入能力仍为 `text,image`。
- 备选模型 `deepseek-v4-flash-noontec-newapi` 实际请求 HTTP 200，并精确回复验收文本。
- NewAPI 上游 `http://10.18.2.100/v1/responses` 直接携带 PNG 请求时能够正确识别红色图片，证明上游模型和认证本身支持图片。

### 8.2 仍未通过项目

CCSwitchMulti `3.19.2-18` 的 MultiRouter 在实际运行时仍忽略上述 Responses 配置。2026-09-01 15:22 的真实图片请求日志仍显示：

```text
effective_endpoint=/chat/completions
responses_to_chat=true
upstream_url=http://10.18.2.100/v1/chat/completions
```

转换后的请求体只有约 253 字节；视觉模型明确回复图片被省略、当前只有文字输入。因此，视觉模型虽然返回 HTTP 200，但语义验收失败，不能宣称已经稳定修复。

### 8.3 已排除的错误判断

- `/v1/models` 中出现模型，只能证明目录可见，不能证明图片会传到上游。
- `input_modalities = ["text", "image"]` 只能证明目录能力声明正确，不能证明 MultiRouter 转换器保留了图片。
- 图片请求 HTTP 200 不能作为视觉成功证据；必须让模型识别一个已知内容的图片，并严格校验回答。
- 仅修改 `protocol_compatibility_profiles.transport` 或 MultiRouter 投影不足以改变当前版本的运行时选择。

### 8.4 操作边界与恢复记录

- 排查期间曾错误强制结束 CCSwitchMulti，导致本地路由未自动恢复；用户随后重新打开路由。后续禁止由自动化关闭、强制结束或切换总路由开关。
- 修改前数据库备份：
  - `C:\Users\twm\.cc-switch\backups\newapi-protocol-fix-20260901_144842`
  - `C:\Users\twm\.cc-switch\backups\newapi-selected-transport-20260901_151857`
- 两次正常重启后问题仍可复现。下一步应检查 CCSwitchMulti Universal Codex Provider 的运行时协议选择代码或由维护者修复，不能继续靠反复重启或覆盖整个数据库试错。
