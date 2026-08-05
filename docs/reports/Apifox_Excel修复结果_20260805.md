# Apifox ↔ Excel 对账修复结果（2026-08-05）

## 结论

- Excel 已完成 119 个单元格修复，并由原生 Excel 打开、保存。
- Apifox AI 分支已完成 202 个单接口用例修复，覆盖 96 个接口；202/202 均已回读核验。
- 906 个断言缺口按当前决定保留，不在本次处理范围内。
- Apifox `main` 未修改、未合并；Git `main` 也未在本次操作中修改。

## Apifox 修复

- 项目 ID：`8122217`
- 来源分支：`main`（ID `7879358`）
- AI 分支：`ai/20260805-from-main-storage-reconcile`（ID `8459871`）
- 用例修改：202 个，涉及 96 个接口
- 内容：198 个认证请求头问题、10 个明确的 Content-Type/请求体冲突、5 个明确的参数或请求体差异；合并重复命中后为 202 个不同用例
- 校验：202 个完整更新载荷全部通过 Apifox CLI Schema 校验；写入后逐个读取，目标字段 202/202 一致

本次没有将 AI 分支合并回 Apifox `main`。合并前应在 Apifox 中人工审阅该分支差异。

## Excel 修复

- 86 个单元格：表单接口的 `Content-Type` 从 `application/json` 改为 `application/x-www-form-urlencoded`
- 32 个单元格：无请求体的 GET 接口移除 `Content-Type`
- 1 个单元格：`卷!H112` 的非法路径参数名由 `das` 修正为 `uuid`，非法值 `asd` 保留

修改前备份保存在 Git 忽略目录 `temp_scripts/存储管理单接口测试用例.before_reconcile_20260805.xlsx`，不纳入版本库。

## 文件完整性核验

当前文件与修改前备份逐单元格比较结果：

- 值差异：恰好 119 个
- 样式差异：0
- 公式差异：0
- Sheet 名称、行列范围、合并单元格、冻结窗格：全部一致
- 当前文件大小：537,760 字节；修改前：537,087 字节

原生 Excel 保存未出现兼容性或覆盖警告。

## 质量门禁

`node tools\api_case_pipeline\all_sheet_check.js` 结果为 8 个 Sheet、总问题数 0。体检规则同步修正为：GET/HEAD 无请求体时不强制要求 `Content-Type`；请求头非空和认证头规则仍继续检查。

完整对账的原始基线仍保留在 [Apifox_Excel完整对账_20260805.md](./Apifox_Excel完整对账_20260805.md)，用于追踪修复前状态；本文件记录 AI 分支和 Excel 的修复后状态。
