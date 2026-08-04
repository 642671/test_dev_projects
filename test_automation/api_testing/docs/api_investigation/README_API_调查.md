# TOS 系统默认模块 API 完整接口调查报告

## 调查成果概览

本调查已经完成对 TOS 系统默认模块的 API 接口的全面梳理，生成了以下交付物：

### 生成文件清单

| 文件名 | 格式 | 用途 | 大小 |
|------|------|------|------|
| `TOS_API_调查报告.txt` | 纯文本 | 详细调查报告，包含分析和建议 | 23K |
| `tos_api_inventory.json` | JSON | 结构化数据，便于程序处理 | 49K |
| `tos_api_inventory.csv` | CSV | 表格格式，便于 Excel 导入 | 26K |
| `tos_api_inventory.html` | HTML | 网页浏览，美化显示 | 83K |
| `tos_api_inventory.txt` | 纯文本 | 按功能分类的完整清单 | 30K |

## 快速数据

- **总接口数**: 199 个
- **HTTP 方法分布**:
  - GET: 85 个 (42.7%)
  - POST: 87 个 (43.7%)
  - PUT: 18 个 (9.0%)
  - DELETE: 9 个 (4.5%)

- **功能分类**: 8 个
  - 其他模块 (登录、桌面、消息等): 186 个
  - 提示管理: 2 个
  - 桌面总览: 2 个
  - 欢迎页: 2 个
  - 用户协议: 2 个
  - 系统信息: 1 个
  - 系统提示: 2 个
  - 调试模式: 2 个

## 核心发现

### 1. API 规范性
- ✓ 所有接口都有清晰的命名和文档
- ✓ 遵循 OpenAPI 3.0.1 标准
- ✓ 使用 /v2/ 版本前缀（部分 /v1/ 向后兼容接口）
- ✓ 支持 Tag 分类便于组织

### 2. 功能模块
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

### 3. 服务器探测结果

对 http://192.168.64.8:8181 的探测结果：

| 端点 | 状态码 | 说明 |
|-----|--------|------|
| /v2/login/state | 403 | 需要认证 ✓ |
| /v2/welcome | 403 | 需要认证 ✓ |
| /v2/desktop/eula | 403 | 需要认证 ✓ |
| 其他测试端点 | 404 | 接口不存在/模块未加载 |

**结论**: 服务器在线，认证机制有效，部分接口可能需要特殊配置。

## 关键接口示例

### 登录相关
```
POST /v2/login                          用户登录
GET  /v2/login/state                    获取登录状态
```

### 欢迎页和配置
```
GET  /v2/welcome                        获取登录欢迎页配置
GET  /v2/welcome/advancedSetting        获取用户高级设置
GET  /v2/desktop/eula                   获取用户协议
PUT  /v2/desktop/eula                   同意用户协议
```

### 桌面管理
```
GET  /v2/desktop/init                   初始化桌面配置
GET  /v2/desktop/list                   获取导航栏列表
GET  /v2/desktop/listDesktop            获取桌面应用列表
POST /v2/desktop/showState              设置应用显示状态
GET  /v2/desktop/recentlyVisited        获取最近访问列表
```

### 存储管理 (核心模块)
```
GET  /v2/storage/overview               获取磁盘分配总览
GET  /v2/storage/list/volume            获取卷或存储池列表
POST /v2/storage/create/volume          创建卷或存储池
DELETE /v2/storage/delete/{role}/{uuid} 删除卷或存储池
GET  /v2/disk/GetDiskListData           获取硬盘列表数据
POST /v2/disk/format/start              开始抹除磁盘
```

### OTP 双因素认证
```
GET  /otp/info                          获取OTP配置信息
GET  /otp/qrbind                        获取OTP绑定二维码
POST /otp/checkcode                     验证OTP验证码
POST /otp/bind_email                    绑定邮箱地址
```

## 使用指南

### 查看详细清单
1. **使用 HTML 文件** (推荐浏览)
   ```bash
   open tos_api_inventory.html
   ```

2. **使用纯文本文件** (快速查阅)
   ```bash
   cat tos_api_inventory.txt
   ```

3. **使用 CSV 文件** (Excel 打开)
   - 双击 `tos_api_inventory.csv` 在 Excel 中打开
   - 可按 HTTP 方法、路径、分类等列进行排序和过滤

4. **使用 JSON 文件** (程序处理)
   ```python
   import json
   with open('tos_api_inventory.json') as f:
       data = json.load(f)
   print(f"总接口数: {data['total_apis']}")
   ```

### 生成测试用例

基于此清单，可以使用 `test_case_generator` 为每个接口生成对应的测试用例：

```python
# 示例: 基于接口清单生成测试用例
from testcase_generator import TestCaseGenerator

generator = TestCaseGenerator()
# 按 Tag 分类生成
generator.generate_from_openapi('/Users/miaoqi/Downloads/默认模块.openapi.json')
```

### 接口测试

使用认证 Cookie 进行测试：

```bash
# 获取登录状态
curl -s -b "TMSESSNAME=<your_session>" \
  http://192.168.64.8:8181/v2/login/state

# 获取欢迎页配置
curl -s -b "TMSESSNAME=<your_session>" \
  http://192.168.64.8:8181/v2/welcome
```

## 重要发现

1. **认证要求**
   - 大多数接口需要有效的 `TMSESSNAME` Cookie
   - 敏感操作（删除、格式化等）需要密码验证
   - 某些内部接口 (/v1/) 可能无需认证

2. **模块加载**
   - OpenAPI 规范定义了所有接口
   - 192.168.64.8:8181 可能未加载全部模块
   - 建议在正式环境验证接口可用性

3. **API 设计**
   - 遵循 RESTful 原则
   - 使用 Tag 进行逻辑分组
   - 提供详细的接口描述

## 后续建议

1. **测试用例生成**
   - 为每个接口生成对应的测试用例
   - 按 Tag 分类创建功能测试套件
   - 重点关注存储管理模块

2. **接口文档完善**
   - 补充请求/响应示例
   - 记录错误码和异常场景
   - 标记需要密码验证的接口

3. **环境验证**
   - 在正式的 TOS 环境 (192.168.64.7:8181) 进行验证
   - 确认 API 基础路径
   - 测试认证和授权机制

4. **集成测试**
   - 基于此清单设计集成测试流程
   - 考虑接口间的依赖关系
   - 准备充分的测试数据

## 技术细节

### 数据来源
- **主要数据源**: `/Users/miaoqi/Downloads/默认模块.openapi.json`
- **OpenAPI 版本**: 3.0.1
- **API 版本**: 主要使用 /v2/ 前缀

### 调查方法
1. 解析 OpenAPI 规范文件
2. 提取所有路径、方法、标签和描述
3. 按功能分类组织接口
4. 对关键端点进行 HTTP 探测验证
5. 生成多种格式的清单报告

### 文件路径
- OpenAPI 规范: `/Users/miaoqi/Downloads/默认模块.openapi.json`
- Apifox 数据: `/Users/miaoqi/Library/Application Support/apifox/`
- 调查报告: `/Users/miaoqi/Desktop/test_dev_projects/`

---

**调查完成时间**: 2026-06-01
**生成工具**: Python 3 + OpenAPI 解析
**联系人**: 研究员
