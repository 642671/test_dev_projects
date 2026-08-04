# 存储管理重构测试工作区

本仓库当前以**存储管理应用重构测试**为中心，主要维护接口测试设计真源、Apifox 配套资产、pytest 自动化代码、批处理工具和项目文档。

## 核心资产

| 路径 | 职责 |
|---|---|
| `storagemanager/` | 存储管理应用重构及版本资产；当前业务中心，`.deb` 仅本地保留 |
| `接口测试用例/` | 接口测试核心交付物：Excel 真源、Apifox 脚本、变量追踪和执行规划 |
| `test_automation/` | pytest 自动化体系：API、UI、性能测试及公共模块 |
| `tools/` | 正式、可复用的工具 |
| `docs/` | 项目文档唯一正式入口 |
| `temp_scripts/` | 历史批处理工作台；本地只读参考，不作为正式工具入口 |
| `archives/` | 历史备份和清理快照 |

完整现状见：

- `docs/guides/01_项目目录说明.md`
- `docs/guides/15_项目综合状态报告_20260804.md`
- `docs/guides/17_项目目录重建方案_20260804.md`

## 当前接口测试基线

- Excel 真源：`接口测试用例/单个接口测试用例/存储管理单接口测试用例.xlsx`
- 规模：8 个 Sheet、124 个接口分组、2825 条用例。
- 九维体检：2026-08-04 修复后为 0 问题。
- Apifox：修复前名称/存在性对账为 2704 = 2704；现有对账脚本不比较请求内容。

## 常用命令

```powershell
# 九维结构体检
node tools\api_case_pipeline\all_sheet_check.js

# Excel 与 Apifox 名称/存在性对账（需要 Apifox CLI 和项目权限）
node tools\api_case_pipeline\reverse_check.js

# pytest 全部测试
py -m pytest

# 仅接口自动化
py -m pytest test_automation\api_testing\testcases
```

Windows 环境使用 `py -m` 调用 Python/pip。PowerShell 不使用 Bash 的 `&&` 语法。

## 工作约束

- Excel 是接口测试设计真源；真实执行结果禁止推测填写。
- Apifox 写入前必须先读取目标资源、使用 CLI Schema 校验，并在写入后回读验证。
- `temp_scripts/`、`archives/`、`node_modules/` 和本地编辑器状态不提交。
- `miaoqi/` 是个人素材，不移动、不修改、不提交。
- 目录重建期间禁止未经检查直接执行 `git add .`。
- 破坏性测试和存储管理应用代码修改需要用户单独授权。

## Git 状态说明

目录重建已经提交完成，`win` 与 `main` 以本次同步后的同一提交为准。已停用的 `tos_api_cli_tester` 保存在本地 `archives/inactive_projects/`，不进入提交；完整迁移记录见目录重建方案。
