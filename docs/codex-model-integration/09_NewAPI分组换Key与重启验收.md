# NewAPI 分组换 Key 与重启验收

> 操作日期：2026-09-23
>
> 当前阶段：数据库切换已完成并通过只读验证，等待用户完整重启
> CCSwitchMulti 和 Codex。

## 1. 当前分组

| 项目 | 值 |
| --- | --- |
| 当前分组 ID | `universal-codex-950cc769853e4620b148532ead68beb2` |
| 当前分组名称 | `Noontec NewAPI (New Key)` |
| 当前分组用途 | 使用新 Key，保留原 Provider ID 和全部路由引用 |
| 旧 Key 分组 ID | `universal-codex-newapi-noontec-old-key-20260923` |
| 旧 Key 分组名称 | `Noontec NewAPI (Old Key)` |
| 当前 Codex 路由 | `router-universal-codex-newapi-noontec` |
| 当前路由目标 | 原 Provider ID，因此模型和历史兼容项不变 |

两个分组包含相同的 Base URL、模型目录、推理声明和协议设置，差异只在
`settings_config.auth.OPENAI_API_KEY`。

## 2. 已完成验证

- 新 Key 直接请求 `http://10.18.2.100/v1/responses` 返回 HTTP 200。
- 新 Key 返回验收文本 `KEY_CHECK_OK`。
- 数据库中当前分组的 Key 与目标新 Key 一致。
- 复制的旧 Key 分组与修改前 Key 一致。
- 当前分组与旧 Key 分组的模型和 Provider 配置一致。
- 当前路由仍指向原 Provider ID，没有改动模型目录或历史任务。

只读验证命令：

```powershell
py -3 D:\test_dev_projects\docs\codex-model-integration\scripts\clone-newapi-provider-new-key.py --verify
```

命令会隐藏输入 Key，只输出布尔检查结果，不会修改数据库。

## 3. 重启步骤

1. 从系统托盘彻底退出 CCSwitchMulti。
2. 完全退出 Codex。
3. 先启动 CCSwitchMulti。
4. 再启动 Codex。
5. 回到任务发送 `新Key分组已重启`。

不要只关闭窗口而不退出托盘进程。数据库变更需要 CCSwitchMulti 重启后才会
加载到运行内存。

## 4. 重启后验收

重启后需要检查：

1. CCSwitchMulti 进程启动时间晚于本次数据库切换时间。
2. `Noontec NewAPI (New Key)` 和 `Noontec NewAPI (Old Key)` 两个分组都存在。
3. 当前 NewAPI 路由仍指向原 Provider ID。
4. 新 Key 的隐藏输入验证仍然通过。
5. 本地路由文字请求返回 HTTP 200。
6. 本地路由图片请求能真实识别已知测试图，不只检查 HTTP 状态。
7. 路由日志中的有效 Provider 名称为 `Noontec NewAPI (New Key)`。

## 5. 备份与回滚

本次修改前备份：

```text
C:\Users\twm\.cc-switch\backups\newapi-new-key-20260923_142011
```

备份包含：

- `cc-switch.db`
- `config.toml`
- `cc-switch-model-catalog.json`
- `settings.json`

回滚必须在 CCSwitchMulti 和 Codex 完全退出后进行。不要直接覆盖正在使用
WAL 的 `cc-switch.db`，应先确认进程已退出，再按实际 Provider 字段做最小恢复。

本次操作没有记录或输出任何 API Key。
