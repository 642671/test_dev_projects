# 将测试用例导入 Apifox：MCP 与 CLI 使用指南

> 适用对象：需要把测试用例（Excel 用例、OpenAPI 接口定义、Apifox 原生数据）导入 Apifox 的测试工程师。
> 编写依据：TEST-TNAS(8122217) 项目 123 接口 / 2800+ 用例的批量导入实战 + 官方 CLI 文档。
> **当前状态（2026-08）**：Apifox MCP 官方服务已下线（调用返回 `code=51404 not found`），接口定义读取与用例写入**统一走 CLI**。本文仍保留 MCP 配置章节，供官方恢复后参考。

---

## 一、先看这张选型表

| 你要做的事 | 用什么 | 命令入口 |
|---|---|---|
| 导入接口定义（OpenAPI/原生格式） | CLI | `apifox import` |
| Excel 用例 → Apifox 单接口用例（批量） | CLI | `test-case create`（循环） |
| 用例导入测试场景 | CLI | `test-scenario import-steps` |
| 快速浏览接口 Schema | ~~MCP~~ → CLI | `apifox endpoint get`（MCP 已下线） |
| 查看/修改已有用例 | CLI | `test-case list/get/update` |

**分工原则**：MCP 只适合"看一眼"接口 Schema；一切可复现的批量操作必须走 CLI，流程为 `读取 → 生成 JSON → cli-schema 校验 → 写入 → 回读验证`。

---

## 二、环境配置（新成员必做，约 10 分钟）

### 2.1 安装 CLI

前置要求：Node.js ≥ 18（`node -v` 确认）。

```powershell
# 官方安装
npm install -g apifox-cli@latest

# 国内镜像备用（推荐）
npm install -g apifox-cli@latest --registry=https://registry.npmmirror.com/
```

验证安装：

```powershell
apifox --version   # 本项目环境为 2.2.9+
apifox --help
```

### 2.2 登录认证（最关键一步）

**第一步：创建 API 访问令牌。** 打开 Apifox 客户端，路径：`用户头像 → 账号设置 → API 访问令牌 → 新建令牌`。

**第二步：本机登录（在你自己终端执行，不要让 AI 代跑）：**

```powershell
apifox login --with-token <你的TOKEN>
```

**第三步：验证身份：**

```powershell
apifox whoami
```

安全要求（不可违反）：
- Token **不要**粘贴到聊天消息、命令日志、Markdown 或 Git 仓库。
- CLI 凭证保存在 `~/.apifox/config.toml`，不要手动修改或复制它。
- 私有部署环境：所有命令追加 `--api-base-url https://your-server`。

### 2.3 获取项目 ID 并固化

方法一（推荐）：Apifox 客户端 → `项目设置 → 基本设置 → 项目 ID`。
方法二：命令行查询：

```powershell
apifox project list
```

项目 ID 不是密钥，可写入工作区 `.apifox/settings.json` 作为默认值：

```json
{ "projectId": "8122217" }
```

> 本团队固定使用 TEST-TNAS 项目，ID = `8122217`。如无特殊说明，下文 `<projectId>` 均指它。

### 2.4 开启 AI 写入权限（AI 批量导入必做）

CLI/AI 写入 Apifox 时若提示权限受限，二选一：

| 方式 | 操作 | 适用 |
|---|---|---|
| A. 直接编辑权限 | Apifox 客户端 2.8.32+ → `项目设置 → 功能设置 → AI 功能设置 → 外部 AI 编辑权限` 打开开关 | 需直接改 main/迭代分支 |
| B. AI 分支（推荐） | 见下文 4.2，改动隔离在 AI 分支，确认后再合并 | 批量导入、不污染源分支 |

---

## 三、路线 A：导入接口定义（OpenAPI / Apifox 原生格式）

### 3.1 导入前质量门禁（不可跳过）

不要只看"导入命令成功"。先解析 spec 并统计：

| 指标 | 含义 | 风险信号 |
|---|---|---|
| `paths` / `operations` | 接口规模 | 数量多 ≠ spec 完整 |
| `schemas` | 模型数量 | 大项目 schemas 极少 → 疑似"路由骨架" |
| `writes` / `withBody` | 写接口及 body 覆盖 | 写接口多但 body 覆盖少 → 不完整 |
| `emptyObjectBodies` | 空 body 数 | 大量空 body → 强风险，禁止作为最终导入 |

### 3.2 OpenAPI 导入

```powershell
apifox import --project <projectId> --format openapi --file ./openapi.yaml
```

导入前检查每个 operation 是否有**业务化 tags**（如 `存储卷`、`磁盘`），不要按 URL 路径机械分组，否则 Apifox 目录会变成 `api/v1/xxx` 技术路径堆。

### 3.3 Apifox 原生格式导入（迁移 / 备份 / 复制）

```powershell
# 全量导入（默认模块策略 match-name：同名模块匹配则复用，否则新建）
apifox import --project <projectId> --format apifox --file ./project.apifox.json

# 每次复制一套全新模块
apifox import --project <projectId> --format apifox --file ./project.apifox.json --module-import-mode new

# 精确控制模块去向（可重复传，优先级最高）
apifox import --project <projectId> --format apifox --file ./project.apifox.json --module-map "存储卷API=8049476"
```

反向（导出，用于迁移前验证或备份）：

```powershell
apifox export --project <projectId> --format apifox --output ./project.apifox.json
```

### 3.4 导入后验证（必做）

1. 看导入结果中 `ignoreCount`——明显偏高说明旧接口被忽略/项目被污染，不要当作成功。
2. 回读：`apifox endpoint list --project <projectId>` 确认接口总数。
3. 抽查一个读接口 + 一个写接口：`apifox endpoint get <endpointId> --project <projectId>`，确认 requestBody、response、schema 正常。

---

## 四、路线 B：Excel 用例批量导入（团队主力流程）

> 原则：**Excel 是真源，Apifox 是执行副本**；Apifox 用例必须与 Excel 用例严格一一对应（数量、顺序、标题、预期结果）。批量导入一律走 AI 分支。

### 4.1 流程总览（5 步）

```
建AI分支 → pick-to导入接口 → 查分类ID → 生成用例JSON并校验 → 批量create → 回读验证
```

### 4.2 Step 1：创建 AI 分支

```powershell
apifox branch create --project <projectId> --type ai --name ai/20260807-from-main-<模块名> --from main
```

⚠️ 分支名必须符合 `ai/年月日-from-来源分支-模块名` 规范，否则报错。
⚠️ AI 分支初始为**空**，不会自动 clone 源分支资源；且 24 小时无差异会自动归档，中途不要停太久。

### 4.3 Step 2：导入接口资源到 AI 分支（必须先做！）

```powershell
apifox branch pick-to --project <projectId> --type ai --from main --to ai/20260807-from-main-<模块名> --endpoint-ids <接口ID1,接口ID2>
```

AI 分支为空时直接 `test-case create` 会失败——必须先 pick 接口，才能挂测试用例。

### 4.4 Step 3：查询用例分类 ID

```powershell
apifox test-case category --project <projectId>
```

内置 5 类（**每个项目的分类 ID 都不同，必须现场查询**）：正向 / 负向 / 边界值 / 安全性 / 其他。按 Excel 场景把用例映射到对应分类。

### 4.5 Step 4：生成用例 JSON（核心模板）

必填字段：`apiDetailId`、`categoryId`、`parameters`、`commonParameters`、`requestBody`；**`path` 必须显式填写**（不填则 Apifox 中用例 URL 只显示 `/`）。

```json
{
  "name": "正常获取存储概览信息",
  "apiDetailId": "484618538",
  "categoryId": "9119405",
  "method": "get",
  "path": "/v2/storage/overview",
  "parameters": {
    "query": [],
    "path": [],
    "header": [
      { "name": "Content-Type", "value": "application/json", "enable": true },
      { "name": "Cookie", "value": "{{Cookie}}", "enable": true },
      { "name": "X-Csrf-Token", "value": "{{X-Csrf-Token}}", "enable": true }
    ],
    "cookie": []
  },
  "requestBody": { "type": "none" },
  "postProcessors": [
    {
      "type": "assertion",
      "data": {
        "subject": "httpCode",
        "comparison": "equal",
        "value": 200
      }
    }
  ]
}
```

断言取值参考（对应 Excel 预期结果列）：
- 正常场景：`200 + code=true + is_login=true + code_num=0` 四件套；
- Token 失效 / CSRF / 无权限：`403`；
- 未登录：`200 + is_login=false`；
- 复杂逻辑断言用 `type: customScript`（data 为脚本字符串）。

### 4.6 Step 5：Schema 校验 → 批量创建

**写之前必须校验**（CLI 强制流程）：

```powershell
apifox cli-schema get test-case-create        # 获取当前版本结构
apifox cli-schema validate test-case-create --file ./case.json   # 通过后才允许创建
```

批量创建（PowerShell 循环，Node 脚本编排更佳）：

```powershell
apifox test-case create --project <projectId> --branch ai/20260807-from-main-<模块名> --file ./case.json
```

### 4.7 导入后验证

```powershell
apifox test-case list --project <projectId> --branch ai/20260807-from-main-<模块名> --page-size 500
```

- 确认用例总数与 Excel 行数一致；
- 抽查 3~5 条：`test-case get <caseId>` 看 path/参数/断言；
- 到 Apifox 客户端 GUI 抽查 URL 是否完整显示。

### 4.8 合并回 main（确认后再做）

```powershell
apifox branch merge <branchId> --project <projectId> --target main
```

- 合并前先让用户确认变更清单；目标 main 受保护时改走 `merge-request`；
- 合并需要来源/目标分支的直接编辑权限开关均已开启。

### 4.9 实战高频坑速查（都是踩过的）

| 坑 | 现象 | 解法 |
|---|---|---|
| `test-case create` 不传 `path` | 创建成功但 URL 只有 `/` | JSON 必须带 `path` 字段 |
| `--page-size 999` | 被静默截断成 200 条 | 用 `--page-size 500` + 分页循环 |
| CLI 输出带 BOM/提示行 | `JSON.parse` 报错 | `.replace(/^\uFEFF/,'').slice(indexOf('{'))` |
| PowerShell 内联 `node -e` | `$` `"` 被截获 | 一律写成 `.js` 文件再执行 |
| 绑定端点的用例 `update` 改 header | 头只增不减/只减不增 | 未登录场景用**空值覆盖**而非删除头 |
| `folder create --parentId` | unknown option | CLI 只能建顶级目录，层级在桌面端拖 |
| `import-steps` 跨端点 | 报错 | 每个端点单独调用一次 |
| AI 分支 24h 无差异 | 被自动归档 | 中途不长时间停顿，及时合并 |

---

## 五、MCP 配置（官方恢复后参考，当前不可用）

### 5.1 当前状态

MCP 官方服务已下线，`CallMcpTool` 返回 `code=51404 not found`。**不要在新流程里依赖 MCP**；如需接口定义一律用 `apifox endpoint get <endpointId> --project <projectId>`（当前唯一可靠方式）。

### 5.2 新版 HTTP MCP（内测配置，供恢复后使用）

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

Token 放本机 MCP 凭据位置（如用户级环境变量 `APIFOX_ACCESS_TOKEN`），**不放进项目仓库**。工具名是动态哈希后缀（如 `read_project_oas_cv3pwv`），每次刷新都会变，使用前先探测当前工具列表。

### 5.3 旧版本地 stdio MCP（备用配置）

```json
{
  "mcpServers": {
    "apifox-project": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "apifox-mcp-server@latest", "--project=<project-id>"],
      "env": { "APIFOX_ACCESS_TOKEN": "<access-token>" }
    }
  }
}
```

注意：旧版本地缓存接口文档，项目更新后必须主动刷新，否则 AI 读到旧数据。

---

## 六、安全写入流程（所有写操作强制 10 步）

1. `apifox whoami` 验证身份
2. `apifox project get <projectId>` 验证项目访问权
3. 读取目标资源和分支当前状态
4. 优先在 AI 分支准备变更
5. `apifox cli-schema get <schemaKey>` 获取当前版本结构
6. 在忽略目录（如 `temp_scripts/`）生成 JSON 数据文件
7. `apifox cli-schema validate <schemaKey> --file <path>` 校验
8. 用户确认变更清单后执行 create/update/delete
9. `get/list` 回读验证
10. 用户审查后再合并到 main

删除、覆盖、批量更新、main 分支写入——**任何时候都需要用户再次确认**。

---

## 七、新成员自检清单

- [ ] `apifox --version` 正常（≥2.2.x）
- [ ] `apifox whoami` 显示自己的账号
- [ ] `.apifox/settings.json` 有项目 ID
- [ ] 了解自己用「直接编辑权限」还是「AI 分支」
- [ ] 能跑通 `apifox endpoint get` 读取接口定义
- [ ] 能跑通 `cli-schema validate` → `test-case create` 最小闭环
- [ ] 知道 `path` 必填、page-size 上限、token 不落仓库三条红线

---

## 附：命令速查

```powershell
apifox login --with-token <TOKEN>                    # 登录
apifox whoami                                        # 验证身份
apifox project list                                  # 项目列表
apifox endpoint get <epId> --project <pid>           # 接口定义
apifox test-case category --project <pid>            # 分类ID
apifox cli-schema get test-case-create               # 结构
apifox cli-schema validate test-case-create --file x.json
apifox test-case create --project <pid> --file x.json
apifox test-case list --project <pid> --page-size 500
apifox import --project <pid> --format openapi --file spec.yaml
apifox import --project <pid> --format apifox --file p.apifox.json
apifox export --project <pid> --format apifox --output p.apifox.json
apifox branch create --type ai --name ai/20260807-from-main-x --from main
apifox branch pick-to --type ai --from main --to ai/xxx --endpoint-ids 1,2
apifox branch merge <branchId> --project <pid> --target main
```

参考文档：`docs/guides/16_Apifox_MCP_CLI接入研究_20260804.md`、`temp_scripts/Apifox_CLI_MCP_实战手册.md`，官方资料见 [Apifox CLI 概述](https://docs.apifox.com/apifox-cli) 与 [CLI 命令选项](https://docs.apifox.com/doc-5637756)。
