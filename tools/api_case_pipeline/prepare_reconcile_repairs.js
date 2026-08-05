// 根据完整对账报告生成 Apifox AI 分支用例更新载荷和 Excel 精确改单。
// 本脚本不调用 Apifox；远端写入由 CLI 在 schema 校验后执行。

const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

const ROOT = path.resolve(__dirname, '..', '..');
const REPORT = path.join(ROOT, 'docs', 'reports', 'data', 'apifox_excel_reconcile_20260805.json');
const SNAPSHOT = path.join(ROOT, 'temp_scripts', 'apifox_storage_baseline.apifox.json');
const CONFIG = path.join(__dirname, 'config', 'storage_scope.json');
const PAYLOAD_DIR = path.join(ROOT, 'temp_scripts', 'apifox_reconcile_payloads_20260805');
const MANIFEST = path.join(PAYLOAD_DIR, 'manifest.json');

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function flattenProject(project) {
  const cases = new Map();
  const endpoints = new Map();
  function walk(items, folderName) {
    for (const item of items || []) {
      if (item.api) {
        const endpoint = {
          id: Number(item.api.id),
          name: item.name || item.api.name || '',
          folderName,
          definition: item.api
        };
        endpoints.set(endpoint.id, endpoint);
        for (const testCase of item.api.cases || []) {
          cases.set(Number(testCase.id), { testCase, endpoint });
        }
      } else if (Array.isArray(item.items)) {
        walk(item.items, item.name || folderName);
      }
    }
  }
  for (const root of project.apiCollection || []) walk(root.items, root.name || '');
  return { cases, endpoints };
}

function bodyType(record) {
  return record?.type || 'none';
}

function findHeader(headers, name) {
  return (headers || []).find(item => String(item.name || '').toLowerCase() === name.toLowerCase());
}

function setHeader(testCase, name, value) {
  testCase.parameters ||= {};
  testCase.parameters.header ||= [];
  const existing = findHeader(testCase.parameters.header, name);
  if (existing) {
    existing.value = value;
    existing.enable = true;
    existing.relatedName ||= name;
    return;
  }
  testCase.parameters.header.push({
    name,
    value,
    enable: true,
    id: `reconcile.${testCase.id}.${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
    relatedName: name
  });
}

function setQuery(testCase, name, value, replaceName) {
  testCase.parameters ||= {};
  testCase.parameters.query ||= [];
  let item = replaceName
    ? testCase.parameters.query.find(entry => String(entry.name || '').toLowerCase() === replaceName.toLowerCase())
    : testCase.parameters.query.find(entry => String(entry.name || '').toLowerCase() === name.toLowerCase());
  if (!item) {
    item = { id: `reconcile.${testCase.id}.query.${name}`, enable: true };
    testCase.parameters.query.push(item);
  }
  item.name = name;
  item.relatedName = name;
  item.value = value;
  item.enable = true;
}

function makePayload(testCase, endpointId) {
  return {
    name: testCase.name,
    categoryId: Number(testCase.categoryId),
    responseId: testCase.responseId ?? '0',
    apiDetailId: Number(endpointId),
    method: testCase.method || '',
    path: testCase.path ?? null,
    parameters: deepClone(testCase.parameters || { query: [], path: [], header: [], cookie: [] }),
    commonParameters: deepClone(testCase.commonParameters || {}),
    requestBody: deepClone(testCase.requestBody || { type: 'none' }),
    preProcessors: deepClone(testCase.preProcessors || []),
    postProcessors: deepClone(testCase.postProcessors || []),
    inheritPreProcessors: deepClone(testCase.inheritPreProcessors || {}),
    inheritPostProcessors: deepClone(testCase.inheritPostProcessors || {}),
    auth: deepClone(testCase.auth || {}),
    securityScheme: deepClone(testCase.securityScheme || {}),
    advancedSettings: deepClone(testCase.advancedSettings || {}),
    visibility: testCase.visibility || 'INHERITED',
    tagIds: deepClone(testCase.tagIds || [])
  };
}

function replaceContentType(raw, value) {
  return String(raw || '').replace(
    /(Content-Type\s*[:：]\s*)[^\r\n]*/i,
    `$1${value}`
  );
}

function removeContentType(raw) {
  return String(raw || '')
    .replace(/(?:^|[\r\n]+)Content-Type\s*[:：]\s*[^\r\n]*/i, '')
    .replace(/^[\r\n]+|[\r\n]+$/g, '')
    .replace(/\r{2,}\n/g, '\r\n');
}

function main() {
  const report = JSON.parse(fs.readFileSync(REPORT, 'utf8'));
  const project = JSON.parse(fs.readFileSync(SNAPSHOT, 'utf8'));
  const config = JSON.parse(fs.readFileSync(CONFIG, 'utf8'));
  const { cases } = flattenProject(project);
  const working = new Map();

  function editCase(issue, change) {
    const id = Number(issue.apifoxCaseId);
    if (!working.has(id)) {
      const source = cases.get(id);
      if (!source) throw new Error(`快照中找不到用例: ${id}`);
      working.set(id, {
        caseId: id,
        endpointId: Number(issue.endpointId),
        title: issue.title,
        sheet: issue.sheet,
        testCase: deepClone(source.testCase),
        endpoint: source.endpoint,
        changes: []
      });
    }
    const record = working.get(id);
    change(record.testCase, record);
  }

  // 认证类请求头：标题与 Excel 明确要求不同，统一写成用例级覆盖值。
  for (const issue of report.contentIssues) {
    if (!['header_value_diff', 'header_missing'].includes(issue.type)) continue;
    if (issue.field === 'Content-Type') continue;
    editCase(issue, (testCase, record) => {
      setHeader(testCase, issue.field, issue.expected);
      record.changes.push(`${issue.field}: ${issue.actual || '(缺失)'} -> ${issue.expected}`);
    });
  }

  // Content-Type 只改两类确定的 Apifox 内部冲突：JSON Body 配成 form；form Body 配成 JSON。
  for (const issue of report.contentIssues) {
    if (!['header_value_diff', 'header_missing'].includes(issue.type) || issue.field !== 'Content-Type') continue;
    const source = cases.get(Number(issue.apifoxCaseId));
    const caseType = bodyType(source?.testCase.requestBody);
    const shouldFixApifox =
      (issue.expected === 'application/json' && issue.actual === 'application/x-www-form-urlencoded' && caseType === 'application/json') ||
      (issue.expected === 'application/x-www-form-urlencoded' && issue.actual === 'application/json');
    if (!shouldFixApifox) continue;
    editCase(issue, (testCase, record) => {
      setHeader(testCase, 'Content-Type', issue.expected);
      record.changes.push(`Content-Type: ${issue.actual || '(缺失)'} -> ${issue.expected}`);
    });
  }

  // 5 个明确参数差异；Excel 第 112 行单独在本地修正，不更新 Apifox。
  const parameterRules = new Map([
    [398475713, testCase => {
      testCase.parameters.path = [];
      testCase.parameters.query = [];
      setQuery(testCase, 'dasd', 'dsadasasd');
    }],
    [398475794, testCase => {
      testCase.parameters.path = [];
      testCase.parameters.query = [];
      setQuery(testCase, 'uuid', '{{lv0_uuid}}');
      setQuery(testCase, 'dsad', 'dasd');
    }],
    [398476343, testCase => setQuery(testCase, 'dasdL', 'das', 'das')],
    [398477550, testCase => {
      testCase.requestBody = { type: 'application/json', data: 'dasdas' };
    }],
    [398480996, testCase => setQuery(testCase, 'dasdL', 'das', 'das')]
  ]);
  for (const issue of report.contentIssues.filter(item => item.type === 'parameter_missing' && item.row !== 112)) {
    const rule = parameterRules.get(Number(issue.apifoxCaseId));
    if (!rule) throw new Error(`缺少参数修复规则: ${issue.apifoxCaseId}`);
    editCase(issue, (testCase, record) => {
      rule(testCase);
      record.changes.push(`参数按 Excel 第 ${issue.row} 行修正`);
    });
  }

  fs.mkdirSync(PAYLOAD_DIR, { recursive: true });
  const manifest = [];
  for (const record of [...working.values()].sort((a, b) => a.caseId - b.caseId)) {
    const file = path.join(PAYLOAD_DIR, `${record.caseId}.json`);
    fs.writeFileSync(file, JSON.stringify(makePayload(record.testCase, record.endpointId), null, 2) + '\n', 'utf8');
    manifest.push({
      caseId: record.caseId,
      endpointId: record.endpointId,
      sheet: record.sheet,
      title: record.title,
      file: file.replace(/\\/g, '/'),
      changes: [...new Set(record.changes)]
    });
  }
  fs.writeFileSync(MANIFEST, JSON.stringify({ branch: 'ai/20260805-from-main-storage-reconcile', cases: manifest }, null, 2) + '\n', 'utf8');

  const excelChanges = [];
  const workbook = XLSX.readFile(path.join(ROOT, config.excel), { cellStyles: true });
  const changedCells = new Set();
  function updateCell(sheetName, rowNumber, column, transform, reason) {
    const sheet = workbook.Sheets[sheetName];
    const address = `${column}${rowNumber}`;
    const cell = sheet[address];
    if (!cell) throw new Error(`Excel 单元格不存在: ${sheetName}!${address}`);
    const before = String(cell.v ?? '');
    const after = transform(before);
    if (before === after) return;
    cell.v = after;
    cell.w = after;
    changedCells.add(`${sheetName}!${address}`);
    excelChanges.push({ sheet: sheetName, row: rowNumber, cell: address, before, after, reason });
  }

  for (const issue of report.contentIssues) {
    if (!['header_value_diff', 'header_missing'].includes(issue.type) || issue.field !== 'Content-Type') continue;
    const source = cases.get(Number(issue.apifoxCaseId));
    const caseType = bodyType(source?.testCase.requestBody);
    const endpointType = bodyType(source?.endpoint.definition.requestBody);
    const excelToForm =
      issue.expected === 'application/json' &&
      issue.actual === 'application/x-www-form-urlencoded' &&
      caseType === 'none' && endpointType === 'multipart/form-data';
    const excelRemove =
      issue.expected === 'application/json' &&
      caseType === 'none' && endpointType === 'none';
    if (excelToForm) {
      updateCell(issue.sheet, issue.row, 'G', raw => replaceContentType(raw, 'application/x-www-form-urlencoded'), '表单接口 Content-Type');
    } else if (excelRemove) {
      updateCell(issue.sheet, issue.row, 'G', removeContentType, '无请求体接口移除 Content-Type');
    }
  }
  updateCell('卷', 112, 'H', raw => raw.replace(/das\s*[:：]\s*asd/i, 'uuid:asd'), '路径占位符保持 uuid，使用非法值');

  const excelChangeFile = path.join(PAYLOAD_DIR, 'excel_changes.json');
  fs.writeFileSync(excelChangeFile, JSON.stringify({ cells: [...changedCells], changes: excelChanges }, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({
    apifoxCases: manifest.length,
    apifoxEndpoints: new Set(manifest.map(item => item.endpointId)).size,
    excelCells: changedCells.size,
    excelApplied: false,
    manifest: path.relative(ROOT, MANIFEST).replace(/\\/g, '/'),
    excelChangeFile: path.relative(ROOT, excelChangeFile).replace(/\\/g, '/')
  }, null, 2));
}

main();
