# office 工作区

本目录用于 PRD 自动生成测试用例。

当用户要求“用 $generate-prd-testcases 生成测试用例”“按我的格式生成测试用例”“PRD 转测试用例”或“生成 TOS 测试用例”时执行本工作流：

1. 先读取本目录 `README.md`。
2. 读取技能 `D:\test_dev_projects\.agents\skills\generate-prd-testcases\SKILL.md` 并按其工作流执行。
3. 输入目录：`00-输入需求/{项目名}/`；输出到 `01-需求分析/{项目名}/` 和 `02-测试用例/{项目名}/`。
4. 除非用户明确要求，不修改 `00-输入需求/` 下的原始文件。
