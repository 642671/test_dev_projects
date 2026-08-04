#!/usr/bin/env python3
"""
将 TOS API 清单 (JSON) 转换为 OpenAPI 3.0 规范文件

使用方法:
    python generate_openapi.py

输出:
    api_testing/docs/api_investigation/tos_openapi.yaml
"""

import json
import yaml
from pathlib import Path
from collections import defaultdict


def load_api_inventory(json_path: str) -> dict:
    """加载 TOS API 清单 JSON 文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def categorize_endpoints(endpoints: list) -> dict:
    """按 Tag 对接口进行分类"""
    categories = defaultdict(list)
    for ep in endpoints:
        tag = ep.get('tags', '').strip() or '未分类'
        categories[tag].append(ep)
    return dict(categories)


def generate_operation_id(method: str, path: str) -> str:
    """从 HTTP 方法和路径生成 operationId"""
    # 移除路径参数和特殊字符
    clean_path = path.replace('{', '').replace('}', '').replace('/', '_').strip('_')
    # 转换为 snake_case
    operation_id = f"{method.lower()}_{clean_path}"
    return operation_id


def extract_path_parameters(path: str) -> list:
    """从路径中提取路径参数"""
    import re
    params = re.findall(r'\{(\w+)\}', path)
    return [
        {
            "name": param,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
            "description": f"路径参数: {param}"
        }
        for param in params
    ]


def build_paths(endpoints: list) -> dict:
    """构建 OpenAPI paths 对象"""
    paths = defaultdict(dict)
    
    for ep in endpoints:
        path = ep['path']
        method = ep['method'].lower()
        
        operation = {
            "summary": ep.get('summary', ''),
            "description": ep.get('description', ''),
            "operationId": generate_operation_id(method, path),
            "tags": [ep.get('tags', '未分类').strip()] if ep.get('tags', '').strip() else ["未分类"],
            "responses": {
                "200": {
                    "description": "成功响应"
                },
                "400": {
                    "description": "请求参数错误"
                },
                "401": {
                    "description": "未认证"
                },
                "403": {
                    "description": "权限不足"
                },
                "500": {
                    "description": "服务器内部错误"
                }
            }
        }
        
        # 添加路径参数
        path_params = extract_path_parameters(path)
        if path_params:
            operation["parameters"] = path_params
        
        # 为 POST/PUT 请求添加请求体占位符
        if method in ['post', 'put', 'patch']:
            operation["requestBody"] = {
                "description": "请求体",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "description": "根据具体接口定义请求体结构"
                        }
                    }
                }
            }
        
        paths[path][method] = operation
    
    return dict(paths)


def generate_openapi_spec(inventory: dict) -> dict:
    """生成完整的 OpenAPI 3.0 规范"""
    endpoints = inventory.get('endpoints', [])
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "TOS 系统默认模块 API",
            "description": """TOS (Truenas Open Storage) 系统默认模块的完整 API 接口规范。

本规范基于 API 调查报告自动生成，包含 199 个接口的定义。

## 认证方式
大多数接口需要有效的 `TMSESSNAME` Cookie 进行认证。

## 版本信息
- API 版本: v2 (主要)
- 向后兼容: v1 (部分内部接口)
- OpenAPI 规范版本: 3.0.3

## 功能模块
- 用户认证与会话
- 桌面管理
- 消息通知
- OTP 双因素认证
- 存储管理 (核心功能)
- 磁盘管理
- RAID 管理
- 虚拟磁盘 (iSCSI)
- USB 设备管理
- SSD 缓存
- 热备盘管理
""",
            "version": "1.0.0",
            "contact": {
                "name": "TOS API 研究团队"
            }
        },
        "servers": [
            {
                "url": "http://192.168.64.8:8181",
                "description": "TOS 开发环境"
            },
            {
                "url": "http://192.168.64.7:8181",
                "description": "TOS 正式环境"
            }
        ],
        "paths": build_paths(endpoints),
        "components": {
            "securitySchemes": {
                "CookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "TMSESSNAME",
                    "description": "TOS 会话认证 Cookie"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "integer",
                            "description": "错误码"
                        },
                        "message": {
                            "type": "string",
                            "description": "错误信息"
                        }
                    }
                }
            }
        },
        "security": [
            {"CookieAuth": []}
        ],
        "tags": []
    }
    
    # 生成 Tags 列表
    categories = categorize_endpoints(endpoints)
    for tag_name in sorted(categories.keys()):
        spec["tags"].append({
            "name": tag_name,
            "description": f"{tag_name}相关接口"
        })
    
    return spec


def main():
    """主函数"""
    # 文件路径
    base_dir = Path(__file__).parent
    json_path = base_dir / "api_testing" / "docs" / "api_investigation" / "tos_api_inventory.json"
    output_path = base_dir / "api_testing" / "docs" / "api_investigation" / "tos_openapi.yaml"
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 加载 API 清单
    print(f"📖 加载 API 清单: {json_path}")
    inventory = load_api_inventory(str(json_path))
    print(f"✅ 成功加载 {inventory['total_apis']} 个接口")
    
    # 生成 OpenAPI 规范
    print("🔧 生成 OpenAPI 3.0 规范...")
    spec = generate_openapi_spec(inventory)
    
    # 写入 YAML 文件
    print(f"💾 保存到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            spec,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120
        )
    
    # 统计信息
    categories = categorize_endpoints(inventory['endpoints'])
    print("\n📊 接口分类统计:")
    for tag, eps in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  - {tag}: {len(eps)} 个接口")
    
    print(f"\n✅ OpenAPI 规范生成完成！")
    print(f"📁 文件位置: {output_path}")
    print(f"🔢 总计接口: {inventory['total_apis']} 个")
    print(f"📝 分类数量: {len(categories)} 个")
    
    # 提供后续使用指南
    print("\n" + "="*60)
    print("📚 后续使用指南:")
    print("="*60)
    print("1. 在 Postman 中导入:")
    print("   - 打开 Postman → Import → 选择 tos_openapi.yaml")
    print("   - 或使用 Postman MCP: /postman:sync")
    print("\n2. 生成客户端代码:")
    print("   - 使用 openapi-generator 生成 Python/TypeScript 客户端")
    print("   - 或使用 Postman MCP: /postman:codegen")
    print("\n3. 生成 API 文档:")
    print("   - 使用 Redoc: redoc-cli serve tos_openapi.yaml")
    print("   - 使用 Swagger UI: swagger-ui-dist")
    print("\n4. 运行安全审计:")
    print("   - 使用 Postman MCP: /postman:security")


if __name__ == "__main__":
    main()
