# Apifox MCP 与 CLI 接入研究（2026-08-04）

> 状态：已完成官方资料调研、MCP 配置、CLI 升级、Agent Skills 安装和本机认证；尚未写入任何 Apifox 项目。重启 Codex 后 MCP 将读取用户级环境变量。
>
> 目标：让 Codex 能读取 Apifox 项目资料，并以可校验、可回读的方式维护单接口用例、场景用例及相关测试资产。

## 一、结论

Apifox MCP 与 Apifox CLI 不是互相替代关系：

- **MCP**：适合让 Codex 结构化读取项目、接口、模型、文档和测试用例；新版 MCP 也提供部分增删改能力。
- **CLI**：适合可复现的批量资源管理，尤其是单接口用例、场景用例、测试套件、测试数据、分支和测试报告。
- **推荐组合**：MCP 用于理解和检索；CLI 用于 `读取 → 生成 JSON → Schema 校验 → 写入 → 回读验证`。

对本项目而言，Excel 仍是测试设计真源；Apifox 是执行与编排副本。任何批量同步都应先生成差异清单，在 AI 分支或受控目标上验证后再合并。

## 二、官方 MCP 的两条路线

### 2.1 新版远程 HTTP MCP（推荐优先验证）

官方“新版 MCP 内测”已经从本地 stdio 迁移到 Streamable HTTP：

- 不强依赖本地 Node.js。
- 支持多项目、多分支、多模块和按需读取。
- 官方称基础工具从旧版 3 个扩展到 18 个，并提供 100+ 开放接口 Beta 工具包。
- 涵盖接口、数据模型、Markdown 文档、测试用例等资源的查询及部分增删改。

Codex 配置示意：

```json
{
  "mcpServers": {
    "apifox-new-mcp": {
      "type": "http",
      "url": "https://api.apifox.com/mcp",
      "headers": {
        "Authorization": "Bearer <access_token>",
        "X-Apifox-Api-Version": "2025-09-01"
      }
    }
  }
}
```

该功能仍处于内测，具体工具名称和 Schema 必须在连接后通过工具列表实测，不在连接前硬编码假设。

### 2.2 旧版本地 stdio MCP（备用）

旧版通过 npm 包在本地启动：

```json
{
  "mcpServers": {
    "apifox-project": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "apifox-mcp-server@latest",
        "--project=<project-id>"
      ],
      "env": {
        "APIFOX_ACCESS_TOKEN": "<access-token>"
      }
    }
  }
}
```

Windows 官方 FAQ 推荐用 `cmd /c npx ...`。旧版会把接口文档缓存在本地；项目数据更新后需要主动刷新，否则 AI 可能读到旧缓存。

## 三、Apifox CLI 能力

官方 CLI 当前覆盖：

- 项目、团队与项目设置。
- 分支、目录、接口、模型、Mock、环境和变量。
- 单接口测试用例。
- 场景用例、测试套件和测试数据。
- 测试运行、测试报告、Runner 和定时任务。
- 导入导出、文档站及其他项目资源。

### 3.1 单接口测试用例

```powershell
apifox test-case list --project <projectId> --endpoint <endpointId>
apifox test-case get <caseId> --project <projectId>
apifox test-case category --project <projectId>
apifox cli-schema get test-case-create
apifox cli-schema validate test-case-create --file .\case.json
apifox test-case create --project <projectId> --file .\case.json
apifox test-case update <caseId> --project <projectId> --file .\case.json
```

### 3.2 场景用例

```powershell
apifox test-scenario list --project <projectId>
apifox test-scenario get <scenarioId> --project <projectId>
apifox cli-schema get test-scenario-create
apifox cli-schema validate test-scenario-create --file .\scenario.json
apifox test-scenario create --project <projectId> --file .\scenario.json
apifox test-scenario update <scenarioId> --project <projectId> --file .\scenario.json
apifox test-scenario run <scenarioId> --project <projectId> --environment <environmentId>
```

场景用例可以引用接口或单接口用例作为步骤，支持 If、For、Wait、动态参数和步骤间数据传递。复杂场景应先读取已有场景和当前 CLI Schema，再生成 JSON。

### 3.3 安全写入流程

所有 Apifox 写操作执行以下固定流程：

1. `apifox whoami` 验证当前身份。
2. `apifox project get <projectId>` 验证项目访问权。
3. 读取目标资源和目标分支当前状态。
4. 优先在 AI 分支准备变更。
5. `cli-schema get <schema-key>` 获取当前 CLI 版本的结构。
6. 在仓库外或忽略目录生成 JSON 数据文件。
7. `cli-schema validate` 校验。
8. 用户确认变更清单后执行 create/update/delete。
9. `get/list` 回读验证。
10. 用户审查后再合并到 main。

删除、覆盖、批量更新和 main 分支写入始终需要用户再次确认。

## 四、认证和密钥安全

后续需要用户在 Apifox 中创建“API 访问令牌”。令牌不应：

- 粘贴到聊天消息。
- 写入 Git 仓库、Markdown、JSON 示例或截图。
- 出现在命令日志和脚本输出中。

推荐方式：

- MCP：把 token 配置在 Codex 的本机 MCP 凭据位置，不放进项目仓库。
- CLI：由用户在本机交互执行 `apifox auth login`；不要把令牌放进命令行历史。
- 项目 ID 可以写入 `.apifox/settings.json`；它不是密钥。
- `.apifox/.gitignore` 至少忽略 `*.private.*`，任何本地变量和凭据文件也必须忽略。

## 五、当前安装结果

2026-08-04 已完成以下本机接入：

- Apifox CLI 已升级到 `2.2.9`。
- Codex 全局 MCP 已配置为 `https://api.apifox.com/mcp`，通过 `APIFOX_ACCESS_TOKEN` 环境变量取令牌，项目仓库不保存密钥。
- `.apifox/settings.json` 已写入非敏感项目 ID `8122217`。
- `.agents/skills/` 已安装 Apifox 官方 8 个 Agent Skills，并生成 `skills-lock.json`。
- CLI 已成功登录 Apifox 官方账号；用户级 `APIFOX_ACCESS_TOKEN` 已配置。尚未执行项目和分支读取验证，重启 Codex 后再验证 MCP 工具列表和只读访问。

CLI 安装/更新命令为：

官方安装/更新命令为：

```powershell
npm install -g apifox-cli@latest
```

国内镜像备用：

```powershell
npm install -g apifox-cli@latest --registry=https://registry.npmmirror.com/
```

已安装的 Skills：`apifox-cli`、`apifox-test-case`、`apifox-test-automation`、`apifox-test-scenario`、`apifox-branch`、`apifox-cli-checkup`、`apifox-import-export`、`apifox-workflow-api-lifecycle`。

## 六、建议的实际接入顺序

1. 重启 Codex，让 MCP 读取用户级 `APIFOX_ACCESS_TOKEN`。
2. 只读验证身份、项目、分支、接口、单接口用例和场景用例。
3. 用一个临时 AI 分支做“创建一个测试用例 → 回读 → 删除/回滚”的最小验证。
4. 验证通过后再接入 Excel 批量同步工作流。

## 七、官方资料

- [新版 MCP 内测](https://docs.apifox.com/8395000m0)
- [Apifox MCP Server 概述](https://docs.apifox.com/apifox-mcp-server)
- [通过 MCP 使用项目内 API 文档](https://docs.apifox.com/6327888m0)
- [Apifox CLI 概述](https://docs.apifox.com/apifox-cli)
- [安装和运行 CLI](https://docs.apifox.com/install-and-run-cli)
- [CLI 命令选项](https://docs.apifox.com/doc-5637756)
- [使用 Apifox CLI 搭配 AI Agent](https://docs.apifox.com/9212297m0)
