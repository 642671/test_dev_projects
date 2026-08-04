# Postman 插件能力总结与 TOS API OpenAPI 规范生成

## 📦 Postman 插件完整能力

### 核心组件

#### 1. 8 个 Commands（命令）

| 命令 | 功能描述 | 使用场景 |
|------|---------|---------|
| `/postman:setup` | 首次配置：验证 API Key、选择工作区 | 初次使用 Postman 插件时 |
| `/postman:search` | API 发现：通过自然语言搜索工作区中的 API | 查找特定功能的 API 接口 |
| `/postman:codegen` | 代码生成：从 Postman 集合生成类型化客户端代码 | 为前端/后端生成 API 客户端 |
| `/postman:docs` | 文档改进：分析、补充和生成 API 文档 | 完善 API 文档覆盖度 |
| `/postman:test` | 测试执行：运行集合测试、诊断失败、建议修复 | 自动化 API 测试 |
| `/postman:security` | 安全审计：对照 OWASP API Top 10 进行安全审查 | API 安全评估 |
| `/postman:mock` | Mock 服务：创建 Mock 服务器供前端开发使用 | 前后端并行开发 |
| `/postman:sync` | 同步管理：从 OpenAPI 规范创建/更新集合 | API 规范与 Postman 同步 |

#### 2. 3 个 Skills（技能，后台自动加载）

- **postman-knowledge**: Postman 概念和 MCP 工具选择指导
- **postman-routing**: 自动路由 API/Postman 请求到正确的命令
- **agent-ready-apis**: API 对 AI Agent 就绪度的知识库

#### 3. 1 个 MCP Server

- **端点**: `https://mcp.postman.com/mcp`
- **认证**: 通过 `POSTMAN_API_KEY` 环境变量
- **工具**: 提供 30+ MCP 工具（搜索、读取、创建、更新、同步等）

#### 4. 1 个子 Agent

- **API Readiness Analyzer**: 分析 API 对 AI Agent 的就绪程度（48 项检查，8 个维度）

#### 5. 1 个规则文件

- **postman-best-practices.md**: API 设计最佳实践

---

## 🎯 本次执行的任务

### 任务目标
将已有的 TOS API 调查数据（199 个接口）转换为标准 OpenAPI 3.0 规范文件，为后续使用 Postman 插件奠定基础。

### 执行步骤

#### 第一步：探索现有 API 数据
- ✅ 发现 `api_testing/docs/api_investigation/tos_api_inventory.json` 包含 199 个接口
- ✅ 确认数据包含：路径、方法、摘要、描述、标签等信息

#### 第二步：生成转换脚本
- ✅ 创建 `generate_openapi.js`（Node.js 脚本，无需外部依赖）
- ✅ 实现功能：
  - JSON 数据解析
  - OpenAPI 3.0 规范构建
  - 路径参数提取
  - 操作 ID 生成
  - YAML 格式输出

#### 第三步：生成 OpenAPI 规范
- ✅ 成功生成 `tos_openapi.yaml`（4683 行）
- ✅ 包含完整信息：
  - API 元数据（标题、版本、描述）
  - 服务器配置（开发/正式环境）
  - 199 个接口定义
  - 安全方案（Cookie 认证）
  - 8 个功能分类标签

### 生成文件清单

| 文件 | 大小 | 用途 |
|------|------|------|
| `generate_openapi.js` | 转换脚本 | 将 JSON 清单转换为 OpenAPI 规范 |
| `generate_openapi.py` | 转换脚本（Python 版） | 备选方案（需要 PyYAML 库） |
| `tos_openapi.yaml` | 4683 行 | 标准 OpenAPI 3.0 规范文件 |

### 接口分类统计

| 分类 | 接口数量 | 占比 |
|------|---------|------|
| 未分类 | 186 | 93.5% |
| 调试模式 | 2 | 1.0% |
| 用户协议 | 2 | 1.0% |
| 提示管理 | 2 | 1.0% |
| 桌面总览 | 2 | 1.0% |
| 系统提示 | 2 | 1.0% |
| 欢迎页 | 2 | 1.0% |
| 系统信息 | 1 | 0.5% |

---

## 📚 后续使用指南

### 1. 配置 Postman MCP（可选）

如果你希望使用 Postman 插件的全部功能：

```bash
# 第一步：获取 Postman API Key
# 访问 https://app.postman.com/settings/me/api-keys 创建 API Key

# 第二步：设置环境变量（Windows PowerShell）
$env:POSTMAN_API_KEY="your_api_key_here"

# 第三步：重启 Qoder

# 第四步：验证配置
# 运行 /postman:setup 命令
```

### 2. 导入到 Postman

**方法 A：手动导入**
1. 打开 Postman 应用
2. 点击 "Import" 按钮
3. 选择 `tos_openapi.yaml` 文件
4. 确认导入

**方法 B：使用 Postman MCP（配置后）**
```
/postman:sync
# 选择 tos_openapi.yaml 文件
# 自动创建 Postman 集合
```

### 3. 生成客户端代码

**使用 openapi-generator:**
```bash
# 生成 Python 客户端
openapi-generator generate -i tos_openapi.yaml -g python -o ./tos-client-python

# 生成 TypeScript 客户端
openapi-generator generate -i tos_openapi.yaml -g typescript-axios -o ./tos-client-ts
```

**使用 Postman MCP（配置后）:**
```
/postman:codegen
# 自动检测项目语言
# 生成符合项目规范的客户端代码
```

### 4. 生成 API 文档

**使用 Redoc:**
```bash
# 安装
npm install -g redoc-cli

# 启动文档服务器
redoc-cli serve tos_openapi.yaml

# 访问 http://localhost:8080
```

**使用 Swagger UI:**
```bash
# 使用 Docker
docker run -p 8080:8080 -e SWAGGER_JSON=/tos_openapi.yaml -v $(pwd):/tos_openapi.yaml swaggerapi/swagger-ui
```

### 5. 运行安全审计

**使用 Postman MCP（配置后）:**
```
/postman:security
# 自动对照 OWASP API Top 10 进行审计
# 生成安全报告并提供修复建议
```

### 6. 创建 Mock 服务

**使用 Postman MCP（配置后）:**
```
/postman:mock
# 创建 Mock 服务器
# 获取 Mock URL 供前端开发使用
```

---

## 🔍 OpenAPI 规范文件结构

```yaml
tos_openapi.yaml
├── openapi: 3.0.3                    # OpenAPI 版本
├── info:                             # API 元数据
│   ├── title: TOS 系统默认模块 API
│   ├── description: ...              # 详细说明
│   ├── version: 1.0.0
│   └── contact: ...
├── servers:                          # 服务器配置
│   ├── 开发环境: 192.168.64.8:8181
│   └── 正式环境: 192.168.64.7:8181
├── paths:                            # 199 个接口定义
│   ├── /app/config/language:
│   │   └── get: ...
│   ├── /v2/login:
│   │   └── post: ...
│   └── ...
├── components:                       # 可复用组件
│   ├── securitySchemes:
│   │   └── CookieAuth: ...           # Cookie 认证方案
│   └── schemas:
│       └── Error: ...                # 错误响应 schema
├── security:                         # 全局安全要求
│   └── CookieAuth: []
└── tags:                             # 8 个功能分类
    ├── 未分类
    ├── 调试模式
    ├── 用户协议
    └── ...
```

---

## 💡 关键发现

### 1. API 规范性
- ✅ 所有接口都有清晰的命名和文档
- ✅ 遵循 OpenAPI 3.0.1 标准
- ✅ 使用 /v2/ 版本前缀（部分 /v1/ 向后兼容接口）
- ✅ 支持 Tag 分类便于组织

### 2. 认证机制
- 大多数接口需要 `TMSESSNAME` Cookie
- 敏感操作（删除、格式化等）需要密码验证
- 某些内部接口 (/v1/) 可能无需认证

### 3. 功能模块
**主要功能模块**:
- 用户认证与会话 (登录、会话状态)
- 桌面管理 (桌面初始化、应用管理、最近访问)
- 消息通知 (消息增删改查、订阅管理)
- OTP 双因素认证 (9 个接口)
- 存储管理 (100+ 接口，核心功能):
  - 存储池和卷管理
  - 磁盘管理
  - RAID 管理
  - 虚拟磁盘 (iSCSI)
  - USB 设备管理
  - SSD 缓存 (Hyper Cache)
  - 热备盘管理

---

## 🚀 下一步建议

1. **完善 Tag 分类**: 当前 93.5% 的接口标记为"未分类"，建议按功能模块重新分类
2. **补充请求/响应 Schema**: 为每个接口定义具体的请求体和响应体结构
3. **添加示例数据**: 为关键接口添加请求/响应示例
4. **配置 Postman MCP**: 设置 API Key 以启用完整的 Postman 插件功能
5. **生成测试用例**: 基于 OpenAPI 规范自动化生成 API 测试用例

---

## 📝 技术细节

### 数据来源
- **主要数据源**: `tos_api_inventory.json`
- **OpenAPI 版本**: 3.0.3
- **API 版本**: 主要使用 /v2/ 前缀

### 生成方法
1. 解析 JSON 格式的 API 清单
2. 提取所有路径、方法、标签和描述
3. 生成 OpenAPI 3.0 规范结构
4. 输出 YAML 格式文件

### 工具链
- Node.js（无需外部依赖）
- 自定义 YAML 序列化器
- 路径参数自动提取
- 操作 ID 自动生成

---

**生成时间**: 2026-06-22  
**生成工具**: Node.js + 自定义脚本  
**总计接口**: 199 个  
**分类数量**: 8 个
