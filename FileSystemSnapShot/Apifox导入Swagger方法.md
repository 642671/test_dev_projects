# Apifox 导入 Swagger 方法

本文记录使用 Apifox CLI 将本地 Swagger/OpenAPI 文件导入独立分支的方法，并包含本次 `FileSystemSnapShot` 导入结果和验证步骤。

## 1. 适用范围

- 项目：`TEST-TNAS`
- 项目 ID：`8122217`
- 源文件：`D:\test_dev_projects\FileSystemSnapShot\swagger.yaml`
- 本次隔离分支：`ai/20260903-from-main-fs-snapshot-import`
- 分支 ID：`8582904`
- 当前状态：Swagger 内容已导入 AI 分支并已合并到 `main`
- 主分支目录：`FileSystemSnapShot`
- 主分支接口数量：276（原有 260 + 新增 16）

> 写入任何 Apifox 项目前，请先确认目标项目、目标分支和覆盖范围。不要在未确认的情况下直接导入主分支。

## 2. 前置检查

在 PowerShell 中执行：

```powershell
apifox --version
apifox auth status
```

确认：

- `apifox` 可用；
- 已登录；
- 当前账号有权写入目标项目。

查看项目及分支：

```powershell
apifox project get 8122217
apifox branch list --project 8122217 --type all
```

## 3. 创建隔离分支

推荐创建 AI 分支，不要直接写入 `main`。AI 分支创建后初始为空，不会自动修改主分支内容。

```powershell
apifox branch create `
  --project 8122217 `
  --type ai `
  --name "ai/20260903-from-main-fs-snapshot-import" `
  --from main
```

命名建议：

```text
ai/年月日-from-main-功能说明
```

创建后回读确认：

```powershell
apifox branch get "ai/20260903-from-main-fs-snapshot-import" `
  --project 8122217 `
  --type ai
```

## 4. 导入 Swagger

本次使用的导入命令：

```powershell
apifox import `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import" `
  --format openapi `
  --file "D:\test_dev_projects\FileSystemSnapShot\swagger.yaml"
```

关键点：

- `--branch` 必须与创建分支时保持一致；
- `--format openapi` 用于 OpenAPI/Swagger 文件；
- `--file` 使用本地文件绝对路径；
- 不传 `--branch` 时，CLI 默认操作主分支。

导入成功响应中的关键计数：

```text
api 16 created
schema 18 created
endpointCase 16 created
security scheme 2 created
error 0
ignore 0
delete 0
```

## 5. 补充 BasePath

本次 CLI 导入时，`basePath: /FileSystemSnapshot` 没有自动拼接到接口路径。为使分支内容与原始 Swagger 一致，需要手动更新接口路径，例如：

```powershell
apifox endpoint update 510331970 `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import" `
  --path "/FileSystemSnapshot/GetVolumeSnapshot"
```

对应原始路径：

| 原始路径 | 修正后的完整路径 |
|---|---|
| `/GetVolumeSnapshot` | `/FileSystemSnapshot/GetVolumeSnapshot` |
| `/GetSnapshotTasks` | `/FileSystemSnapshot/GetSnapshotTasks` |
| `/GetSnapshotTaskMap` | `/FileSystemSnapshot/GetSnapshotTaskMap` |
| `/GetBtrfsVolume` | `/FileSystemSnapshot/GetBtrfsVolume` |
| `/GetSnapshotConf` | `/FileSystemSnapshot/GetSnapshotConf` |
| `/SetSnapshotConf` | `/FileSystemSnapshot/SetSnapshotConf` |
| `/TakeSnapshot` | `/FileSystemSnapshot/TakeSnapshot` |
| `/DelSnapshot` | `/FileSystemSnapshot/DelSnapshot` |
| `/DelAllSnapshot` | `/FileSystemSnapshot/DelAllSnapshot` |
| `/LockSnapshot` | `/FileSystemSnapshot/LockSnapshot` |
| `/RestoreSnapshot` | `/FileSystemSnapshot/RestoreSnapshot` |
| `/QueryStatus` | `/FileSystemSnapshot/QueryStatus` |
| `/GetGlobalStatus` | `/FileSystemSnapshot/GetGlobalStatus` |
| `/GetInitData` | `/FileSystemSnapshot/GetInitData` |
| `/lang` | `/FileSystemSnapshot/lang` |
| `/log` | `/FileSystemSnapshot/log` |

## 5.1 给接口补充必填请求头

本次所有 SnapShot 接口均在 AI 分支上增加了以下两个必填 Header，变量名称严格保持：

```text
X-Csrf-Token: {{X-Csrf-Token}}
Cookie: {{Cookie}}
```

Apifox 参数中的对应配置：

| Header 名 | 示例值 | 必填 | 启用 |
|---|---|---|---|
| `X-Csrf-Token` | `{{X-Csrf-Token}}` | 是 | 是 |
| `Cookie` | `{{Cookie}}` | 是 | 是 |

实现要求：

- 只修改隔离分支，不修改 `main`；
- 使用 `endpoint update --file` 提交完整参数对象，避免覆盖原有的 Query、Body 和 Response；
- 如果接口已有其他 Header（例如 `/lang` 的 `Accept-Language`），保留原 Header，只新增或替换这两个认证 Header；
- 使用 `{{X-Csrf-Token}}` 和 `{{Cookie}}` 变量，让后续登录接口提供实际凭证；
- 更新后必须用 `endpoint get` 回读，确认 Header、Query、Body、Response 都保留。

更新示例：

```powershell
apifox endpoint update <ENDPOINT_ID> `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import" `
  --file <ENDPOINT_JSON_FILE>
```

## 6. 回读验证

确认接口：

```powershell
apifox endpoint list `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import" `
  --page 1 `
  --page-size 500
```

确认数据模型：

```powershell
apifox schema list `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import"
```

抽查一个读取接口和一个写入接口：

```powershell
apifox endpoint get 510331970 `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import"

apifox endpoint get 510331976 `
  --project 8122217 `
  --branch "ai/20260903-from-main-fs-snapshot-import"
```

确认主分支未被修改：

```powershell
apifox endpoint list --project 8122217 --branch main --page 1 --page-size 500
```

## 7. 本次导入与合并结果

源文件与分支内容对账结果：

- 接口：源文件 16 个，分支回读 16 个；
- 数据模型：源文件 18 个，分支回读 18 个；
- 安全方案：`CookieAuth`、`XCsrfToken`，共 2 个；
- 目录：`FileSystemSnapShot` 顶层目录，下含快照查询、快照配置、快照操作、状态查询、页面基础数据、国际化、日志，共 7 个子目录；
- 主分支：合并前 260 个接口，合并后 276 个接口，新增 16 个快照接口。

直接合并结果：

```text
HTTP_API created 16
HTTP_API_CASE created 16
DATA_SCHEMA created 18
API_FOLDER created 8
SECURITY_SCHEME created 2
SECURITY_SCHEME_FOLDER created 1
failed 0
```

接口检查结果：

- 16 个接口的方法和路径均存在；
- 查询参数已导入，例如 `GetVolumeSnapshot` 的 `volume`、`task_name`；
- POST/DELETE 接口请求体引用已导入；
- 200 响应均为 `application/json`；
- 数据模型引用正常；
- BasePath 已补全。
- 16 个接口均已增加必填 Header `X-Csrf-Token` 和 `Cookie`；
- `/lang` 原有可选 Header `Accept-Language` 已保留。

## 8. 合并到主分支

本次已完成直接合并到 `main`，并在主分支创建 `FileSystemSnapShot` 目录。合并时显式传入了接口、接口用例、API 目录、数据模型、安全方案和安全方案目录的资源 ID。

如使用 CLI，需要额外确认分支权限和合并请求流程：

```powershell
apifox merge-request --help
apifox branch merge --help
```

注意：

- 合并前先查看差异；
- 主分支或目标分支受保护时，优先使用 merge request；
- 不要在未确认时直接合并；
- 本次主分支未受保护，已使用直接 merge；
- 合并完成并确认主分支正常后，再考虑归档该 AI 分支。

## 9. 注意事项

- Swagger 全局安全要求 `CookieAuth` 和 `XCsrfToken` 已作为安全方案导入，但当前 CLI 导入不会自动把这两个方案绑定到每个接口。如果需要接口级认证展示，建议合并前在 Apifox 中确认并关联，或使用 Apifox 支持该能力的导入方式。
- `branch get` 的项目统计可能滞后，实际应以 `endpoint list` / `schema list` 回读结果为准。
- 导入响应报告 `endpointCase=16`，但 CLI 在 AI 分支执行 `test-case list` 当前返回 0。这与 AI 分支的单接口用例可见性有关；合并到主分支后应再次核对接口用例是否保留。
- 不要删除、归档或覆盖旧分支；
- 不要重复对主分支执行覆盖式导入；
- 不要在文档中记录或输出 API Token；
- 若使用浏览器页面展示的 Open API，Token 应通过环境变量或安全方式提供。

## 10. Open API 方式（参考）

右侧 Apifox 页面展示的是 HTTP Open API：

```text
POST https://api.apifox.com/v1/projects/{projectId}/import-openapi
```

请求头：

```text
X-Apifox-Api-Version: 2024-03-28
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

请求体示例：

```json
{
  "input": {
    "url": "https://example.com/swagger.json"
  },
  "options": {
    "targetEndpointFolderId": 76,
    "targetSchemaFolderId": 60,
    "endpointOverwriteBehavior": "deleteUnmatchedResources",
    "schemaOverwriteBehavior": "KEEP_EXISTING",
    "updateFolderOfChangedEndpoint": true,
    "prependBasePath": true
  }
}
```

注意：

- 该方式适合远程 URL；
- `endpointOverwriteBehavior: deleteUnmatchedResources` 可能删除目标项目中未匹配的旧接口；
- `prependBasePath: true` 可避免本次 CLI 导入遗漏 `basePath` 的问题；
- 本地文件优先使用 CLI 导入，更容易控制目标分支。
