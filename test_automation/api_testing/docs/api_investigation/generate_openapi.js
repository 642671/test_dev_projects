#!/usr/bin/env node
/**
 * 将 TOS API 清单 (JSON) 转换为 OpenAPI 3.0 规范文件 (YAML)
 * 
 * 使用方法:
 *   node generate_openapi.js
 * 
 * 输出:
 *   api_testing/docs/api_investigation/tos_openapi.yaml
 */

const fs = require('fs');
const path = require('path');

// 简单的 YAML 序列化（避免依赖外部库）
function toYAML(obj, indent = 0) {
  const spaces = '  '.repeat(indent);
  let yaml = '';

  if (Array.isArray(obj)) {
    for (const item of obj) {
      if (typeof item === 'object' && item !== null) {
        yaml += `${spaces}- ${toYAML(item, indent + 1).trimStart()}`;
      } else {
        yaml += `${spaces}- ${formatValue(item)}\n`;
      }
    }
  } else if (typeof obj === 'object' && obj !== null) {
    const entries = Object.entries(obj);
    for (let i = 0; i < entries.length; i++) {
      const [key, value] = entries[i];
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        yaml += `${spaces}${key}:\n${toYAML(value, indent + 1)}`;
      } else if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n${toYAML(value, indent + 1)}`;
      } else {
        yaml += `${spaces}${key}: ${formatValue(value)}\n`;
      }
    }
  }

  return yaml;
}

function formatValue(value) {
  if (value === null || value === undefined) {
    return 'null';
  }
  if (typeof value === 'string') {
    // 检查是否需要引号
    if (value.includes(':') || value.includes('#') || value.includes('\n') || 
        value.includes('{') || value.includes('}') || value.includes('[') || 
        value.includes(']') || value.includes(',') || value.includes("'") ||
        value.startsWith('http')) {
      return `"${value.replace(/"/g, '\\"')}"`;
    }
    return value;
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }
  return String(value);
}

function loadApiInventory(jsonPath) {
  const data = fs.readFileSync(jsonPath, 'utf-8');
  return JSON.parse(data);
}

function categorizeEndpoints(endpoints) {
  const categories = {};
  for (const ep of endpoints) {
    const tag = ep.tags?.trim() || '未分类';
    if (!categories[tag]) {
      categories[tag] = [];
    }
    categories[tag].push(ep);
  }
  return categories;
}

function generateOperationId(method, path) {
  const cleanPath = path.replace(/{/g, '').replace(/}/g, '').replace(/\//g, '_').replace(/^_/, '');
  return `${method.toLowerCase()}_${cleanPath}`;
}

function extractPathParameters(pathStr) {
  const regex = /\{(\w+)\}/g;
  const params = [];
  let match;
  while ((match = regex.exec(pathStr)) !== null) {
    params.push({
      name: match[1],
      in: 'path',
      required: true,
      schema: { type: 'string' },
      description: `路径参数: ${match[1]}`
    });
  }
  return params;
}

function buildPaths(endpoints) {
  const paths = {};

  for (const ep of endpoints) {
    const pathStr = ep.path;
    const method = ep.method.toLowerCase();

    if (!paths[pathStr]) {
      paths[pathStr] = {};
    }

    const operation = {
      summary: ep.summary || '',
      description: ep.description || '',
      operationId: generateOperationId(method, pathStr),
      tags: [ep.tags?.trim() || '未分类'],
      responses: {
        '200': { description: '成功响应' },
        '400': { description: '请求参数错误' },
        '401': { description: '未认证' },
        '403': { description: '权限不足' },
        '500': { description: '服务器内部错误' }
      }
    };

    const pathParams = extractPathParameters(pathStr);
    if (pathParams.length > 0) {
      operation.parameters = pathParams;
    }

    if (['post', 'put', 'patch'].includes(method)) {
      operation.requestBody = {
        description: '请求体',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              description: '根据具体接口定义请求体结构'
            }
          }
        }
      };
    }

    paths[pathStr][method] = operation;
  }

  return paths;
}

function generateOpenAPISpec(inventory) {
  const endpoints = inventory.endpoints || [];

  const spec = {
    openapi: '3.0.3',
    info: {
      title: 'TOS 系统默认模块 API',
      description: `TOS (Truenas Open Storage) 系统默认模块的完整 API 接口规范。

本规范基于 API 调查报告自动生成，包含 ${inventory.total_apis} 个接口的定义。

## 认证方式
大多数接口需要有效的 \`TMSESSNAME\` Cookie 进行认证。

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
`,
      version: '1.0.0',
      contact: {
        name: 'TOS API 研究团队'
      }
    },
    servers: [
      {
        url: 'http://192.168.64.8:8181',
        description: 'TOS 开发环境'
      },
      {
        url: 'http://192.168.64.7:8181',
        description: 'TOS 正式环境'
      }
    ],
    paths: buildPaths(endpoints),
    components: {
      securitySchemes: {
        CookieAuth: {
          type: 'apiKey',
          in: 'cookie',
          name: 'TMSESSNAME',
          description: 'TOS 会话认证 Cookie'
        }
      },
      schemas: {
        Error: {
          type: 'object',
          properties: {
            code: {
              type: 'integer',
              description: '错误码'
            },
            message: {
              type: 'string',
              description: '错误信息'
            }
          }
        }
      }
    },
    security: [
      { CookieAuth: [] }
    ],
    tags: []
  };

  const categories = categorizeEndpoints(endpoints);
  for (const tagName of Object.keys(categories).sort()) {
    spec.tags.push({
      name: tagName,
      description: `${tagName}相关接口`
    });
  }

  return spec;
}

function main() {
  const baseDir = __dirname;
  const jsonPath = path.join(baseDir, 'tos_api_inventory.json');
  const outputPath = path.join(baseDir, 'tos_openapi.yaml');

  console.log('📖 加载 API 清单:', jsonPath);
  const inventory = loadApiInventory(jsonPath);
  console.log(`✅ 成功加载 ${inventory.total_apis} 个接口`);

  console.log('🔧 生成 OpenAPI 3.0 规范...');
  const spec = generateOpenAPISpec(inventory);

  console.log('💾 保存到:', outputPath);
  const yamlContent = toYAML(spec);
  fs.writeFileSync(outputPath, yamlContent, 'utf-8');

  const categories = categorizeEndpoints(inventory.endpoints);
  console.log('\n📊 接口分类统计:');
  const sortedCategories = Object.entries(categories).sort((a, b) => b[1].length - a[1].length);
  for (const [tag, eps] of sortedCategories) {
    console.log(`  - ${tag}: ${eps.length} 个接口`);
  }

  console.log(`\n✅ OpenAPI 规范生成完成！`);
  console.log(`📁 文件位置: ${outputPath}`);
  console.log(`🔢 总计接口: ${inventory.total_apis} 个`);
  console.log(`📝 分类数量: ${Object.keys(categories).length} 个`);

  console.log('\n' + '='.repeat(60));
  console.log('📚 后续使用指南:');
  console.log('='.repeat(60));
  console.log('1. 在 Postman 中导入:');
  console.log('   - 打开 Postman → Import → 选择 tos_openapi.yaml');
  console.log('   - 或使用 Postman MCP: /postman:sync');
  console.log('\n2. 生成客户端代码:');
  console.log('   - 使用 openapi-generator 生成 Python/TypeScript 客户端');
  console.log('   - 或使用 Postman MCP: /postman:codegen');
  console.log('\n3. 生成 API 文档:');
  console.log('   - 使用 Redoc: redoc-cli serve tos_openapi.yaml');
  console.log('   - 使用 Swagger UI: swagger-ui-dist');
  console.log('\n4. 运行安全审计:');
  console.log('   - 使用 Postman MCP: /postman:security');
}

main();
