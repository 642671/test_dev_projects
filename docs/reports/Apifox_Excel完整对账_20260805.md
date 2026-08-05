# Excel ↔ Apifox 存储管理完整对账（20260805）

> 本报告由只读工具生成。Apifox 原生快照存放在 Git 忽略的 `temp_scripts/`；执行过程没有修改 Apifox 项目。

## 结论

- Excel 共 2825 条，其中请求方法错误类 121 条不导入，理论应同步 2704 条。
- Apifox 快照包含 135 个存储管理接口、2704 条单接口用例。
- Excel 功能分组映射到 123 个实际端点；其余 12 个为明确不处理范围，不计为缺失。
- 成功同名匹配 2704 条；缺失 0 条；处理范围端点上额外用例 0 条。
- 内容级检查发现 1238 项：高风险 0、中风险 332、低风险 906；详见下表和 JSON 完整明细。

## 统计摘要

| 指标 | 数量 |
| --- | --- |
| Excel 数据行 | 2825 |
| 方法错误类（不导入） | 121 |
| 应同步用例 | 2704 |
| Excel 功能分组 | 124 |
| Apifox 导出接口 | 135 |
| Excel 实际涉及端点 | 123 |
| 明确不处理端点 | 12 |
| Apifox 导出用例 | 2704 |
| 同名匹配用例 | 2704 |
| 缺失用例 | 0 |
| 处理范围额外用例 | 0 |
| 内容问题 | 1238 |

## 内容问题分类

| 类型 | 数量 |
| --- | --- |
| 断言覆盖缺口 | 906 |
| 请求头值不同 | 297 |
| 请求参数缺失 | 6 |
| 请求头缺失 | 29 |

## 按风险级别

| 级别 | 数量 |
| --- | --- |
| high | 0 |
| medium | 332 |
| low | 906 |

## 按 Sheet 问题数

| Sheet | 问题数 |
| --- | --- |
| 概要 | 22 |
| 卷 | 48 |
| 存储池 | 723 |
| 热备盘 | 148 |
| 磁盘 | 114 |
| 虚拟磁盘 | 170 |
| HyperCache | 5 |
| USB设备 | 8 |

## 端点映射失败

_无_

## Excel 有、Apifox 缺失的用例

_无_

## 处理范围端点上的额外 Apifox 用例

_无_

## 内容级问题

| 级别 | 类型 | Sheet/行 | 用例 | 字段 | Excel | Apifox |
| --- | --- | --- | --- | --- | --- | --- |
| low | 断言覆盖缺口 | 概要/12 | 正常获取磁盘概览信息成功 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/13 | 未登录访问获取磁盘概览信息接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 概要/14 | Token失效访问磁盘概览信息 | Cookie | {{expired_Cookie}} | {{NormalUserCookie}} |
| low | 断言覆盖缺口 | 概要/14 | Token失效访问磁盘概览信息 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 概要/15 | Cookie值的X-Csrf-Token与请求头X-Csrf-Token中不相同 | Cookie | {{Cookie}} | {{NormalUserCookie}} |
| low | 断言覆盖缺口 | 概要/15 | Cookie值的X-Csrf-Token与请求头X-Csrf-Token中不相同 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/16 | 无权限用户访问（普通用户） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 概要/17 | 接口响应时间超时 | Cookie | {{Cookie}} | {{NormalUserCookie}} |
| low | 断言覆盖缺口 | 概要/17 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 概要/18 | 畸形 URL 访问磁盘概览接口（携带参数等错误） | Cookie | {{Cookie}} | {{NormalUserCookie}} |
| low | 断言覆盖缺口 | 概要/18 | 畸形 URL 访问磁盘概览接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/2 | 正常获取存储概览信息（有存储池） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/3 | 正常获取存储概览信息（无存储池） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/4 | 存储概览数据容量与健康度逻辑合理 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/5 | 未登录访问存储概览接口应失败 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 概要/6 | Token失效访问存储概览信息 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 概要/6 | Token失效访问存储概览信息 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/7 | Cookie值的X-Csrf-Token与请求头X-Csrf-Token中不相同 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 概要/8 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 概要/8 | 无权限用户访问（普通用户） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/9 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 概要/10 | 畸形 URL 访问存储概览接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 卷/11 | Token失效访问获取卷列表接口 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/13 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/19 | Token失效访问获取卷容量预警配置 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/21 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/27 | Token失效访问获取创建卷资源信息 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/29 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/38 | Token失效访问获取存储状态 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/40 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/52 | Token失效访问获取卷容量占用情况 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/54 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/72 | Token失效访问卷容量统计操作 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/74 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求参数缺失 | 卷/82 | 参数非法 | dasd | 存在 | 未找到 |
| medium | 请求参数缺失 | 卷/83 | 添加任意非法参数 | dsad | 存在 | 未找到 |
| medium | 请求头值不同 | 卷/86 | Token失效访问获取全部卷容量占用情况 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/88 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/100 | Token失效访问获取SSD TRIM信息 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/102 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求参数缺失 | 卷/112 | 参数非法 | das | 存在 | 未找到 |
| medium | 请求头值不同 | 卷/117 | Token失效访问获取卷信息 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/119 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/150 | Token失效访问编辑卷容量预警配置 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/152 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/176 | Token失效访问设置SSD TRIM | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/178 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求参数缺失 | 卷/197 | 添加任意非法参数 | dasdL | 存在 | 未找到 |
| medium | 请求头值不同 | 卷/201 | Token失效碎片整理 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/201 | Token失效碎片整理 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/202 | Cookie值的X-Csrf-Token与请求头X-Csrf-Token中不相同 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/203 | 无权限用户访问（普通用户） | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/203 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/204 | 接口响应时间超时 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/205 | 畸形 URL 访问碎片整理接口（携带参数等错误） | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求参数缺失 | 卷/236 | 请求体不是JSON | dasdas | 存在 | 未找到 |
| medium | 请求头值不同 | 卷/240 | Token失效编辑卷 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/242 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/275 | Token失效访问设置卷压缩 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/277 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/344 | Token失效时创建卷 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/346 | 无权限（普通用户）创建卷 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求参数缺失 | 卷/368 | 添加任意非法参数 | dasdL | 存在 | 未找到 |
| medium | 请求头值不同 | 卷/376 | Cookie值的X-Csrf-Token与请求头X-Csrf-Token中不相同 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/376 | Cookie值的X-Csrf-Token与请求头X-Csrf-Token中不相同 | X-Csrf-Token | {{wrong_X-Csrf-Token}} | {{X-Csrf-Token}} |
| medium | 请求头值不同 | 卷/377 | 无权限用户访问（普通用户） | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/377 | 无权限用户访问（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| medium | 请求头值不同 | 卷/377 | 无权限用户访问（普通用户） | X-Csrf-Token | {{NormalUserCsrfToken}} | {{X-Csrf-Token}} |
| medium | 请求头值不同 | 卷/378 | 接口响应时间超时 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 卷/379 | 畸形 URL 删除卷接口（携带参数等错误） | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/2 | 正常获取存储池列表（detail） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/3 | 正常获取存储池列表（brief） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/4 | 正常获取存储池列表（存储池为空） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/5 | type参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/6 | type参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/7 | 添加任意非法参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/8 | 缺少type参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/9 | type参数错误（不存在的枚举值） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/10 | 未登录访问获取存储池列表接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/11 | Token失效访问获取存储池列表 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/11 | Token失效访问获取存储池列表 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/12 | CSRF不一致访问获取存储池列表 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/13 | 无权限用户访问获取存储池列表 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/13 | 无权限用户访问获取存储池列表 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/14 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/15 | 畸形 URL 获取存储池列表接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/16 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/18 | 正常获取存储池信息 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/19 | 正常获取存储池信息（有热备盘） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/20 | 存储池中所有磁盘系统分区大小相同 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/21 | uuid参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/22 | uuid参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/23 | 参数名大写UUID | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/24 | 添加任意非法参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/25 | 缺少uuid参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/26 | uuid参数错误（不存在的存储池） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/27 | 未登录访问获取存储池信息接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/28 | Token失效访问获取存储池信息 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/28 | Token失效访问获取存储池信息 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/29 | CSRF不一致访问获取存储池信息 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/30 | 无权限用户访问获取存储池信息 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/30 | 无权限用户访问获取存储池信息 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/31 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/32 | 畸形 URL 获取存储池信息接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/33 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/41 | Token失效访问获取创建池资源信息 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| medium | 请求头值不同 | 存储池/43 | 无权限用户访问获取创建池资源信息 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/48 | 正常获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/49 | 正常获取有进行任务的存储池的阵列同步速度及Bitmap（如同步中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/50 | 损坏的存储池无法获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/51 | 可用池无法无法获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/52 | 创建中的存储池无法获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/53 | 删除中的存储池无法获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/54 | 挂载中的存储池无法获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/55 | RAID0阵列的快速修复应该为false | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/56 | raid参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/57 | raid参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/58 | 添加任意非法参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/59 | 缺少raid参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/60 | raid参数错误（不存在的raid） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/61 | 未登录访问获取阵列同步速度及Bitmap接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/62 | Token失效访问获取阵列同步速度及Bitmap | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/62 | Token失效访问获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/63 | CSRF不一致访问获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/64 | 无权限用户访问获取阵列同步速度及Bitmap | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/64 | 无权限用户访问获取阵列同步速度及Bitmap | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/65 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/66 | 畸形 URL 获取阵列同步速度及Bitmap接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/67 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/69 | 正常获取Data Scrubbing配置（存储池有冗余） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/70 | 无冗余磁盘无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/71 | 处于执行数据清理的阵列无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/72 | 有进行任务的存储池无法获取Data Scrubbing配置（如同步中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/73 | 降阶的存储池无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/74 | 损坏的存储池无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/75 | 可用池无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/76 | 创建中的存储池无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/77 | 删除中的存储池无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/78 | 挂载中的存储池无法获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/79 | raid参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/80 | raid参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/81 | 添加任意非法参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/82 | 缺少raid参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/83 | raid参数错误（不存在的raid） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/84 | 未登录访问获取Data Scrubbing配置接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/85 | Token失效访问获取Data Scrubbing配置 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/85 | Token失效访问获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/86 | CSRF不一致访问获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/87 | 无权限用户访问获取Data Scrubbing配置 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/87 | 无权限用户访问获取Data Scrubbing配置 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/88 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/89 | 畸形 URL 获取Data Scrubbing配置接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/90 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/92 | 正常检查卷容量预警（未达到预警则不用发通知） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/93 | 正常检查卷容量预警（存在达到预警的卷发通知） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/94 | 未登录访问检查卷容量预警接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/95 | Token失效访问检查卷容量预警 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 存储池/95 | Token失效访问检查卷容量预警 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/95 | Token失效访问检查卷容量预警 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/96 | CSRF不一致访问检查卷容量预警 | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/96 | CSRF不一致访问检查卷容量预警 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/97 | 无权限用户访问检查卷容量预警（普通用户） | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 存储池/97 | 无权限用户访问检查卷容量预警（普通用户） | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/97 | 无权限用户访问检查卷容量预警（普通用户） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/98 | 接口响应时间超时 | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/98 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/99 | 畸形 URL 访问检查卷容量预警接口（携带参数等错误） | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/99 | 畸形 URL 访问检查卷容量预警接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/100 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/102 | 正常检测硬盘存储池系统分区匹配(存储池中磁盘与非系统盘的候选盘P2分区相同-都是8GB) | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/103 | 正常检测硬盘存储池系统分区匹配(存储池中磁盘与非系统盘的候选盘P2分区相同-都是32GB) | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/104 | 正常检测硬盘存储池系统分区不匹配(存储池中磁盘与系统盘的候选盘P2分区相同) | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/105 | 正常检测硬盘存储池系统分区不匹配(存储池中磁盘与系统盘的候选盘P2分区不同) | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/106 | 正常选中多块候选盘检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/107 | 损坏的存储池无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/108 | 候选盘无P2分区执行检测硬盘存储池系统分区是否匹配成功 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/109 | 降阶的存储池可以执行检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/110 | 处于执行数据清理的阵列无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/111 | 同步中、修复中等任务中的存储池无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/112 | 可用池无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/113 | 创建中的存储池无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/114 | 删除中的存储池无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/115 | 挂载中的存储池无法检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/116 | uuid参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/117 | uuid参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/118 | 添加任意非法参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/119 | 缺少uuid参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/120 | uuid参数错误（不存在的uuid） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/121 | disks参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/122 | disks参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/123 | 缺少disks参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/124 | disks参数错误（不存在的磁盘路径） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/125 | disks的磁盘类型与当前存储池不一致则无法检测 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/126 | 未登录访问检测硬盘存储池系统分区是否匹配接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/127 | Token失效访问检测硬盘存储池系统分区是否匹配 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/127 | Token失效访问检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/128 | CSRF不一致访问检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/129 | 无权限用户访问检测硬盘存储池系统分区是否匹配 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/129 | 无权限用户访问检测硬盘存储池系统分区是否匹配 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/130 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/131 | 畸形 URL 检测硬盘存储池系统分区是否匹配接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/132 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/134 | 正常检查Btrfs配额状态（未启用） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/135 | 正常检查Btrfs配额状态（已启用） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/136 | 对应的卷是ext4文件系统 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/137 | 对应的卷是HyperLock-WORM文件系统 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/138 | mntPath参数为空 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/139 | mntPath参数值非法 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/140 | 添加任意非法参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/141 | 缺少mntPath参数 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/142 | mntPath参数错误（不存在的挂载路径） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/143 | 未登录访问检查Btrfs配额状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/144 | Token失效访问检查Btrfs配额状态 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/144 | Token失效访问检查Btrfs配额状态 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/145 | CSRF不一致访问检查Btrfs配额状态 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/146 | 无权限用户访问检查Btrfs配额状态 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/146 | 无权限用户访问检查Btrfs配额状态 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/147 | 接口响应时间超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/148 | 畸形 URL 检查Btrfs配额状态接口（携带参数等错误） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/149 | 版本号错误（v2改为v3） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/151 | 正常启用Btrfs配额 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/152 | 对应的卷是ext4文件系统 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/153 | 对应的卷是HyperLock-WORM文件系统 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/154 | 请求体为空对象访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/155 | 请求体非JSON格式访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/156 | 请求体添加非法参数访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/157 | 缺少uuid参数访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/158 | uuid参数为null访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/159 | uuid参数为空字符串访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/160 | uuid参数超长(256字符)访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/161 | uuid参数含XSS脚本访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/162 | uuid参数含SQL注入访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/163 | uuid参数类型错误（数字代替字符串）访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/164 | uuid参数含中文和emoji访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/165 | 缺少file_system参数访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/166 | file_system参数为null访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/167 | file_system参数为空字符串访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/168 | file_system参数超长(256字符)访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/169 | 缺少quota_flag参数访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/170 | quota_flag参数为null访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/171 | quota_flag参数为空字符串访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/172 | quota_flag参数为负数访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/173 | uuid参数名大写访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/174 | file_system参数名大写访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/175 | quota_flag参数名大写访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/176 | 未登录访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/177 | Token失效访问启用Btrfs配额接口 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/177 | Token失效访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/178 | CSRF不一致访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/179 | 无权限用户访问启用Btrfs配额接口 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/179 | 无权限用户访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/180 | 启用Btrfs配额接口响应超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/181 | 畸形URL访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/182 | 版本号错误访问启用Btrfs配额接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/184 | 正常获取卷删除状态（无删除中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/185 | 正常获取存储池删除状态（无删除中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/186 | 正常获取卷删除状态（有删除中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/187 | 正常获取存储池删除状态（有删除中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/188 | role参数为空访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/189 | role参数非法访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/190 | role参数名大写访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/191 | role参数添加多余字符访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/192 | 缺少role参数访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/193 | role参数错误访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/194 | 未登录访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/195 | Token失效访问获取删除状态接口 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 存储池/195 | Token失效访问获取删除状态接口 | Cookie | {{expired_Cookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/195 | Token失效访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/196 | CSRF不一致访问获取删除状态接口 | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/196 | CSRF不一致访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/197 | 无权限用户访问获取删除状态接口 | Content-Type | application/json | application/x-www-form-urlencoded |
| medium | 请求头值不同 | 存储池/197 | 无权限用户访问获取删除状态接口 | Cookie | {{NormalUserCookie}} | {{Cookie}} |
| low | 断言覆盖缺口 | 存储池/197 | 无权限用户访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/198 | 获取删除状态接口响应超时 | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/198 | 获取删除状态接口响应超时 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/199 | 畸形URL访问获取删除状态接口 | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/199 | 畸形URL访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| medium | 请求头值不同 | 存储池/200 | 版本号错误访问获取删除状态接口 | Content-Type | application/json | application/x-www-form-urlencoded |
| low | 断言覆盖缺口 | 存储池/200 | 版本号错误访问获取删除状态接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/202 | 正常设置Data Scrubbing（存储池有冗余） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/203 | 无冗余磁盘无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/204 | 处于执行数据清理的阵列无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/205 | 有进行任务的存储池无法设置Data Scrubbing（如同步中） | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/206 | 降阶的存储池无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/207 | 损坏的存储池无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/208 | 可用池无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/209 | 创建中的存储池无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/210 | 删除中的存储池无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/211 | 挂载中的存储池无法设置Data Scrubbing | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/212 | 请求体为空对象访问设置Data Scrubbing接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/213 | 请求体非JSON格式访问设置Data Scrubbing接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/214 | 请求体添加非法参数访问设置Data Scrubbing接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/215 | 缺少raid参数访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/216 | raid参数为null访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/217 | raid参数为空字符串访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/218 | raid参数超长(256字符)访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/219 | raid参数含XSS脚本访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/220 | raid参数含SQL注入访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/221 | raid参数类型错误（数字代替字符串）访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |
| low | 断言覆盖缺口 | 存储池/222 | raid参数含中文和emoji访问接口 | postProcessors | Excel 有预期结果 | Apifox 无可识别断言 |

## 明确不处理的 Apifox 接口

| 目录 | 接口 ID | 接口名 | 方法 | 路径 | 用例数 |
| --- | --- | --- | --- | --- | --- |
| 存储池 | 484618574 | VG监控（内部接口） | get | /v2/storage/VgMonitor | 0 |
| 存储池 | 484618573 | 同步状态监控通知_6.0（已弃用） | post | /v2/VgMonitor | 0 |
| 磁盘 | 484618600 | 更新挂载状态（内部接口） | post | /v1/update_mount_status | 0 |
| 磁盘 | 484618626 | 设置分区权限（内部接口） | put | /v1/part_perms | 0 |
| 磁盘 | 484618604 | 激活弹出的USB设备 | put | /v1/active/{uuid} | 0 |
| 磁盘 | 484618607 | 移除存储设备 | delete | /v1/{name}/{remove} | 0 |
| 磁盘 | 484618585 | 加密存储设备 | put | /v1/encrypt/{action}/{name}/{password} | 0 |
| 磁盘 | 484618601 | 格式化存储设备 | put | /v1/{name}/{fs} | 0 |
| 磁盘 | 484618613 | 获取分区权限列表 | get | /v1/part_perms | 0 |
| 磁盘 | 484618606 | 磁盘自动挂载（未找到） | put | /v1/{name} | 0 |
| 磁盘 | 484618598 | 新磁盘通知 | put | /v1/notice/{name} | 0 |
| 虚拟磁盘 | 489221849 | 00 ISCSI 获取所有数据 | get | /v2/proxy/iSCSIManager/Select | 0 |

## 能力边界

- 名称、数量、端点映射、分类、结构化请求头和参数名存在性为确定性检查。
- 只有 Excel 与 Apifox 两侧请求体均为合法 JSON 时才做请求体精确比较。
- 查询参数和表单参数的值尚未做自动等价判断，不能仅凭本报告宣称内容完全一致。
- Excel “前置条件/操作步骤/预期结果”是自然语言；本版只检查预期结果是否有可识别的 Apifox 断言，不宣称语义等价。
- Markdown 为便于审阅会截断超长明细；JSON 报告保存全部记录。

快照 SHA-256：`3e8d01e999e71016031a118f4891699f264df3cab5c67fda32a8ab6ee2e781ea`
