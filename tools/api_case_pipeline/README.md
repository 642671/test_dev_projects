# 接口测试用例工具链

这里存放从 `temp_scripts/` 提炼出的正式、可复用工具。历史脚本仍留在本地工作台，不作为项目入口。

## 九维体检

```powershell
node tools\api_case_pipeline\all_sheet_check.js
```

检查 8 个 Sheet 的必填列、组内重名、功能回头、通用场景顺序、ID 连续性、步骤方法/路径一致性和特定请求头规则。成功不代表接口业务语义或实际响应已经验证。

## Apifox 名称/存在性对账

```powershell
node tools\api_case_pipeline\reverse_check.js
```

依赖：

- 已安装并登录 Apifox CLI。
- `.apifox/settings.json` 包含正确的 `projectId`。
- `data/endpoints_dump.json` 与当前 Apifox 项目接口保持同步。

该脚本只验证 Excel 中可导入用例在对应端点是否存在同名用例，并统计数量。它**不比较**请求头、请求参数、请求体、步骤、断言或后置处理器，不能据此宣称 Excel 与 Apifox 内容完全一致。

写入 Apifox 前必须使用 `cli-schema get` 和 `cli-schema validate`，并在写入后回读资源。

## Excel ↔ Apifox 完整只读对账

```powershell
# 使用已有的本地快照
node tools\api_case_pipeline\reconcile_excel_apifox.js

# 先从 Apifox main 只读导出最新原生快照，再生成报告
node tools\api_case_pipeline\reconcile_excel_apifox.js --refresh
```

该工具使用 `config/storage_scope.json` 定义 Excel 真源、Apifox 项目、分支和 8 个存储管理目录。Apifox 原生快照写入 Git 忽略的 `temp_scripts/`，不会提交，也不会修改远端项目。

报告输出：

- `docs/reports/Apifox_Excel完整对账_YYYYMMDD.md`：人工审阅摘要与主要明细。
- `docs/reports/data/apifox_excel_reconcile_YYYYMMDD.json`：全部映射、缺失、额外接口/用例和内容问题。

确定性检查包括端点映射、用例名称/数量、分类、结构化请求头、参数名存在性，以及两侧均可解析时的 JSON 请求体精确比较。查询参数和表单参数的值、自然语言前置条件、步骤和预期结果不能自动证明语义相同；工具只报告可识别断言覆盖，最终变更仍需人工确认。
