# 存储管理接口测试项目 — 交接文档与 Codex 提示词

> 面向对象：未来使用 **VSCode + Codex** 继续工作的自己（或接手的 AI 助手）。
> 本文件包含项目概览、核心工作流、规范速查，以及直接可复用的 **Codex 提示词模板**。

---

## 一、项目概览

| 项目 | 说明 |
|------|------|
| 工作区路径 | `D:\test_dev_projects` |
| 核心交付物 | 存储管理模块单接口测试用例（Excel 真源 + Apifox 同步） |
| 涉及模块 | 卷 / 存储池 / 磁盘 / 热备盘 / 虚拟磁盘 / HyperCache / USB设备 / 概要 |
| 测试用例规模 | 8 个 Sheet，124 个接口分组，2825 条用例 |
| 关键外部工具 | Apifox（接口管理）、Node.js 脚本（Excel 审计/对账） |
| 测试设备 | 3 台 TNAS NAS（10.18.15.170/171/173） |
| Python 运行方式 | `py -m pytest`（python/pip 不在 PATH） |
| 7.1 重构代码 | `D:\test_dev_projects\storagemanager`（用户用 VSCode 自管，AI 禁止修改） |

---

## 二、目录结构速查

```
test_dev_projects/
├── 接口测试用例/              ← ⭐ 核心交付物（Excel 真源 + Apifox 脚本 + 变量追踪）
│   ├── 单个接口测试用例/存储管理单接口测试用例.xlsx   ← 唯一真源
│   ├── apifox_scripts/                         ← 后置脚本 01-25
│   ├── apifox_variable_tracking.json           ← 变量追踪（给 AI 看）
│   ├── docs/apifox_variable_tracking.md        ← 变量追踪（给人看）
│   └── 测试执行/                               ← 执行批规划
├── test_automation/           ← pytest 自动化体系（conftest + api_testing + ui_automation）
├── temp_scripts/              ← 批处理工具链（对账/体检/生成/修复，约 5000 脚本，只读参考）
├── docs/guides/               ← 编号文档体系 01-18
├── storagemanager/            ← 存储管理应用重构版本资产（当前业务中心）
├── archives/scripts_legacy/   ← 本地历史一次性脚本归档（Git 忽略）
├── archives/                  ← 历史备份
└── miaoqi/                    ← 个人素材（勿动）
```

> 完整结构见 `docs/guides/01_项目目录说明.md`

---

## 三、核心工作流

### 3.1 单模块测试用例 8 步标准流

1. AI 处理接口通用场景及请求体/参数覆盖
2. 用户补充业务场景用例
3. AI 在对话中给出测试场景，用户审查
4. 审查通过后合并进 Excel（顺序一致，不跨 Sheet 批量）
5. 去重 + 六维审计检查
6. 导入 Apifox（删旧建新，顺序同 Excel）
7. 补齐空列（用例 ID / 所属模块 / 优先级）
8. 冻结前检查（六维终审 + ID 连续性）

> **实际结果列不可推测，须真实跑接口后回填。**

### 3.2 测试用例通过/不通过判定流程

- 首轮：仅采集真实响应体回填 Excel，**不设断言**
- 首轮后：基于真实响应补充断言（code_num=0、HTTP 状态码等），校正预期结果
- 之后：运行才产生有效通过/失败判定

### 3.3 Excel ↔ Apifox 对账

```bash
# 九维结构体检（首选审查工具）
node tools/api_case_pipeline/all_sheet_check.js

# Excel ↔ Apifox main 反向对账
node tools/api_case_pipeline/reverse_check.js
```

---

## 四、关键规范速查

### 4.1 变量命名

| 变量类型 | 命名格式 | 示例 |
|----------|----------|------|
| 存储池 | `cv_pool{N}_xxx` | `cv_pool0_name` → vg0 |
| 热备盘 | `hs{N}_device`、`hs{N}_vg` | `hs1_device`、`hs1_vg` |
| 磁盘 | `disk{N}_device`、`disk{N}_smart_id` | `disk1_device`、`disk1_smart_id` |
| IHM 磁盘 | `Ihm{N}_device`、`Ihm{N}_name` | `Ihm1_device` |
| 卷挂载路径 | `{卷名}_mnt_path` | `lv0_mnt_path` |

> 空变量必须显式 `unset`，禁止残留空值。

### 4.2 测试用例字段重点检查项

- 用例标题与关联功能是否一致（防止复制粘贴错位）
- 畸形 URL 路径是否匹配接口地址
- 前置条件是否准确反映接口依赖
- 操作步骤是否聚焦测试目标

### 4.3 输出格式规范

- 禁止使用 Excel 单元格编号（C12/R11），必须用中文全称
- Bug 报告标准结构：标题 / 前置条件 / 操作步骤 / 期望结果 / 实际结果
- 实际结果必须含完整 JSON 响应体
- 接口测试概念讲解时用 F12 Network 面板实证，前端校验不可信

---

## 五、Codex 提示词模板

> 以下提示词可直接复制到 Codex / VSCode Chat 中使用。根据实际需求调整 `{...}` 占位部分。

### 模板 1：让 Codex 理解项目全貌

```
我正在维护一个存储管理接口测试项目，路径是 D:\test_dev_projects。

请先阅读以下文件了解项目全貌：
1. D:\test_dev_projects\docs\guides\01_项目目录说明.md — 目录结构与职责
2. D:\test_dev_projects\docs\guides\14_项目交接_Codex提示词.md — 本文档（核心规范 + 工作流）
3. D:\test_dev_projects\docs\guides\13_接口测试工作流程.md — 完整工作流详解
4. D:\test_dev_projects\docs\guides\08_接口测试用例编写与审查规范.md — 用例字段规范
5. D:\test_dev_projects\接口测试用例\docs\apifox_variable_tracking.md — 变量依赖链路

阅读完后请用自己的话总结：
- 项目核心目标和交付物是什么
- 主要有哪些目录和各自用途
- 测试用例管理的标准工作流是怎样的
- 有哪些关键命名和格式规范需要遵守
```

### 模板 2：审查测试用例质量（六维审查）

```
请对 Excel 文件 D:\test_dev_projects\接口测试用例\单个接口测试用例\存储管理单接口测试用例.xlsx
进行六维审查，检查以下维度：

1. 用例标题与关联功能是否一致（有无复制粘贴导致模块错位）
2. 请求路径（URL）是否正确、是否与接口文档匹配
3. 前置条件是否准确（接口依赖是否正确描述）
4. 操作步骤是否聚焦测试目标（权限测试应明确角色，方法错误测试不应混入权限描述）
5. 预期结果格式是否符合规范（JSON 格式、字段校验点明确）
6. 请求方法和参数是否正确（GET/POST 方法、必填参数覆盖）

请逐条列出所有发现的问题，按 Sheet 分组，给出具体行号和修改建议。
优先处理高严重性（路径/方法错误）问题。
```

### 模板 3：生成新接口的测试用例

```
接口名称：{接口名称，如 GET /v2/storage/pool/createPool}
接口文档：{粘贴接口文档或 OAS 内容}

请基于上述接口文档，按照项目规范生成标准化测试用例。每个用例需包含：
- 用例标题（格式：{接口名}-{场景描述}）
- 关联功能（所属模块）
- 请求方法 + 请求路径
- 前置条件（真实依赖，如"存在可用磁盘"/"用户已登录"）
- 操作步骤（聚焦测试目标）
- 预期结果（含 HTTP 状态码、code_num、关键字段）

场景覆盖要求：
1. 正常场景：合法参数，预期成功（code_num=0）
2. 参数异常：必填参数缺失、参数类型错误、参数值超边界
3. 鉴权异常：未登录、Token 过期/篡改、权限不足
4. 方法错误：POST 改 GET、GET 改 POST
5. 路径畸形：大小写错乱、路径层级错误
6. 业务约束：资源不足、状态不满足、重复操作

输出格式：表格，列与项目 Excel 一致（13 字段标准）。
```

### 模板 4：Excel ↔ Apifox 对账修复

```
请对比以下两个来源的测试用例，找出差异并给出修复方案：

Excel 源：D:\test_dev_projects\接口测试用例\单个接口测试用例\存储管理单接口测试用例.xlsx
Apifox 项目：{Apifox 项目 ID 或名称}

对账维度：
1. 用例数量是否一致（按 Sheet/接口分组统计）
2. 用例标题是否一一对应
3. 请求方法 + 路径是否匹配
4. 请求体/参数是否一致
5. 前置条件/操作步骤文字是否一致

对每一处差异：
- 判断哪一方为准（Excel 为真源，除非 Excel 有明显错误）
- 给出具体修复操作（Excel 修改 or Apifox 同步）
- 输出差异汇总表

注意：修复 Apifox 侧时不要直接操作，先列出修改清单由我确认。
```

### 模板 5：运行对账脚本

```
请在终端中运行以下命令，检查测试用例质量：

第一步：九维结构体检
node D:\test_dev_projects\tools\api_case_pipeline\all_sheet_check.js

第二步：Excel ↔ Apifox 反向对账
node D:\test_dev_projects\tools\api_case_pipeline\reverse_check.js

请解释输出结果中每个错误/警告的含义，并给出修复优先级排序。
```

### 模板 6：SSH 连接 NAS 测试设备

```
请帮我连接测试 NAS 设备执行以下操作：

SSH 配置：
- 别名 tnas：主机 10.18.15.170，端口 9222，用户 test
- 别名 tnas2：主机 10.18.15.171，端口 9222，用户 test
- 别名 tnas3：主机 10.18.15.173，端口 9222，用户 test

命令：ssh tnas

连接后执行：
{描述需要在 NAS 上执行的操作，如查看磁盘状态、检查日志等}

注意：测试机为生产环境，执行危险操作前请先确认。
```

### 模板 7：分析 API 接口响应

```
以下是一个 TOS API 的响应 JSON：

{粘贴 JSON 响应体}

请分析：
1. 响应结构是否符合通用规范（code_num、msg、data）
2. 各字段含义和数据类型是否正确
3. code_num 和 msg 是否语义一致
4. 是否存在字段缺失或冗余
5. 该接口的后置脚本需要提取哪些变量（参考项目变量命名规范）
```

### 模板 8：生成 Apifox 后置脚本

```
接口：{接口路径，如 GET /v2/disk/list}
响应示例：
{粘贴响应 JSON}

请为上述接口编写 Apifox 后置脚本，要求：
1. 脚本开头用正则扫描并清空旧的同名变量（模式 /^disk\d+_xxx$/）
2. 响应 data 字段标准化为数组（兼容对象/数组/空数组/null）
3. 按索引从 1 开始生成模块变量（如 disk1_device、disk1_name）
4. 空值/undefined/null/NaN 时必须 unset，禁止残留
5. 设置汇总变量（如 disk_count）和完整列表变量
6. 使用 setOrUnset 工具函数（如果环境已定义）

变量命名规范参考：D:\test_dev_projects\接口测试用例\docs\apifox_variable_tracking.md
```

### 模板 9：编写测试用例预期结果

```
接口：{接口路径}
正常请求：{请求方法 + 参数}
实际 API 响应：
{粘贴完整响应 JSON}

请基于以上真实响应，编写该测试用例的预期结果：
- 格式：结构化描述，包含 HTTP 状态码、code_num、msg、关键 data 字段校验点
- 断言点：code_num=0、HTTP 200、必要字段非空、数值字段范围合理
- 参考规范：D:\test_dev_projects\docs\guides\08_接口测试用例编写与审查规范.md

禁止推测，必须以实际响应为准。
```

### 模板 10：执行批（测试执行方案）推导

```
请基于以下信息推导测试执行批方案：

模块：{模块名，如 卷/存储池/磁盘}
测试用例清单：{Excel 中该模块的用例范围}
可用测试机：tnas(3盘位) / tnas2(7盘位) / tnas3(2盘位)

要求：
1. 分析用例的变量依赖关系（哪些用例产出的变量被后续用例消费）
2. 按依赖关系划分执行批次
3. 为每批分配合适的测试机（考虑磁盘位需求）
4. 给出批内用例执行顺序

变量依赖参考：D:\test_dev_projects\接口测试用例\docs\apifox_variable_tracking.md
```

---

## 六、常用命令速查

```bash
# ——— Python 测试 ———
py -m pytest                                          # 跑全部测试
py -m pytest test_automation/api_testing/testcases    # 只跑接口测试
py -m pytest -m smoke                                 # 冒烟测试

# ——— Node.js 脚本 ———
node tools/api_case_pipeline/all_sheet_check.js       # 九维体检
node tools/api_case_pipeline/reverse_check.js         # Excel↔Apifox 名称/存在性对账

# ——— SSH ———
ssh tnas                                              # 连 170 测试机
ssh tnas2                                             # 连 171 测试机
ssh tnas3                                             # 连 173 测试机

# ——— pip（Python 不在 PATH） ———
py -m pip install <包名>                               # 安装依赖
```

> ⚠️ `python`/`pip` 不在 PATH，一律用 `py -m` 前缀。PowerShell 不支持 `&&`，用 `;` 分隔。

---

## 七、文档索引

| 编号 | 文件 | 内容 |
|------|------|------|
| 01 | `01_项目目录说明.md` | 目录结构 + 各目录职责 |
| 02 | `02_UI自动化使用指南.md` | UI 自动化操作 |
| 03 | `03_常用命令速查表.md` | 命令速查 |
| 04 | `04_跨平台同步指南.md` | 家↔公司同步 |
| 05 | `05_冒烟测试用例清单.md` | 冒烟测试清单 |
| 06 | `06_Git提交与同步指南.md` | Git 操作 |
| 07 | `07_Windows中文路径文件读取指南.md` | 中文路径处理 |
| 08 | `08_接口测试用例编写与审查规范.md` | 用例字段规范 |
| 09 | `09_多文件系统磁盘挂载测试指南.md` | 磁盘挂载测试 |
| 10 | `10_磁盘与USB多文件系统挂载测试用例及执行记录.md` | USB 挂载记录 |
| 11 | `11_SSH连接指南.md` | SSH 配置 |
| 12 | `12_SSH密码保存方案说明.md` | 密码保存方案 |
| 13 | `13_接口测试工作流程.md` | 完整工作流 |
| **14** | **`14_项目交接_Codex提示词.md`** | **交接文档 + Codex 提示词（本文）** |
| 15 | `15_项目综合状态报告_20260804.md` | 脚本实测状态与风险 |
| 16 | `16_Apifox_MCP_CLI接入研究_20260804.md` | Apifox 接入方案 |
| 17 | `17_项目目录重建方案_20260804.md` | 目录重建目标与迁移步骤 |
| **18** | **`18_项目当前记忆与交接_20260805.md`** | **当前最高优先级记忆、协作约定与最新状态** |

---

> 最后更新：2026-08-04
> storagemanager 重构目录：`D:\test_dev_projects\storagemanager`（用户 VSCode 自管，AI 禁止修改）
