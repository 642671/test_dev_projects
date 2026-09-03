# 停用 CCSwitchMulti 并让 Codex 直连 NewAPI

## 最终结构

切换完成后，Codex 直接访问：

```text
http://10.18.2.100/v1
```

不再经过 `http://127.0.0.1:15721/v1`。API Key 从现有 CCSwitchMulti Provider 安全迁移到用户级环境变量 `TWM_NEWAPI_API_KEY`，不会写入 TOML、脚本或本文档。

Provider ID 仍保留为 `codex_model_router_v2`。这个名字只是历史任务的稳定标识，不代表请求仍会经过 CCSwitchMulti。保留它可以避免历史任务出现 `Model provider not found`。

## 模型

- 默认模型：`deepseek-v4-flash-vision-exp`
- 默认推理强度：`max`
- 视觉模型输入：`text,image`
- 文字模型：`deepseek-v4-flash`

NewAPI 当前只提供上述两个真实模型。因此，历史任务中旧的视觉别名会迁移到视觉模型，其他已经不存在的别名会迁移到文字模型。

## 正式切换步骤

当前对话仍通过 CCSwitchMulti 通信，所以不要提前关闭路由。准备切换时严格按下面顺序操作：

1. 在 CCSwitchMulti 托盘图标上选择“退出”。只关闭窗口不够，因为它会最小化到托盘。
2. 正常退出 Codex Desktop，确认窗口和托盘进程都已结束。
3. 打开 PowerShell，运行：

```powershell
& 'D:\test_dev_projects\docs\codex-model-integration\scripts\apply-direct-newapi-cutover.ps1'
```

4. 看到 `applied : True` 后，只打开 Codex Desktop，不要再打开 CCSwitchMulti。
5. 新建一个测试任务，发送文字请求；再附加一张图片，要求模型说明图片内容。
6. 打开一个旧任务并继续发送一条消息，确认历史任务可以正常加载和续聊。

脚本会自动完成：

- 创建带时间戳的完整切换备份。
- 将 Codex Provider 改为 NewAPI 直连。
- 设置视觉模型为默认模型，推理强度设为 `max`。
- 结构化迁移 SQLite 和历史 JSONL 中的旧模型名。
- 只修改 JSONL 的 `turn_context.payload.model`，不修改对话正文。
- 关闭 CCSwitchMulti 的开机启动、本地代理和 Codex 管理入口。
- 保留 CCSwitchMulti 程序、数据库和 Provider，方便回滚。

## 切换后验收

切换成功应同时满足：

- Codex 可以正常发送文字请求。
- `deepseek-v4-flash-vision-exp` 能根据图片实际内容作答。
- 旧任务能打开并继续。
- CCSwitchMulti 未运行时 Codex 仍可请求模型。
- 本机端口 `15721` 不再是 Codex 请求的必要条件。

只看到模型列表或 HTTP 200 不算完整验收，必须完成真实文字、真实图片和旧任务续聊测试。

## 回滚

若切换后 Codex 无法使用：

1. 退出 Codex Desktop。
2. 确认 CCSwitchMulti 也已退出。
3. 找到应用脚本输出中的 `backup` 目录。
4. 运行：

```powershell
& 'D:\test_dev_projects\docs\codex-model-integration\scripts\restore-pre-direct-newapi.ps1' `
  -BackupDirectory 'C:\Users\twm\.codex\backups\direct-newapi-cutover-实际时间戳'
```

回滚会恢复 Codex 配置、历史数据库、历史 JSONL、CCSwitchMulti 设置和原有开机启动状态。完成后再启动 CCSwitchMulti，然后启动 Codex。
