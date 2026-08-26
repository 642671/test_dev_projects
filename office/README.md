# office：Codex 自动生成测试用例

这是一个 PRD 转测试用例工作区。把 PRD 放进 `00-输入需求/`，Codex 会按你的固定格式生成需求分析、测试计划和 Excel 测试用例。

## 目录结构

```text
D:\test_dev_projects
├── .agents\skills\generate-prd-testcases\   Codex 技能（自动执行流程）
└── office
    ├── 00-输入需求\{项目名}\                放 PRD 和 UI 参考图
    ├── 01-需求分析\{项目名}\                需求模型、测试范围
    ├── 02-测试用例\{项目名}\                单模块 xlsx、合并 xlsx、评审
    ├── AGENTS.md
    └── README.md
```

## 日常使用

1. 打开 Codex，工作目录选择 `D:\test_dev_projects`，建议开一个新任务，确保技能 `$generate-prd-testcases` 被加载。
2. 在 `00-输入需求/` 下建项目文件夹，例如 `00-输入需求/存储管理/`。
3. 放入 PRD 文件，例如 `01_优化磁盘插拔接口阻塞PRD.md`。
4. 说下面任意一句即可：

```text
用 $generate-prd-testcases 处理 office/00-输入需求/存储管理
```

```text
用 $generate-prd-testcases 处理 office/00-输入需求/存储管理/01_优化磁盘插拔接口阻塞PRD.md
```

```text
用 $generate-prd-testcases 重新生成 office/00-输入需求/存储管理 的测试用例
```

```text
用 $generate-prd-testcases 评审 office/02-测试用例/存储管理 的测试用例
```

5. Codex 会生成：

```text
01-需求分析/存储管理/需求模型.json
01-需求分析/存储管理/测试范围.md
02-测试用例/存储管理/01_优化磁盘插拔接口阻塞.xlsx
02-测试用例/存储管理/测试用例.xlsx
02-测试用例/存储管理/评审/评审记录.md
```

6. 打开 Excel 执行测试，在“验证结果”列填 `通过/失败/阻塞/未执行`。

## 固定测试用例格式

字段名称和顺序固定为 10 列，不得修改：

```text
编号	模块	用例名称	优先级	前置条件	操作步骤	输入数据	预期结果	验证结果	备注
```

- 编号示例：`STO-DISK-001`
- 模块示例：`存储管理-磁盘`
- 验证结果默认：`未执行`
- 备注无内容时：`-`

## 已确认的生成规则

- 前置条件只保留当前用例真正依赖的状态，尽量精简为 1-3 条。
- 操作步骤不写单独的“打开存储管理”，进入具体页面合并为一步，例如“进入存储管理-磁盘页面”。
- 插拔类场景直接写“插入磁盘 / 拔出磁盘”。
- 输入数据只写与场景直接相关的数据，插拔类场景写“测试磁盘：1块”。
- 输入数据与预期结果必须一一对应，按相同编号配对。
- 前置条件、操作步骤、输入数据、预期结果中的每个编号项独立换行。
- 生成文本预览时字段之间使用 Tab 分隔。

## 测试场景

Codex 生成用例时按 11 个功能测试场景维度分析：

1. 主流程
2. 默认状态
3. UI场景
4. 输入校验
5. 异常场景
6. 权限场景
7. 重复操作
8. 中断恢复
9. 状态场景
10. 数据持久化
11. 功能联动

存储管理类需求还会检查 UI、API、Linux 后台、数据一致性四层验证。

## 优先级

P0 核心业务和高风险场景；P1 重要业务场景；P2 低风险场景。

## 修改入口

- 改生成规则：`D:\test_dev_projects\.agents\skills\generate-prd-testcases\SKILL.md`
- 改完整规范：`D:\test_dev_projects\.agents\skills\generate-prd-testcases\references\tos-testcase-spec.md`
- 改 Excel 格式：`D:\test_dev_projects\.agents\skills\generate-prd-testcases\scripts\build_excel.py`
- 改需求内容：修改 `00-输入需求/` 下 PRD，再让 Codex 重新生成。
