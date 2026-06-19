# Qoder 记忆恢复数据

> 此文件包含从 Mac 环境导出的所有 Qoder 记忆内容。
> 在 Windows 端的 Qoder 中打开此项目后，将 `restore_prompt.md` 中的内容粘贴给 Qoder 即可批量重建记忆。

---

## 一、用户偏好记忆

### 1. 用户交互节奏偏好
- **类别**: user_communication
- **关键词**: 用户执行,分步指引,交互节奏
- **内容**: 用户倾向由自己执行终端指令，不希望AI代劳操作；AI应提供清晰、可立即执行的分步操作指引（如'第一步：...'），而非直接调用工具。

---

## 二、项目环境配置记忆

### 2. TOS系统运行环境与认证要求
- **类别**: project_environment_configuration
- **关键词**: http://192.168.64.8:8181,TMSESSNAME Cookie,认证要求
- **内容**: TOS系统运行在http://192.168.64.8:8181，多数接口需携带有效的TMSESSNAME Cookie进行认证，敏感操作还需密码验证。

### 3. Python测试项目运行环境与启动流程
- **类别**: project_environment_configuration
- **关键词**: venv,pip install,pytest,多环境配置,并行测试
- **内容**: 
  - 运行环境要求: Python 3.x
  - 环境配置方式: 多环境YAML配置（config/environments/dev.yaml等）
  - 启动流程: 
    1. 创建虚拟环境 `python -m venv venv`
    2. 激活环境（Linux/macOS: `source venv/bin/activate`；Windows: `venv\Scripts\activate`）
    3. 安装依赖 `pip install -r requirements.txt`
    4. 运行测试：`pytest`（全量）、`pytest -m smoke/api/ui`（标签）、`pytest -n auto`（并行）

### 4. Kimi API Key格式规范：sk-加32位随机字符
- **类别**: project_environment_configuration
- **关键词**: Kimi,API Key,sk-格式,32位,格式校验
- **内容**: Kimi API Key 必须以 `sk-` 开头，后接32位随机字符（如 `sk-aBcDeFgHiJkLmNoPqRsTuVwXyZ012345`），Qoder客户端会校验此格式。该规则为强制性前置校验，不满足将直接拒绝请求。

### 5. 代理运行环境配置
- **类别**: project_environment_configuration
- **关键词**: 443端口,hosts劫持,本地监听
- **内容**: 代理服务需监听本地 443 端口，依赖系统 hosts 文件将 api.moonshot.cn 解析至 127.0.0.1，以实现流量劫持拦截。

### 6. 火山引擎API基础地址
- **类别**: project_environment_configuration
- **关键词**: base_url,火山引擎,API地址
- **内容**: 火山引擎API基础地址为https://ark.cn-beijing.volces.com/api/coding/v3，所有模型请求均转发至此地址。

### 7. Latent Upscale节点标准配置
- **类别**: project_environment_configuration
- **关键词**: bislerp,Latent Upscale,潜空间放大,Hires Fix
- **内容**: Latent Upscale节点缩放算法应选用`bislerp`，该算法在潜空间放大中效果最佳，适用于KSampler输出到第二阶段KSampler之间的放大环节。

### 8. Image Scale节点标准配置
- **类别**: project_environment_configuration
- **关键词**: lanczos,Image Scale,1024×1024,裁剪禁用
- **内容**: Image Scale节点缩放算法应选用`lanczos`（拉索斯），目标尺寸设为1024×1024，裁剪功能必须禁用（crop: disabled）。

### 9. ComfyUI模型缺失导致标签页无法关闭
- **类别**: project_environment_configuration
- **关键词**: ComfyUI,模型缺失,标签页关闭,弹窗阻塞
- **内容**: ComfyUI中若工作流引用了本地缺失的模型（如Checkpoint或LoRA），关闭对应标签页时会弹出提示框并阻止关闭操作。

---

## 三、项目SCM配置记忆

### 10. 项目GitHub远程仓库地址
- **类别**: project_scm_configuration
- **关键词**: GitHub,远程仓库,git remote
- **内容**: 项目远程Git仓库地址为 https://github.com/642671/test_dev_projects.git

### 11. 双分支跨平台协作策略
- **类别**: project_scm_configuration
- **关键词**: main分支,win分支,双平台,Git同步
- **内容**: 项目采用双分支协作模式：`main` 分支用于家庭Mac环境日常开发；`win` 分支专用于公司Windows环境，克隆后直接使用；两端通过 `git merge` 手动同步变更，不自动合并。

---

## 四、项目IDE配置记忆

### 12. Qoder编辑器文件导航规范
- **类别**: project_ide_configuration
- **关键词**: Qoder编辑器,文件路径,UI自动化结构
- **内容**: 在Qoder编辑器中主要编辑以下路径的文件：
  - 定位器：`ui_automation/pages/locators/xxx_locators.py`
  - 页面对象：`ui_automation/pages/pages/xxx_page.py`
  - 测试用例：`ui_automation/testcases/{smoke|functional|regression}/test_xxx.py`
  - 测试数据：`ui_automation/testdata/xxx_data.yaml`
  - 环境配置：`config/environments/{test|dev|prod}.yaml`

### 13. VS Code pytest测试面板完整配置与故障排查
- **类别**: project_ide_configuration
- **关键词**: VS Code,settings.json,pytest配置,venv解释器,测试面板,测试失败排查
- **内容**: 
  - 配置文件：`.vscode/settings.json`
  - python.defaultInterpreterPath: `${workspaceFolder}/venv/bin/python3.12`（Windows上改为`venv\Scripts\python.exe`）
  - python.testing.pytestEnabled: true
  - python.testing.unittestEnabled: false
  - python.testing.cwd: `${workspaceFolder}`
  - python.testing.pytestArgs: `["ui_automation", "api_testing"]`
  - 故障排查：解释器是否正确、cwd是否设为workspaceFolder、修改后需Refresh Tests

---

## 五、项目技术栈记忆

### 14. 三方技术栈集成
- **类别**: project_tech_stack
- **关键词**: Kimi Provider,火山引擎,Qoder
- **内容**: 项目集成 Kimi Provider（Qoder内置）、火山引擎 API（https://ark.cn-beijing.volces.com/api/coding/v3）和 Qoder 客户端，构成三方协同调用链路。

---

## 六、项目介绍记忆

### 15. 测试自动化工作区项目概述
- **类别**: project_introduction
- **关键词**: 测试自动化,Page Object,多环境配置,pytest标签,模块化
- **内容**: 
  - 项目定位: 综合测试自动化工作区，支持家↔公司多地协同开发
  - 核心模块：ui_automation/（Selenium + POM）、api_testing/（Requests）、performance/（性能测试）、testcase_generator/（自动生成）、config/（多环境YAML）、common/（公共工具）
  - 架构特点: 模块化设计、配置驱动、标签化测试执行（smoke/api/ui）

### 16. 多模块自治项目目录结构规范
- **类别**: project_introduction
- **关键词**: 模块自治,目录结构,日志隔离,报告隔离,config分层
- **内容**: 项目采用模块化自治架构，各测试模块（ui_automation/api_testing/performance）独立包含自身运行产出物：logs/（执行日志）、reports/（测试报告含screenshots）、common/仅存放跨模块共享工具代码、config/统一管理配置层、docs/统一存放文档。根目录保持极简。

### 17. 模块完全自治架构设计
- **类别**: project_introduction
- **关键词**: 模块自治,配置隔离,独立environments,common职责边界
- **内容**: 每个测试模块均拥有独立的config/目录，内含专属environments/*.yaml配置文件；模块间配置完全隔离；common/仅提供纯工具代码。

### 18. 项目配置分层设计原则
- **类别**: project_introduction
- **关键词**: 配置分层,环境配置,模块配置,config/environments,testdata
- **内容**: 环境级配置（base_url、credentials）在config/environments/*.yaml；模块级专属配置在<module>/config/；测试数据在<module>/testdata/。

### 19. API文档模块内聚规范
- **类别**: project_introduction
- **关键词**: API文档,模块自治,docs目录
- **内容**: 各测试模块独立管理其专属文档，API相关文档统一存放于api_testing/docs/目录下。

### 20. 工具分层治理架构
- **类别**: project_introduction
- **关键词**: 工具分层,跨项目工具,项目内工具,tools目录,common目录
- **内容**: 跨项目共享工具独立于测试项目；项目内公共工具代码保留在common/；模块私有工具嵌入对应模块目录。

### 21. UI自动化学习路线图
- **类别**: project_introduction
- **关键词**: 学习路径,POM分层,fixture分层,测试分类
- **内容**: 四阶段：1.基础配置 2.Page Object模式 3.测试用例组织 4.进阶能力。推荐起点：tos_login_page.py

### 22. Kimi流量拦截与火山引擎转发架构
- **类别**: project_introduction
- **关键词**: Kimi拦截,火山引擎转发,hosts劫持,代理架构
- **内容**: 通过 hosts 将 api.moonshot.cn 劫持至本地，代理监听 443 端口拦截请求，替换认证头为火山引擎 API Key 后转发。

### 23. 系统看板设置功能能力说明
- **类别**: project_introduction
- **关键词**: 系统看板,设置面板,模块勾选,卡片拖动,默认排序
- **内容**: 支持8个模块勾选控制、时间卡片固定不可拖动、其余卡片可拖动、取消再勾选按字母顺序重排。

### 24. Kimi-for-coding与火山引擎模型映射规则
- **类别**: project_introduction
- **关键词**: 模型映射,Kimi-for-coding,glm-5.1,doubao-seed-2.0-code,minimax-latest
- **内容**: Kimi-for-coding→glm-5.1、glm-5.1→glm-5.1、doubao-seed-2.0-code→doubao-seed-2.0-code、minimax-latest→minimax-latest、MiniMax-M1→doubao-seed-2.0-code、abab7-chat→glm-5.1、abab6.5s/6.5→doubao-seed-2.0-code、abab5.5→minimax-latest、其他→doubao-seed-2.0-code

### 25. TOS登录成功判定：URL由/#/变更为/#/desktop
- **类别**: project_introduction
- **关键词**: TOS,登录判定,URL变更,/#/desktop
- **内容**: TOS登录成功判定依据为URL从`/#/`变为`/#/desktop`，而非依赖可见的'您好'文字元素。

### 26. TOS两步式登录流程（无判定逻辑）
- **类别**: project_introduction
- **关键词**: TOS,两步式登录,用户名,密码,保持登录
- **内容**: 第一步输入用户名并点击'下一步'；第二步输入密码、可选勾选'保持登录'复选框，再点击'下一步'完成登录。

### 27. TOS登录功能流程与成功判定_3
- **类别**: project_introduction
- **关键词**: TOS登录,两步式,保持登录,桌面判定
- **内容**: TOS登录为两步式流程；登录成功判定依据为页面跳转至桌面并显示欢迎信息（如'您好，test'）

### 28. TOS登录功能流程与成功判定_2
- **类别**: project_introduction
- **关键词**: TOS登录,两步式,保持登录,桌面判定
- **内容**: 同上（与_3内容一致）

### 29. TOS桌面右栏上方稳定空白点击区域
- **类别**: project_introduction
- **关键词**: TOS,右栏空白,y=200,稳定点击区域,UI自动化
- **内容**: 右侧栏图标起始Y坐标约为318，其正上方Y=200附近区域（如x=1200, y=200）是稳定空白区域，适用于可靠触发看板隐藏等操作。

### 30. 桌面右侧栏USB设备界面功能
- **类别**: project_introduction
- **关键词**: USB设备,右侧栏,安全移除,存储管理一致性
- **内容**: 仅当存在未被用于创建存储池的USB设备时才出现图标；弹窗展示USB设备列表，与存储管理中一致；安全移除功能逻辑一致。

### 31. 桌面右侧栏图标收起规则增强
- **类别**: project_introduction
- **关键词**: 右侧栏,收起规则,点击空白区域,界面关闭
- **内容**: 帮助图标跳转外部链接；其他图标首次点击展开、再次点击收起、点击桌面空白区域也自动收起。

### 32. 桌面右侧栏搜索界面交互增强
- **类别**: project_introduction
- **关键词**: 右侧栏搜索,双击打开,查看更多,全局搜索跳转
- **内容**: 搜索框支持拖动、输入返回结果、双击进入对应内容、查看更多跳转全局搜索应用。

### 33. 项目使用的动漫风格模型
- **类别**: project_introduction
- **关键词**: 动漫模型,4GB,Stable Diffusion
- **内容**: 使用约4GB的动漫风格SD模型，主要用于机甲、角色、场景等风格化视觉内容生成。

---

## 七、开发实践规范记忆

### 34. TOS Web Desktop显式等待规范
- **类别**: development_practice_specification
- **关键词**: SPA等待,显式等待,轮询超时,TOS自动化
- **内容**: 必须采用显式等待：等待组件渲染完成（可交互状态）、等待API响应（loading消失）、等待应用窗口打开并内容就绪、等待长时操作完成（轮询状态+超时）。

### 35. TOS公共UI组件层规范
- **类别**: development_practice_specification
- **关键词**: UI组件,components,复用,TOS桌面
- **内容**: 建立公共UI组件层（components/），封装数据表格、确认弹窗、表单弹窗、左侧树形菜单、Toast通知条等，Page层通过组合方式复用。

### 36. TOS Fixture模块化分层规范
- **类别**: development_practice_specification
- **关键词**: Fixture分层,模块化,conftest.py,TOS测试
- **内容**: 全局conftest.py定义基础fixture（driver、env_config）；模块级conftest.py自动完成环境准备和清理；用例级直接使用已就绪的模块上下文。

### 37. UI自动化三层职责分离规范
- **类别**: development_practice_specification
- **关键词**: Page层,Business层,TestCase层,职责分离
- **内容**: Page层封装元素定位与基础操作；Business层编排跨Page的业务流程；TestCase层仅包含测试逻辑与断言。

### 38. TOS Web Desktop Page层定义与窗口管理规范
- **类别**: development_practice_specification
- **关键词**: Web Desktop,Page定义,窗口管理,WindowManager
- **内容**: Page层对应功能模块而非URL页面；所有应用运行在同一浏览器Tab内，通过WindowManager控制应用窗口的打开、关闭、切换与焦点。

### 39. 跨平台路径规范：禁止绝对路径
- **类别**: development_practice_specification
- **关键词**: 相对路径,绝对路径,跨平台,os.path.join,pathlib
- **内容**: 所有代码必须使用相对路径，以项目根目录为基准用`os.path.dirname(__file__)`动态拼接；跨平台路径统一用`os.path.join()`或`pathlib.Path`。

### 40. TOS测试失败自动恢复规范
- **类别**: development_practice_specification
- **关键词**: 失败恢复,autouse,环境清理,TOS稳定性
- **内容**: 每个测试执行后必须自动恢复干净环境：通过autouse fixture实现，关闭所有已打开的应用窗口或刷新浏览器回到桌面初始状态。

### 41. 测试用例按业务模块组织规范
- **类别**: development_practice_specification
- **关键词**: 测试用例组织,业务模块,pytest mark
- **内容**: 测试用例目录按业务模块组织（如testcases/storage/test_volume.py），测试类型通过pytest标记管理（@pytest.mark.smoke）。

### 42. 系统看板多卡片场景滚动规范
- **类别**: development_practice_specification
- **关键词**: 看板滚动,可视区域,DOM检查,scroll_dashboard
- **内容**: 当勾选全部模块导致卡片超出可视区域时，必须先执行看板容器内滚动操作，确保目标卡片进入视口后再进行断言或交互。

### 43. 系统看板端到端测试流程规范
- **类别**: development_practice_specification
- **关键词**: 端到端流程,系统看板,取消钉住,看板隐藏
- **内容**: 依次执行打开看板→钉住→拖动验证位移→取消钉住→点击桌面空白处→断言看板容器不可见。

### 44. 模型推理程度默认配置
- **类别**: development_practice_specification
- **关键词**: 推理程度,medium,默认参数
- **内容**: 所有模型请求默认使用中等（medium）推理程度参数。

---

## 八、开发测试规范记忆

### 45. 测试用例字段格式与粒度规范
- **类别**: development_test_specification
- **关键词**: 用例格式,小粒度,输入数据,预期结果,一一对应,用例编号
- **内容**: 
  - 8个字段：用例编号→模块→用例名称→前置条件→操作步骤→输入数据→预期结果→备注
  - 输入数据与预期结果必须严格一一对应（编号对应，条数一致）
  - 小粒度用例：每条只验证一个具体场景
  - 模块字段不可遗漏，同模块用例合并单元格

### 46. 系统看板设置功能测试覆盖规范
- **类别**: development_test_specification
- **关键词**: 看板设置,测试覆盖,勾选验证,拖动验证,排序验证
- **内容**: 必须覆盖：全部8个模块选项显示、单个勾选/取消后卡片显隐、非时间卡片拖动、取消再勾选后按模块名顺序重排。

---

## 九、开发代码规范记忆

### 47. 动漫风格图像生成的提示工程实践规范
- **类别**: development_practice_specification
- **关键词**: 提示词工程,机甲生成,机械质感,反向提示词排除项
- **内容**: 正向提示词前置质量词+主体+机械质感关键词+权重语法强化；反向提示词排除干扰项（soft, rounded, organic等）；每次调参仅改1-2个变量。

---

## 十、经验教训记忆

### 48. GitHub push HTTP/2协议不稳定导致RPC失败
- **类别**: common_pitfalls_experience
- **关键词**: git push,HTTP/2,RPC failed,curl 16
- **内容**: 临时切换为HTTP/1.1协议（`git config --global http.version HTTP/1.1`），推送完成后恢复。

### 49. Qoder自定义模型(BYOK)受账号Credits限制
- **类别**: common_pitfalls_experience
- **关键词**: Qoder,BYOK,自定义模型,Credits,账号限制
- **内容**: 需要足够Credits、不足时模型显示不可用、即使数据库写入配置仍会检查账号权限。

### 50. Qoder对Kimi API Key的sk-前缀格式校验
- **类别**: common_pitfalls_experience
- **关键词**: Qoder,Kimi,API Key,sk-
- **内容**: Kimi的Key必须以'sk-'开头，否则直接拒绝添加模型。

### 51. Node.js/Electron 需显式设置 NODE_EXTRA_CA_CERTS 信任自签名证书
- **类别**: common_pitfalls_experience
- **关键词**: NODE_EXTRA_CA_CERTS,Electron,自签名证书,SSL信任
- **内容**: 必须通过NODE_EXTRA_CA_CERTS环境变量显式指定证书路径。

### 52. 火山引擎API base_url已含版本路径，禁止重复拼接/v1
- **类别**: common_pitfalls_experience
- **关键词**: 火山引擎,Ark API,路径拼接,strip_v1_prefix
- **内容**: base_url已包含/v3，不应再添加/v1前缀，否则404。

### 53. SearchReplace 必须提供 replacements 参数
- **类别**: common_pitfalls_experience
- **关键词**: SearchReplace,replacements,参数校验
- **内容**: 必须提供replacements参数（数组，含original_text和new_text），否则报错。

### 54. 代理日志文件需 root 权限写入
- **类别**: common_pitfalls_experience
- **关键词**: proxy.log,permission denied,root权限,日志写入
- **内容**: proxy.log由root权限进程写入，普通用户无法直接清空。

### 55. ComfyUI新版弃用--metal-smart-memory参数
- **类别**: common_pitfalls_experience
- **关键词**: ComfyUI,Metal,启动参数,M系列芯片
- **内容**: v0.24.1+已移除该参数，功能内置为默认行为；仅保留--force-fp16。

### 56. 代理启动前需替换config.json中的API Key占位符
- **类别**: common_pitfalls_experience
- **关键词**: API Key,config.json,代理启动,火山引擎
- **内容**: 必须将YOUR_VOLCANO_ENGINE_API_KEY_HERE替换为真实有效的API Key。

### 57. Chromium应用需同时配置IPv4和IPv6 hosts拦截
- **类别**: common_pitfalls_experience
- **关键词**: hosts,IPv6,Chromium,代理绕过
- **内容**: 需同时配置127.0.0.1和::1拦截，否则IPv6请求会绕过代理。

### 58. 火山引擎API认证头必须为Bearer且唯一
- **类别**: common_pitfalls_experience
- **关键词**: 火山引擎,Authorization,1004,Bearer
- **内容**: 必须为'Authorization: Bearer <api_key>'格式，禁止携带其他认证头。

### 59. run_in_terminal 工具不可用需替换为 Agent/Bash
- **类别**: common_pitfalls_experience
- **关键词**: run_in_terminal,Agent,Bash,工具不可用
- **内容**: 遇到需执行终端命令的场景应改用Agent或Bash工具。

### 60. 终端执行工具名为Bash而非run_in_terminal
- **类别**: common_pitfalls_experience
- **关键词**: Bash,终端执行,tool not found
- **内容**: 实际可用的终端执行工具为Bash。

### 61. 终端执行工具名应为Bash而非run_in_terminal
- **类别**: common_pitfalls_experience
- **关键词**: Bash,终端执行工具,工具名
- **内容**: 实际可用的终端执行工具是Bash，而非run_in_terminal或read_file。

---

## 十一、重要决策记忆

### 62. 测试工作区核心技术栈与用例格式决策
- **类别**: important_decision_experience
- **关键词**: 测试工作区,技术选型,测试用例格式,GitHub,Selenium
- **内容**: GitHub远程仓库、Python+Selenium+pytest+POM+YAML+截图/HTML/checkpoint、Apifox/Postman接口测试、JMeter+K6性能测试。

### 63. TOS看板端到端验证流程合并决策
- **类别**: important_decision_experience
- **关键词**: TOS看板,端到端验证,用例合并,DOM显隐
- **内容**: 合并为单一流程：打开看板→钉住→拖动验证→取消钉住→点击桌面空白处→验证看板DOM消失。

### 64. Qoder BYOK前端可用性绕过决策
- **类别**: important_decision_experience
- **关键词**: Qoder,BYOK,前端绕过,Gq函数,feature flag
- **内容**: 采用直接修改Qoder主JS文件中的Gq函数强制返回true方案。

---

## 十二、专家经验记忆

### 65. TOS桌面模块测试点（含实际界面观察）
- **类别**: expert_experience
- **关键词**: TOS桌面,登录,窗口,搜索,通知,任务中心,权限,会话
- **内容**: 详细的TOS桌面测试关注点，包括登录页面布局、桌面三区域布局（导航栏、桌面图标、右侧栏）、桌面通知、右键菜单、导航栏交互规则、典型测试点等。

### 66. TOS用户设置界面结构与交互规则
- **类别**: expert_experience
- **关键词**: 用户设置,账号,显示,密码,壁纸,语言,OTP,强调色,未保存提示
- **内容**: 完整的用户设置界面结构（账号/显示模块）、交互行为规则（未保存提示弹窗、修改密码弹窗、语言切换提示）。

### 67. TOS桌面通知与桌面图标交互补充
- **类别**: expert_experience
- **关键词**: 桌面通知,消息卡片,删除通知,自动排序,拖动,开始,右键限制
- **内容**: 桌面通知支持下拉查看详情、删除单个、一键删除全部；桌面图标默认自动排序、可拖动；导航栏「开始」没有右键功能。

### 68. TNAS/TOS测试回答原则与关联模块处理
- **类别**: expert_experience
- **关键词**: 回答原则,关联模块,测试深度,展开条件,用例格式
- **内容**: 优先判断问题所属模块、关联模块展开条件（任务中心、通知日志、权限安全等）、测试用例使用8字段格式。

### 69. TOS桌面右侧栏搜索界面功能详情
- **类别**: expert_experience
- **关键词**: 搜索,右侧栏搜索,拖动,查看更多,全局搜索,双击结果
- **内容**: 搜索框可拖动、输入返回结果、双击进入对应内容、查看更多跳转全局搜索、与开始菜单搜索的关系。

### 70. TOS桌面右侧栏消息通知界面功能详情
- **类别**: expert_experience
- **关键词**: 消息通知,右侧栏,删除消息,清空通知,查看详情,设置,通用设置
- **内容**: 消息列表/空状态、设置入口跳转控制面板、查看详情不重复打开窗口、删除单条、清空全部。

---

## 十三、学到的技能记忆

### 71. SPA页面局部滚动容器操作与DOM元素全量检测技能
- **类别**: learned_skill_experience
- **关键词**: SPA,局部滚动,scrollTop,DOM全量检测,is_displayed
- **内容**: 定位滚动容器→execute_script操作scrollTop→find_elements+textContent替代is_displayed()。

### 72. Vue/React自定义拖动模拟技能
- **类别**: learned_skill_experience
- **关键词**: Vue拖动,Selenium,click_and_hold,自定义拖拽
- **内容**: click_and_hold→pause(1)→move_by_offset分步慢移→release()，禁用原生HTML5拖放时必须用此组合。

### 73. 看板模块勾选状态与卡片可见性联动验证技能
- **类别**: learned_skill_experience
- **关键词**: 看板测试,状态联动,逐级断言,模块勾选
- **内容**: 逐个取消勾选→每步获取可见卡片名→断言数量和内容→时间模块固定排除。

### 74. Context7 MCP文档检索技能
- **类别**: learned_skill_experience
- **关键词**: Context7,MCP,文档检索,pytest,API文档
- **内容**: initialize获取Session-Id→resolve-library-id选最高benchmark→query-docs获取文档。

### 75. Vue单页应用表单双向验证操作技能
- **类别**: learned_skill_experience
- **关键词**: Vue,clear失效,双向验证,ActionChains
- **内容**: ActionChains执行Command+A/Ctrl+A全选→Backspace→send_keys；复选框全部取消→应用→全部勾选→应用。

### 76. 测试框架混合代码库安全清理技能
- **类别**: learned_skill_experience
- **关键词**: 代码清理,pytest --collect-only,__init__.py,测试框架治理
- **内容**: 扫描区分项目代码与模板代码→分析__init__.py依赖→分阶段清理→pytest --collect-only验证。

### 77. 多模块测试项目目录结构设计技能
- **类别**: learned_skill_experience
- **关键词**: 目录结构,模块自治,日志隔离,测试报告
- **内容**: 识别模块→建立自包含子目录（logs/reports）→提取共享代码到common/→根目录保持简洁。

### 78. 多模块测试项目目录重构收尾验证技能
- **类别**: learned_skill_experience
- **关键词**: 目录清理,pytest collect验证,find树状结构
- **内容**: ls扫描→分组清理→ls/pytest --collect-only/find验证。

### 79. Git项目提交与同步操作指南生成技能
- **类别**: learned_skill_experience
- **关键词**: Git指南,VS Code提交,gitignore配置,提交同步
- **内容**: git status→编辑.gitignore→git add+reset→commit→push（HTTP/2报错时降级）→VS Code操作指引。

### 80. Bash强制覆盖文件技能
- **类别**: learned_skill_experience
- **关键词**: cat重定向,强制覆盖,文件污染修复,EOF
- **内容**: `cat > 文件路径 << 'EOF'`写入完整内容→wc -l验证→必须用单引号EOF。

### 81. Python conftest.py 文件末尾污染清洗技能
- **类别**: learned_skill_experience
- **关键词**: conftest.py,文件污染,pytest,清洗
- **内容**: 定位孤立"""→删除到文件末尾→pytest --collect-only验证。

### 82. Python多模块测试项目配置目录重构技能
- **类别**: learned_skill_experience
- **关键词**: 多模块测试,配置重构,sys.path优先级,pytest路径配置
- **内容**: 识别依赖→创建模块专属config→sys.path.insert优先加载→更新pytest.ini→验证导入链路。

### 83. SPA桌面应用自动化测试框架补全技能
- **类别**: learned_skill_experience
- **关键词**: SPA测试,显式等待,UI组件复用,Fixture分层,失败恢复
- **内容**: 5个基础设施层：等待层、操作层、组件层、Fixture层、恢复层。

### 84. 多项目工具分层治理技能
- **类别**: learned_skill_experience
- **关键词**: 工具治理,跨项目复用,目录隔离,common目录
- **内容**: 跨项目工具独立存放、项目内公共工具在common/、模块私有工具在模块内。

### 85. 多模块测试项目配置分层治理技能
- **类别**: learned_skill_experience
- **关键词**: 配置分层,环境配置,模块专属配置,测试架构
- **内容**: 环境变化值→environments/*.yaml；模块固有属性→模块config/；移除无关配置。

### 86. 多模块测试项目目录结构设计技能（解耦配置版）
- **类别**: learned_skill_experience
- **关键词**: 多模块测试,配置解耦,sys.path,pytest,模块隔离
- **内容**: 与技能77类似但增加配置解耦：移除根目录config/→每个模块独立config→sys.path.insert优先加载。

### 87. OpenAI兼容代理后端切换技能
- **类别**: learned_skill_experience
- **关键词**: 代理切换,后端迁移,OpenAI兼容,API Key
- **内容**: 修改代理配置→更新模型映射→修改代理代码→编译检查→重启验证。

### 88. Qoder前端BYOK可用性补丁技能
- **类别**: learned_skill_experience
- **关键词**: Qoder,JS补丁,Gq函数,CachedData,前端绕过
- **内容**: 退出Qoder→备份JS→定位Gq函数→替换为return!0→清理CachedData→重启验证。

### 89. Qoder自定义模型baseUrl数据库配置技能
- **类别**: learned_skill_experience
- **关键词**: Qoder,baseUrl,数据库配置,代理链路
- **内容**: sqlite3查询state.vscdb→解析aicoding.customModels→更新baseUrl→重启生效。

### 90. 反向代理绕过模型验证失败技能
- **类别**: learned_skill_experience
- **关键词**: 模型验证,代理拦截,OpenAI兼容,1004错误
- **内容**: GET /v1/models构造模型列表、POST验证消息返回模拟成功、1004错误拦截替换响应。

### 91. Git安全提交流程技能
- **类别**: learned_skill_experience
- **关键词**: git commit,暂存区过滤,git reset,提交验证
- **内容**: git add→检查status→reset排除项→commit→log验证。

### 92. TOS桌面右侧栏界面点击空白处收起技能
- **类别**: learned_skill_experience
- **关键词**: 右侧栏,点击空白收起,TOS桌面,UI交互
- **内容**: 点击桌面任意空白区域收起已展开的右侧栏界面（帮助图标除外）。

### 93. TOS桌面右侧栏功能文档结构化补全技能
- **类别**: learned_skill_experience
- **关键词**: 右侧栏,功能文档,结构化,五项表格
- **内容**: 统一五项结构化表格：触发、可拖动、输入搜索、打开结果、查看更多。

### 94. TOS桌面功能文档精准表述技能
- **类别**: learned_skill_experience
- **关键词**: 功能文档,精准表述,TOS桌面,UI术语,交付顺序
- **内容**: 5点精准表述：桌面图标区域、第三方应用右键菜单、勾选框术语、未保存提示触发场景、文档交付顺序。

### 95. 跨平台开发工作区同步构建技能
- **类别**: learned_skill_experience
- **关键词**: 跨平台,venv重建,.gitignore,开发环境迁移
- **内容**: 审查.gitignore→仅排除venv/__pycache__/二进制→venv本地重建→提供PowerShell/bash对照指南。

---

## 补充：导出后新增的记忆（7条）

### 96. 开发者平台模块测试点
- **类别**: expert_experience
- **关键词**: 开发者平台,应用包,API,SDK,鉴权,沙箱,第三方应用,权限
- **使用场景**: 为开发者平台生成测试用例时参考,分析开发者平台与其他模块的关联影响,开发者平台正式上线后补充测试点
- **内容**: 开发者平台测试关注点（副测，未正式上线）。可能涉及子模块：开发者入口、开发者模式/平台开关、账号/角色/权限、应用包/插件包、上传/安装/升级/卸载/回滚、应用发布/审核/下架、API/SDK、接口鉴权、日志审计、沙箱和安全边界、第三方应用访问存储数据、桌面入口/应用中心入口。典型测试点：开发者入口位置、普通用户是否能看到、开发者模式开关状态、账号类型、应用包格式签名版本依赖、上传安装升级失败提示、应用卸载后清理、第三方应用访问数据权限、API鉴权权限范围、发布审核下架灰度回滚流程、异常日志追踪。当前状态：未正式上线。

### 97. TOS导航栏与桌面应用右键菜单规则
- **类别**: expert_experience
- **关键词**: 右键菜单,导航栏,桌面图标,打开,关闭,发送到桌面,固定到导航栏,卸载,权限,置灰
- **使用场景**: 测试导航栏和桌面图标右键菜单功能,验证右键菜单项状态是否正确,验证打开/关闭状态与菜单文字是否对应,测试第三方应用的卸载和权限功能
- **内容**: 应用分为常规应用（文件管理、控制面板、存储管理等系统内置）和第三方/多用户应用（Docker、OpenClaw等）。导航栏右键菜单：常规应用3项（打开/关闭、发送到桌面、从导航条移除）；第三方应用5项（+卸载、权限）。桌面图标右键菜单：常规应用3项（打开/关闭、固定到导航栏、删除快捷方式）；第三方应用5项（+卸载、权限）。置灰规则：导航栏"发送到桌面"在桌面已有快捷方式时置灰；桌面"固定到导航栏"在导航栏已有该应用时置灰。

### 98. TOS导航栏应用名称映射决策-通用设置=控制面板
- **类别**: important_decision_experience
- **关键词**: TOS,导航栏,控制面板,通用设置,名称映射
- **内容**: "通用设置"在导航栏中实际显示为"控制面板"（齿轮图标），所有自动化测试中应以UI可见文字"控制面板"为准进行识别和点击。适用范围：TOS UI自动化测试中涉及导航栏图标识别、tooltip匹配、应用启动等场景。

### 99. Qoder第三方模型配置文件定位技能
- **类别**: learned_skill_experience
- **关键词**: Qoder,配置文件,settings.json,第三方模型
- **内容**: Qoder第三方模型配置（API密钥、提供商、模型名等）持久化存储在 `~/.qoder/settings.json` 文件中。定位步骤：1. `find ~/.qoder -name "*.json" -type f` 查找JSON配置文件；2. 筛选含model/provider/api字段的文件；3. 优先检查 `~/.qoder/settings.json`。若该文件无model/provider字段，说明尚未添加任何第三方模型。

### 100. 跨平台智能体记忆与知识库迁移技能
- **类别**: learned_skill_experience
- **关键词**: 跨平台迁移,记忆导出,知识库同步,Qoder
- **内容**: 跨平台迁移步骤：1.识别平台敏感数据（二进制.zap/.bolt不可跨平台）；2.提取结构化内容（topic_tree、network JSON、repowiki markdown）；3.生成标准化记忆描述文档（memories_export.md）和恢复提示词（restore_prompt.md）；4.创建自动化打包脚本和环境差异对照表；5.验证完整性。恢复时需分段发送提示词避免单次输入过长。

### 101. 测试用例生成协作模式与记忆策略
- **类别**: learned_skill_experience
- **关键词**: 测试用例生成,协作模式,记忆策略,用例格式,持续优化
- **使用场景**: 用户请求生成测试用例时确定协作方式,用户提供产品需求或测试点时记录产品知识,生成用例时参考用户偏好的风格和格式
- **内容**: 5种生成场景（需求+测试点直接生成、仅需求提炼测试点、现有用例理解风格后补充、需求+用例结合、对话快速生成）。对话输出表格形式每行都写模块名，导出Excel时再合并。用例字段规范8字段。记忆积累策略：产品知识累积、风格自适应、覆盖度提升、纠错学习。Python testcase_generator仅作为文件导出工具，用例智能生成由Qoder记忆驱动。

### 102. Qoder跨平台记忆迁移打包规范
- **类别**: project_environment_configuration
- **关键词**: Qoder,跨平台迁移,记忆导出,恢复提示词,JSON备份
- **内容**: 为实现Mac到Windows跨平台工作区迁移，需打包：1. 项目内知识库路径`.qoder/repowiki/`（markdown文档）；2. Qoder应用数据中可移植的JSON记忆文件（`memory_topic_tree/*.json`和`memory_network/*.json`）；3. 必须配套生成'恢复提示词'文档，用于在Windows端通过Qoder对话批量重建记忆。
