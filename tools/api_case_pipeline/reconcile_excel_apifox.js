// Excel ↔ Apifox 存储管理单接口用例只读完整对账。
// 数据来源：Excel 真源 + Apifox 原生格式只读导出快照。
// 本工具只写本地报告和 temp_scripts 快照，不修改 Apifox 项目。

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const XLSX = require('xlsx');

const ROOT = path.resolve(__dirname, '..', '..');
const CONFIG_FILE = path.join(__dirname, 'config', 'storage_scope.json');

function parseArgs(argv) {
  const result = { refresh: false, date: localDateStamp(new Date()) };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--refresh') result.refresh = true;
    else if (argv[i] === '--snapshot') result.snapshot = argv[++i];
    else if (argv[i] === '--json') result.json = argv[++i];
    else if (argv[i] === '--markdown') result.markdown = argv[++i];
    else if (argv[i] === '--date') result.date = argv[++i];
    else if (argv[i] === '--help' || argv[i] === '-h') result.help = true;
    else throw new Error(`未知参数: ${argv[i]}`);
  }
  return result;
}

function localDateStamp(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}${m}${d}`;
}

function resolveRoot(relativeOrAbsolute) {
  return path.isAbsolute(relativeOrAbsolute)
    ? relativeOrAbsolute
    : path.resolve(ROOT, relativeOrAbsolute);
}

function printHelp() {
  console.log(`用法:
  node tools/api_case_pipeline/reconcile_excel_apifox.js [选项]

选项:
  --refresh             先通过 Apifox CLI 只读导出最新原生快照
  --snapshot <path>     指定已有 Apifox 原生快照
  --json <path>         指定 JSON 报告路径
  --markdown <path>     指定 Markdown 报告路径
  --date <YYYYMMDD>     报告日期（默认本地当天）

示例:
  node tools/api_case_pipeline/reconcile_excel_apifox.js --refresh
`);
}

function refreshSnapshot(config, snapshotFile) {
  fs.mkdirSync(path.dirname(snapshotFile), { recursive: true });
  const folderIds = config.sheets.map(x => x.folderId).join(',');
  const cliArgs = [
    'export', '--project', String(config.projectId), '--branch', config.branch,
    '--format', 'apifox', '--scope', 'folders', '--folder-ids', folderIds,
    '--module-id', String(config.moduleId), '--include-api-cases',
    '--output', snapshotFile
  ];
  let executable = 'apifox';
  let args = cliArgs;
  if (process.platform === 'win32') {
    const cliEntry = path.join(
      process.env.APPDATA || '',
      'npm', 'node_modules', 'apifox-cli', 'bin', 'cli.js'
    );
    if (!fs.existsSync(cliEntry)) {
      throw new Error(`找不到 Apifox CLI Node 入口: ${cliEntry}`);
    }
    executable = process.execPath;
    args = [cliEntry, ...cliArgs];
  }
  console.log(`只读导出 Apifox 快照: project=${config.projectId}, branch=${config.branch}`);
  const result = spawnSync(executable, args, {
    cwd: ROOT,
    encoding: 'utf8',
    windowsHide: true,
    maxBuffer: 20 * 1024 * 1024
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`Apifox 导出失败(${result.status}): ${result.stderr || result.stdout}`);
  }
  if (!fs.existsSync(snapshotFile) || fs.statSync(snapshotFile).size === 0) {
    throw new Error(`Apifox 导出未生成有效快照: ${snapshotFile}`);
  }
}

function normalizeText(value) {
  return String(value ?? '')
    .replace(/\r+/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n+/g, '\n')
    .trim();
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function normalizePath(value) {
  return String(value ?? '')
    .trim()
    .split('?')[0]
    .replace(/:\w+$/g, '')
    .replace(/\/{2,}/g, '/');
}

function normalizeMethod(value) {
  return String(value ?? '').trim().toLowerCase();
}

function endpointKey(method, endpointPath) {
  return `${normalizeMethod(method)}|${normalizePath(endpointPath)}`;
}

function flattenApifoxProject(project) {
  const endpoints = [];
  const projectPostProcessors = project.projectSetting?.postProcessors || [];
  function walk(items, currentFolder, inheritedPostProcessors = projectPostProcessors) {
    for (const item of items || []) {
      if (item.api) {
        const api = item.api;
        endpoints.push({
          id: Number(api.id),
          name: item.name || api.name || '',
          method: normalizeMethod(api.method),
          path: normalizePath(api.path),
          folderId: currentFolder?.id || null,
          folderName: currentFolder?.name || '',
          moduleId: Number(api.moduleId || item.moduleId || 0),
          status: api.status || '',
          cases: Array.isArray(api.cases) ? api.cases : [],
          definition: api,
          inheritedPostProcessors
        });
      } else if (Array.isArray(item.items)) {
        walk(
          item.items,
          { id: Number(item.id), name: item.name || '' },
          [...inheritedPostProcessors, ...(item.postProcessors || [])]
        );
      }
    }
  }
  for (const root of project.apiCollection || []) {
    walk(
      root.items,
      { id: Number(root.id), name: root.name || '' },
      [...projectPostProcessors, ...(root.postProcessors || [])]
    );
  }
  return endpoints;
}

function readExcel(config, excelFile) {
  const workbook = XLSX.readFile(excelFile);
  const methodErrorRe = new RegExp(config.methodErrorPattern);
  const rows = [];
  const groups = new Map();
  for (const sheetConfig of config.sheets) {
    const sheet = workbook.Sheets[sheetConfig.sheet];
    if (!sheet) throw new Error(`Excel 缺少 Sheet: ${sheetConfig.sheet}`);
    const data = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
    for (let index = 1; index < data.length; index++) {
      const raw = data[index];
      const func = normalizeText(raw[3]);
      const title = normalizeText(raw[8]);
      if (!func || !title) continue;
      const row = {
        sheet: sheetConfig.sheet,
        folderName: sheetConfig.folderName,
        row: index + 1,
        caseId: normalizeText(raw[0]),
        module: normalizeText(raw[1]),
        path: normalizePath(raw[2]),
        func,
        priority: normalizeText(raw[4]),
        method: normalizeMethod(raw[5]),
        headers: normalizeText(raw[6]),
        requestParams: normalizeText(raw[7]),
        title,
        precondition: normalizeText(raw[9]),
        steps: normalizeText(raw[10]),
        actualResult: normalizeText(raw[11]),
        expectedResult: normalizeText(raw[12]),
        note: normalizeText(raw[13]),
        isMethodError: methodErrorRe.test(title)
      };
      rows.push(row);
      const groupKey = `${row.sheet}|${row.func}`;
      if (!groups.has(groupKey)) groups.set(groupKey, { key: groupKey, sheet: row.sheet, func: row.func, rows: [] });
      groups.get(groupKey).rows.push(row);
    }
  }
  return { rows, groups: [...groups.values()] };
}

function indexEndpoints(endpoints) {
  const byKey = new Map();
  const byPath = new Map();
  for (const endpoint of endpoints) {
    const key = endpointKey(endpoint.method, endpoint.path);
    if (!byKey.has(key)) byKey.set(key, []);
    byKey.get(key).push(endpoint);
    if (!byPath.has(endpoint.path)) byPath.set(endpoint.path, []);
    byPath.get(endpoint.path).push(endpoint);
  }
  return { byKey, byPath };
}

function chooseEndpoint(group, endpointIndex) {
  const candidates = group.rows.filter(x => !x.isMethodError);
  for (const row of candidates) {
    const exact = endpointIndex.byKey.get(endpointKey(row.method, row.path)) || [];
    const folderExact = exact.filter(x => x.folderName === row.folderName);
    if (folderExact.length === 1) return { endpoint: folderExact[0], strategy: 'method+path+folder', sourceRow: row.row };
    if (exact.length === 1) return { endpoint: exact[0], strategy: 'method+path', sourceRow: row.row };
  }
  for (const row of candidates) {
    const samePath = endpointIndex.byPath.get(row.path) || [];
    const folderExact = samePath.filter(x => x.folderName === row.folderName);
    if (folderExact.length === 1) return { endpoint: folderExact[0], strategy: 'path+folder', sourceRow: row.row };
    if (samePath.length === 1) return { endpoint: samePath[0], strategy: 'path-only', sourceRow: row.row };
  }
  return { endpoint: null, strategy: 'unmatched', sourceRow: candidates[0]?.row || group.rows[0]?.row };
}

function parseExpectedHeaders(raw) {
  const headers = new Map();
  if (!raw || /^(无|none|n\/a)$/i.test(raw)) return headers;
  for (const line of raw.split('\n')) {
    const match = line.trim().match(/^([^:：]+)\s*[:：]\s*(.*)$/);
    if (!match) continue;
    const name = match[1].trim();
    if (name && name.length <= 80) headers.set(name.toLowerCase(), { name, value: match[2].trim() });
  }
  return headers;
}

function actualHeaders(testCase, endpoint) {
  const headers = new Map();
  for (const item of endpoint.definition?.parameters?.header || []) {
    if (item.enable === false || !item.name) continue;
    headers.set(String(item.name).trim().toLowerCase(), {
      name: String(item.name).trim(),
      value: normalizeText(item.value ?? item.example ?? item.default ?? '')
    });
  }
  for (const item of testCase.parameters?.header || []) {
    if (item.enable === false || !item.name) continue;
    headers.set(String(item.name).trim().toLowerCase(), {
      name: String(item.name).trim(),
      value: normalizeText(item.value)
    });
  }
  return headers;
}

function tryJson(raw) {
  const value = normalizeText(raw);
  if (!value || /^(无|none|n\/a)$/i.test(value)) return null;
  if (!(value.startsWith('{') || value.startsWith('['))) return null;
  try { return JSON.parse(value); } catch { return null; }
}

function stableJson(value) {
  if (Array.isArray(value)) return value.map(stableJson);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, stableJson(value[key])]));
  }
  return value;
}

function topLevelKeys(value) {
  return value && !Array.isArray(value) && typeof value === 'object' ? Object.keys(value) : [];
}

function rawObjectKeys(raw) {
  const value = normalizeText(raw);
  if (!value) return [];
  const names = [];
  const pattern = /(?:^|[,{\n]\s*)["']?([A-Za-z_][\w.-]{0,63})["']?\s*:/g;
  for (const match of value.matchAll(pattern)) names.push(match[1]);
  return [...new Set(names)];
}

function requestBodyJson(requestBody) {
  const candidates = [
    requestBody?.data,
    ...(requestBody?.examples || []).map(example => example?.value ?? example?.data)
  ];
  for (const candidate of candidates) {
    if (candidate && typeof candidate === 'object') return candidate;
    const parsed = tryJson(candidate);
    if (parsed) return parsed;
  }
  return null;
}

function addRequestBodyNames(names, requestBody) {
  for (const item of requestBody?.parameters || []) {
    if (item.enable !== false && item.name) names.add(String(item.name));
  }
  for (const name of Object.keys(requestBody?.jsonSchema?.properties || {})) names.add(name);
  for (const name of topLevelKeys(requestBodyJson(requestBody))) names.add(name);
  for (const name of rawObjectKeys(requestBody?.data)) names.add(name);
}

function expectedParameterNames(raw) {
  const json = tryJson(raw);
  if (json) return { names: topLevelKeys(json), parsedAs: 'json', json };
  if (!raw || /^(无|none|n\/a)$/i.test(raw)) return { names: [], parsedAs: 'none', json: null };
  const names = [];
  for (const line of raw.split('\n')) {
    const cleaned = line.trim().replace(/^[-*•\d.、)\s]+/, '');
    const match = cleaned.match(/^([A-Za-z_][\w.-]{0,63})\s*(?:[:：=]|$)/);
    if (match) names.push(match[1]);
  }
  return { names: [...new Set(names)], parsedAs: names.length ? 'key-value' : 'unparsed', json: null };
}

function actualParameterNames(testCase, endpoint) {
  const names = new Set();
  for (const type of ['query', 'path', 'cookie']) {
    for (const item of endpoint.definition?.parameters?.[type] || []) {
      if (item.enable !== false && item.name) names.add(String(item.name));
    }
    for (const item of testCase.parameters?.[type] || []) {
      if (item.enable !== false && item.name) names.add(String(item.name));
    }
  }
  addRequestBodyNames(names, endpoint.definition?.requestBody);
  addRequestBodyNames(names, testCase.requestBody);
  const bodyJson = requestBodyJson(testCase.requestBody) || requestBodyJson(endpoint.definition?.requestBody);
  const bodyRaw = normalizeText(
    testCase.requestBody?.data ?? endpoint.definition?.requestBody?.data ?? ''
  );
  return { names: [...names], bodyJson, bodyRaw };
}

function assertionInfo(testCase, endpoint) {
  const processors = [
    ...(endpoint.inheritedPostProcessors || []),
    ...(endpoint.definition?.postProcessors || []),
    ...(testCase.postProcessors || []),
    ...(testCase.inheritPostProcessorsSnapshot || [])
  ];
  let visual = 0;
  let script = 0;
  for (const processor of processors) {
    if (processor?.enable === false) continue;
    if (processor?.type === 'assertion') visual++;
    if (processor?.type === 'customScript' && /pm\.test\s*\(/.test(String(processor.data || ''))) script++;
  }
  return { visual, script, total: visual + script };
}

function compareCase(row, testCase, endpoint, validCategories) {
  const issues = [];
  const expectedHeaders = parseExpectedHeaders(row.headers);
  const foundHeaders = actualHeaders(testCase, endpoint);
  for (const [key, expected] of expectedHeaders) {
    const actual = foundHeaders.get(key);
    if (!actual) {
      issues.push({ type: 'header_missing', severity: 'medium', field: expected.name, expected: expected.value, actual: '' });
    } else if (normalizeText(expected.value).toLowerCase() !== normalizeText(actual.value).toLowerCase()) {
      issues.push({ type: 'header_value_diff', severity: 'medium', field: expected.name, expected: expected.value, actual: actual.value });
    }
  }

  const expectedParams = expectedParameterNames(row.requestParams);
  const foundParams = actualParameterNames(testCase, endpoint);
  const foundNamesLower = new Set(foundParams.names.map(x => x.toLowerCase()));
  for (const name of expectedParams.names) {
    const rawBodyHasName = new RegExp(`(^|\\W)${escapeRegExp(name)}(\\W|$)`, 'i').test(foundParams.bodyRaw);
    if (!foundNamesLower.has(name.toLowerCase()) && !rawBodyHasName) {
      issues.push({ type: 'parameter_missing', severity: 'medium', field: name, expected: '存在', actual: '未找到' });
    }
  }

  if (expectedParams.json && foundParams.bodyJson) {
    const expectedCanonical = JSON.stringify(stableJson(expectedParams.json));
    const actualCanonical = JSON.stringify(stableJson(foundParams.bodyJson));
    if (expectedCanonical !== actualCanonical) {
      issues.push({ type: 'request_body_diff', severity: 'high', field: 'requestBody', expected: expectedCanonical, actual: actualCanonical });
    }
  }

  const assertions = assertionInfo(testCase, endpoint);
  if (row.expectedResult && assertions.total === 0) {
    issues.push({ type: 'assertion_gap', severity: 'low', field: 'postProcessors', expected: 'Excel 有预期结果', actual: 'Apifox 无可识别断言' });
  }
  if (!testCase.categoryId || !validCategories.has(Number(testCase.categoryId))) {
    issues.push({ type: 'category_invalid', severity: 'medium', field: 'categoryId', expected: '有效分类', actual: String(testCase.categoryId || '') });
  }

  return {
    issues,
    evidence: {
      expectedHeaderCount: expectedHeaders.size,
      actualHeaderCount: foundHeaders.size,
      parameterParseMode: expectedParams.parsedAs,
      expectedParameterCount: expectedParams.names.length,
      actualParameterCount: foundParams.names.length,
      assertionCount: assertions.total
    }
  };
}

function addCount(object, key, increment = 1) {
  object[key] = (object[key] || 0) + increment;
}

function reconcile(config, excel, endpoints, project) {
  const endpointIndex = indexEndpoints(endpoints);
  const mappings = [];
  const handledEndpointIds = new Set();
  const expectedByEndpoint = new Map();
  const mappingIssues = [];

  for (const group of excel.groups) {
    const selected = chooseEndpoint(group, endpointIndex);
    mappings.push({
      sheet: group.sheet,
      func: group.func,
      endpointId: selected.endpoint?.id || null,
      endpointName: selected.endpoint?.name || '',
      method: selected.endpoint?.method || '',
      path: selected.endpoint?.path || '',
      strategy: selected.strategy,
      sourceRow: selected.sourceRow
    });
    if (!selected.endpoint) {
      mappingIssues.push({ sheet: group.sheet, func: group.func, row: selected.sourceRow, reason: '端点未匹配' });
      continue;
    }
    handledEndpointIds.add(selected.endpoint.id);
    if (!expectedByEndpoint.has(selected.endpoint.id)) expectedByEndpoint.set(selected.endpoint.id, []);
    expectedByEndpoint.get(selected.endpoint.id).push(...group.rows.filter(row => !row.isMethodError));
  }

  const validCategories = new Set((project.projectTestCaseCategories || []).map(x => Number(x.id)));
  const missingCases = [];
  const extraCases = [];
  const contentIssues = [];
  const matchedCases = [];
  const issueCounts = {};
  const severityCounts = {};
  const issuesBySheet = {};
  let matched = 0;

  for (const endpoint of endpoints) {
    if (!handledEndpointIds.has(endpoint.id)) continue;
    const expectedRows = expectedByEndpoint.get(endpoint.id) || [];
    const availableByTitle = new Map();
    for (const testCase of endpoint.cases) {
      const title = normalizeText(testCase.name);
      if (!availableByTitle.has(title)) availableByTitle.set(title, []);
      availableByTitle.get(title).push(testCase);
    }
    const usedIds = new Set();
    for (const row of expectedRows) {
      const available = availableByTitle.get(row.title) || [];
      const testCase = available.find(item => !usedIds.has(Number(item.id)));
      if (!testCase) {
        missingCases.push({ sheet: row.sheet, row: row.row, caseId: row.caseId, func: row.func, title: row.title, endpointId: endpoint.id, method: endpoint.method, path: endpoint.path });
        addCount(issuesBySheet, row.sheet);
        continue;
      }
      usedIds.add(Number(testCase.id));
      matched++;
      const compared = compareCase(row, testCase, endpoint, validCategories);
      matchedCases.push({
        sheet: row.sheet,
        row: row.row,
        caseId: row.caseId,
        title: row.title,
        endpointId: endpoint.id,
        apifoxCaseId: Number(testCase.id),
        evidence: compared.evidence
      });
      for (const issue of compared.issues) {
        const record = {
          ...issue,
          sheet: row.sheet,
          row: row.row,
          caseId: row.caseId,
          func: row.func,
          title: row.title,
          endpointId: endpoint.id,
          apifoxCaseId: Number(testCase.id),
          method: endpoint.method,
          path: endpoint.path
        };
        contentIssues.push(record);
        addCount(issueCounts, issue.type);
        addCount(severityCounts, issue.severity);
        addCount(issuesBySheet, row.sheet);
      }
    }
    for (const testCase of endpoint.cases) {
      if (!usedIds.has(Number(testCase.id))) {
        extraCases.push({
          folder: endpoint.folderName,
          endpointId: endpoint.id,
          endpointName: endpoint.name,
          method: endpoint.method,
          path: endpoint.path,
          apifoxCaseId: Number(testCase.id),
          title: normalizeText(testCase.name)
        });
      }
    }
  }

  const outOfScopeEndpoints = endpoints
    .filter(endpoint => !handledEndpointIds.has(endpoint.id))
    .map(endpoint => ({
      folder: endpoint.folderName,
      endpointId: endpoint.id,
      endpointName: endpoint.name,
      method: endpoint.method,
      path: endpoint.path,
      caseCount: endpoint.cases.length
    }));

  const importableRows = excel.rows.filter(row => !row.isMethodError).length;
  return {
    summary: {
      excelRows: excel.rows.length,
      methodErrorRows: excel.rows.length - importableRows,
      importableRows,
      excelFunctionGroups: excel.groups.length,
      apifoxEndpointsInExport: endpoints.length,
      handledEndpoints: handledEndpointIds.size,
      outOfScopeEndpoints: outOfScopeEndpoints.length,
      apifoxCasesInExport: endpoints.reduce((sum, endpoint) => sum + endpoint.cases.length, 0),
      matchedCases: matched,
      missingCases: missingCases.length,
      extraCasesOnHandledEndpoints: extraCases.length,
      contentIssues: contentIssues.length,
      issueCounts,
      severityCounts,
      issuesBySheet
    },
    mappings,
    mappingIssues,
    missingCases,
    extraCases,
    outOfScopeEndpoints,
    contentIssues,
    matchedCases
  };
}

function escapeCell(value) {
  return normalizeText(value).replace(/\|/g, '\\|').replace(/\n/g, '<br>');
}

function markdownTable(headers, rows) {
  if (!rows.length) return '_无_\n';
  return [
    `| ${headers.join(' | ')} |`,
    `| ${headers.map(() => '---').join(' | ')} |`,
    ...rows.map(row => `| ${row.map(escapeCell).join(' | ')} |`)
  ].join('\n') + '\n';
}

function renderMarkdown(meta, result) {
  const s = result.summary;
  const limits = { missing: 200, extra: 200, content: 300, outOfScope: 200 };
  const issueLabels = {
    header_missing: '请求头缺失',
    header_value_diff: '请求头值不同',
    parameter_missing: '请求参数缺失',
    request_body_diff: '请求体不同',
    assertion_gap: '断言覆盖缺口',
    category_invalid: '分类无效'
  };
  const lines = [
    `# Excel ↔ Apifox 存储管理完整对账（${meta.date}）`,
    '',
    '> 本报告由只读工具生成。Apifox 原生快照存放在 Git 忽略的 `temp_scripts/`；执行过程没有修改 Apifox 项目。',
    '',
    '## 结论',
    '',
    `- Excel 共 ${s.excelRows} 条，其中请求方法错误类 ${s.methodErrorRows} 条不导入，理论应同步 ${s.importableRows} 条。`,
    `- Apifox 快照包含 ${s.apifoxEndpointsInExport} 个存储管理接口、${s.apifoxCasesInExport} 条单接口用例。`,
    `- Excel 功能分组映射到 ${s.handledEndpoints} 个实际端点；其余 ${s.outOfScopeEndpoints} 个为明确不处理范围，不计为缺失。`,
    `- 成功同名匹配 ${s.matchedCases} 条；缺失 ${s.missingCases} 条；处理范围端点上额外用例 ${s.extraCasesOnHandledEndpoints} 条。`,
    `- 内容级检查发现 ${s.contentIssues} 项：高风险 ${s.severityCounts.high || 0}、中风险 ${s.severityCounts.medium || 0}、低风险 ${s.severityCounts.low || 0}；详见下表和 JSON 完整明细。`,
    '',
    '## 统计摘要',
    '',
    markdownTable(['指标', '数量'], [
      ['Excel 数据行', s.excelRows],
      ['方法错误类（不导入）', s.methodErrorRows],
      ['应同步用例', s.importableRows],
      ['Excel 功能分组', s.excelFunctionGroups],
      ['Apifox 导出接口', s.apifoxEndpointsInExport],
      ['Excel 实际涉及端点', s.handledEndpoints],
      ['明确不处理端点', s.outOfScopeEndpoints],
      ['Apifox 导出用例', s.apifoxCasesInExport],
      ['同名匹配用例', s.matchedCases],
      ['缺失用例', s.missingCases],
      ['处理范围额外用例', s.extraCasesOnHandledEndpoints],
      ['内容问题', s.contentIssues]
    ]),
    '## 内容问题分类',
    '',
    markdownTable(['类型', '数量'], Object.entries(s.issueCounts).map(([key, count]) => [issueLabels[key] || key, count])),
    '## 按风险级别',
    '',
    markdownTable(['级别', '数量'], ['high', 'medium', 'low'].map(level => [level, s.severityCounts[level] || 0])),
    '## 按 Sheet 问题数',
    '',
    markdownTable(['Sheet', '问题数'], meta.sheetNames.map(name => [name, s.issuesBySheet[name] || 0])),
    '## 端点映射失败',
    '',
    markdownTable(['Sheet', '关联功能', 'Excel 行', '原因'], result.mappingIssues.map(x => [x.sheet, x.func, x.row, x.reason])),
    '## Excel 有、Apifox 缺失的用例',
    '',
    markdownTable(['Sheet', '行', '用例 ID', '关联功能', '标题', '方法', '路径'], result.missingCases.slice(0, limits.missing).map(x => [x.sheet, x.row, x.caseId, x.func, x.title, x.method, x.path])),
    '## 处理范围端点上的额外 Apifox 用例',
    '',
    markdownTable(['目录', '接口', 'Apifox Case ID', '标题', '方法', '路径'], result.extraCases.slice(0, limits.extra).map(x => [x.folder, x.endpointName, x.apifoxCaseId, x.title, x.method, x.path])),
    '## 内容级问题',
    '',
    markdownTable(['级别', '类型', 'Sheet/行', '用例', '字段', 'Excel', 'Apifox'], result.contentIssues.slice(0, limits.content).map(x => [x.severity, issueLabels[x.type] || x.type, `${x.sheet}/${x.row}`, x.title, x.field, x.expected, x.actual])),
    '## 明确不处理的 Apifox 接口',
    '',
    markdownTable(['目录', '接口 ID', '接口名', '方法', '路径', '用例数'], result.outOfScopeEndpoints.slice(0, limits.outOfScope).map(x => [x.folder, x.endpointId, x.endpointName, x.method, x.path, x.caseCount])),
    '## 能力边界',
    '',
    '- 名称、数量、端点映射、分类、结构化请求头和参数名存在性为确定性检查。',
    '- 只有 Excel 与 Apifox 两侧请求体均为合法 JSON 时才做请求体精确比较。',
    '- 查询参数和表单参数的值尚未做自动等价判断，不能仅凭本报告宣称内容完全一致。',
    '- Excel “前置条件/操作步骤/预期结果”是自然语言；本版只检查预期结果是否有可识别的 Apifox 断言，不宣称语义等价。',
    '- Markdown 为便于审阅会截断超长明细；JSON 报告保存全部记录。',
    '',
    `快照 SHA-256：\`${meta.snapshotSha256}\``
  ];
  return lines.join('\n');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return printHelp();
  const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
  const excelFile = resolveRoot(config.excel);
  const snapshotFile = resolveRoot(args.snapshot || config.snapshot);
  const jsonFile = resolveRoot(args.json || `docs/reports/data/apifox_excel_reconcile_${args.date}.json`);
  const markdownFile = resolveRoot(args.markdown || `docs/reports/Apifox_Excel完整对账_${args.date}.md`);

  if (args.refresh) refreshSnapshot(config, snapshotFile);
  if (!fs.existsSync(snapshotFile)) {
    throw new Error(`缺少 Apifox 快照，请先加 --refresh: ${snapshotFile}`);
  }

  const snapshotBuffer = fs.readFileSync(snapshotFile);
  const project = JSON.parse(snapshotBuffer.toString('utf8'));
  const endpoints = flattenApifoxProject(project);
  const excel = readExcel(config, excelFile);
  const result = reconcile(config, excel, endpoints, project);
  const meta = {
    generatedAt: new Date().toISOString(),
    date: args.date,
    projectId: config.projectId,
    projectName: project.info?.name || '',
    branch: config.branch,
    moduleId: config.moduleId,
    excel: path.relative(ROOT, excelFile).replace(/\\/g, '/'),
    snapshot: path.relative(ROOT, snapshotFile).replace(/\\/g, '/'),
    snapshotBytes: snapshotBuffer.length,
    snapshotSha256: crypto.createHash('sha256').update(snapshotBuffer).digest('hex'),
    sheetNames: config.sheets.map(x => x.sheet),
    readOnly: true
  };

  fs.mkdirSync(path.dirname(jsonFile), { recursive: true });
  fs.mkdirSync(path.dirname(markdownFile), { recursive: true });
  fs.writeFileSync(jsonFile, JSON.stringify({ meta, ...result }, null, 2) + '\n', 'utf8');
  fs.writeFileSync(markdownFile, renderMarkdown(meta, result) + '\n', 'utf8');

  console.log(JSON.stringify({
    project: `${meta.projectName} (${meta.projectId})`,
    branch: meta.branch,
    ...result.summary,
    jsonReport: path.relative(ROOT, jsonFile),
    markdownReport: path.relative(ROOT, markdownFile)
  }, null, 2));
  if (result.mappingIssues.length || result.missingCases.length) process.exitCode = 2;
}

try {
  main();
} catch (error) {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
}
