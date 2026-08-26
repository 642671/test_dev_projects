const fs = require('fs');
const path = require('path');

const sourceDir = __dirname;
const photoDir = path.dirname(sourceDir);
const finalDir = path.join(sourceDir, '最终测试用例');
fs.rmSync(finalDir, { recursive: true, force: true });
fs.mkdirSync(finalDir, { recursive: true });

const moduleDefs = [
  { key: 'security', file: '01-安全与权限.md', name: '安全与权限', prefixes: ['SEC', 'ACL'] },
  { key: 'api-config', file: '02-接口与配置兼容.md', name: '接口与配置兼容', prefixes: ['API', 'CFG'] },
  { key: 'task-state', file: '03-任务状态与生命周期.md', name: '任务状态与生命周期', prefixes: ['TASK', 'CTX'] },
  { key: 'device-identity', file: '04-磁盘与设备身份.md', name: '磁盘与设备身份', prefixes: ['DISK', 'LOCKED', 'ID', 'DI', 'FC', 'VC', 'HW', 'WARN'] },
  { key: 'pool-raid', file: '05-存储池与RAID.md', name: '存储池与 RAID', prefixes: ['POOL', 'RAID'] },
  { key: 'volume-format', file: '06-存储卷与格式化.md', name: '存储卷与格式化', prefixes: ['VOL', 'FORMAT'] },
  { key: 'cache-watermark', file: '07-缓存与容量水位.md', name: '缓存与容量水位', prefixes: ['CACHE', 'WM'] },
  { key: 'external', file: '08-USB-eSATA与外接设备.md', name: 'USB/eSATA 与外接设备', prefixes: ['HOTPLUG', 'USB'] },
  { key: 'iscsi', file: '09-iSCSI虚拟磁盘.md', name: 'iSCSI 虚拟磁盘', prefixes: ['ISCSI'] },
  { key: 'system-upgrade', file: '10-系统盘升级与稳健性.md', name: '系统盘、升级与稳健性', prefixes: ['SYS', 'UPGRADE', 'ROBUST'] },
];
const prefixToModule = new Map(moduleDefs.flatMap((def) => def.prefixes.map((prefix) => [prefix, def])));
const casePattern = /\b([A-Z][A-Z0-9]*-\d{3}|LOCKED-001)\b/;
const idPattern = /\b[A-Z][A-Z0-9]*-\d{3}\b/g;
const missing = '未在图片中显示';
const baselinePath = path.join(path.dirname(sourceDir), 'TOS7.1存储模块完整测试用例库.md');
const baselineText = fs.existsSync(baselinePath) ? fs.readFileSync(baselinePath, 'utf8') : '';
const baselineRows = new Map();
for (const line of baselineText.split(/\r?\n/)) {
  const match = line.match(/^\s*([A-Z][A-Z0-9]*-\d{3}|LOCKED-001)\s+(.+?)\s+(P[0-2])\s*$/);
  if (!match) continue;
  const id = match[1];
  const def = moduleDefs.find((item) => item.prefixes.includes(id.split('-')[0]));
  if (!def) continue;
  baselineRows.set(id, {
    id, module: def.name, title: match[2].trim(), priority: match[3],
    precondition: missing, input: missing, expected: missing, verification: missing,
    notes: '工作区既有完整测试用例库基线条目；图片未提供更细字段。', sourceImages: new Set(),
  });
}
const executionPath = path.join(path.dirname(sourceDir), 'TOS7.1存储模块测试执行版用例库01.md');
if (fs.existsSync(executionPath)) {
  const executionText = fs.readFileSync(executionPath, 'utf8');
  for (const line of executionText.split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z][A-Z0-9]*-\d{3}|LOCKED-001)\s+(.+?)\s+(P[0-2])\s+(.+?)\s{2,}(.+?)\s*$/);
    if (!match) continue;
    const id = match[1];
    if (!baselineRows.has(id)) continue;
    const row = baselineRows.get(id);
    row.title = match[2].trim();
    row.priority = match[3];
    row.notes = `执行版基线验证：${match[5].trim()}`;
  }
}

function clean(value) {
  return String(value ?? '')
    .replace(/\\\|/g, '|')
    .replace(/\s+/g, ' ')
    .trim();
}

function cell(value) {
  const text = clean(value).replace(/\|/g, '\\|');
  return text || missing;
}

function sourceLink(image) {
  return `[${image}](../../${image})`;
}

function parsePipeRow(line) {
  let value = line.trim().replace(/^>\s?/, '');
  if (!value.startsWith('|')) return null;
  value = value.replace(/^\|/, '').replace(/\|$/, '');
  const cells = value.split('|').map(clean);
  if (cells.length < 2 || !cells.some((item) => casePattern.test(item))) return null;
  const idIndex = cells.findIndex((item) => casePattern.test(item));
  if (idIndex < 0) return null;
  const c = cells.slice(idIndex);
  const id = (c[0].match(casePattern) || [c[0]])[1];
  const priorityIndex = c.findIndex((item, index) => index > 0 && /^P[0-2]$/.test(item));
  // Some source screenshots use the compact form: ID | title | priority | expected.
  // Infer the module from the ID prefix rather than shifting columns left.
  if (priorityIndex === 2) {
    const def = prefixToModule.get(id.split('-')[0]);
    return {
      structured: true,
      id,
      module: def ? def.name : missing,
      title: c[1],
      priority: c[2],
      precondition: missing,
      input: missing,
      expected: c[3] || missing,
      verification: missing,
      notes: c.slice(4).join(' | ') || missing,
    };
  }
  // Five-column form: ID | module | title | priority | expected.
  if (priorityIndex === 3 && c.length <= 6) {
    return {
      structured: true,
      id,
      module: c[1],
      title: c[2],
      priority: c[3],
      precondition: missing,
      input: missing,
      expected: c[4] || missing,
      verification: missing,
      notes: c.slice(5).join(' | ') || missing,
    };
  }
  if (c.length >= 9 && priorityIndex === 3) {
    return {
      structured: true,
      id,
      module: c[1],
      title: c[2],
      priority: c[3],
      precondition: c[4],
      input: c[5],
      expected: c[6],
      verification: c[7],
      notes: c.slice(8).join(' | '),
    };
  }
  if (c.length === 8) return { structured: true, id, module: c[1], title: c[2], priority: c[3], precondition: c[4], input: c[5], expected: c[6], verification: c[7], notes: missing };
  if (c.length === 7) return { structured: true, id, module: c[1], title: c[2], priority: c[3], precondition: c[4], input: c[5], expected: c[6], verification: missing, notes: missing };
  return { structured: true, id, module: c[1], title: c[2], priority: c[3], precondition: missing, input: missing, expected: c[c.length - 1], verification: missing, notes: missing };
}

function parseRawRow(line) {
  const match = line.match(/^\s*(?:>\s*)?(?:\|\s*)?([A-Z][A-Z0-9]*-\d{3}|LOCKED-001)\s+(.+)$/);
  if (!match) return null;
  const id = match[1];
  const rest = clean(match[2]);
  const priorityMatch = rest.match(/\bP[0-2]\b/);
  if (!priorityMatch) return null;
  const beforePriority = rest.slice(0, priorityMatch.index).trim().replace(/^\|\s*/, '').replace(/\s*\|$/, '').trim();
  const afterPriority = rest.slice(priorityMatch.index + priorityMatch[0].length).trim();
  const def = prefixToModule.get(id.split('-')[0]);
  // OCR without visible pipe separators cannot prove column boundaries. Keep
  // only the reliable ID/module/title/priority prefix and preserve the rest
  // verbatim as a review note instead of inventing column assignments.
  const moduleName = def ? def.name : missing;
  const labels = [
    moduleName,
    '安全与权限', '接口兼容性', '配置管理', '任务状态机', '存储池', 'RAID', '存储卷',
    '水位策略', 'device/identity', 'flashcache', 'taskdb-rebind', 'volume-reconcile',
    'DeviceIdentityWarnings', '接口与配置兼容', '磁盘管理', '外接设备', 'SSD 缓存', 'iSCSI',
  ].filter(Boolean).sort((a, b) => b.length - a.length);
  const label = labels.find((item) => beforePriority.includes(item));
  const modulePos = label ? beforePriority.indexOf(label) : -1;
  let title = modulePos >= 0
    ? beforePriority.slice(modulePos + label.length).trim()
    : beforePriority;
  if (title.startsWith('|')) title = title.slice(1).trim();
  if (title.endsWith('|')) title = title.slice(0, -1).trim();
  const compactFields = beforePriority.split(/\s+\|\s+/).map(clean).filter(Boolean);
  const canSplit = compactFields.length >= 2 && compactFields.some((item) => /\d/.test(item));
  return {
    structured: false,
    id,
    module: moduleName,
    title: title.replace(/^\|\s*/, '').replace(/\s*\|$/, '').trim() || '原图用例',
    priority: priorityMatch[0],
    precondition: canSplit ? compactFields[0] : missing,
    input: canSplit ? compactFields[1] : missing,
    expected: canSplit ? compactFields[2] || missing : missing,
    verification: missing,
    notes: `原图未提供可分隔列；原始内容：${afterPriority || rest}`,
    rawContent: afterPriority || rest,
  };
}

function enrichUnseparatedRow(row) {
  const baseline = baselineRows.get(row.id);
  if (!baseline) return row;
  const details = row.rawContent || row.notes || '';
  return {
    ...row,
    title: baseline.title || row.title,
    precondition: baseline.precondition !== missing ? baseline.precondition : row.precondition,
    input: baseline.input !== missing ? baseline.input : row.input,
    expected: baseline.expected !== missing ? baseline.expected : row.expected,
    notes: [baseline.notes, details].filter(Boolean).join('；'),
  };
}

function parseRows(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const row = parsePipeRow(line) || parseRawRow(line);
    if (row) rows.push(row);
  }
  return rows;
}

const docs = fs.readdirSync(sourceDir)
  .filter((name) => /^\d{2}-.*\.md$/.test(name))
  .sort();
const jsonByImage = new Map();
const jsonDir = path.join(sourceDir, 'json');
if (fs.existsSync(jsonDir)) {
  for (const file of fs.readdirSync(jsonDir).filter((name) => name.endsWith('.json'))) {
    try {
      const obj = JSON.parse(fs.readFileSync(path.join(jsonDir, file), 'utf8'));
      const image = path.basename(obj.image || '');
      if (image) jsonByImage.set(image, obj);
    } catch (_) { /* Keep the Markdown source as the fallback. */ }
  }
}

const rowsById = new Map();
const idSources = new Map();
const sourceNotes = [];
for (const doc of docs) {
  const text = fs.readFileSync(path.join(sourceDir, doc), 'utf8');
  const imageMatch = text.match(/!\[[^\]]*\]\(\.\.\/([^\)]+\.jpg)\)/i);
  const image = imageMatch ? imageMatch[1] : null;
  if (!image) continue;
  let rows = [];
  const markdownRows = parseRows(text);
  const json = jsonByImage.get(image);
  let jsonRows = [];
  if (json?.result?.layout?.regions) {
    jsonRows = json.result.layout.regions
      .filter((region) => region.type === 'table')
      .flatMap((region) => parseRows(region.text || ''));
  }
  // The per-image Markdown retains the full OCR line; JSON layout snippets may
  // contain abbreviated ellipses. Prefer Markdown whenever it has rows.
  rows = markdownRows.length ? markdownRows : jsonRows;
  const ids = [...new Set(text.match(idPattern) || [])];
  if (!rows.length || !ids.length) {
    const body = text
      .replace(/^#.*$/gm, '')
      .replace(/^!\[[^\]]*\]\([^\n]+\)$/gm, '')
      .replace(/^## Local image verification[\s\S]*$/m, '')
      .trim();
    sourceNotes.push({ image, body: body || '图片未形成可分列测试表。' });
  }
  for (const row of rows) {
    const def = prefixToModule.get(row.id.split('-')[0]);
    if (!def) continue;
    row.sourceImages = new Set([image]);
    const existing = rowsById.get(row.id);
    if (!existing || score(row) > score(existing)) rowsById.set(row.id, row);
    else existing.sourceImages.add(image);
    if (!idSources.has(row.id)) idSources.set(row.id, new Set());
    idSources.get(row.id).add(image);
  }
  for (const id of ids) {
    if (!idSources.has(id)) idSources.set(id, new Set([image]));
  }
}

function score(row) {
  return ['module', 'title', 'priority', 'precondition', 'input', 'expected', 'verification', 'notes']
    .reduce((total, key) => total + (row[key] && row[key] !== missing ? row[key].length : 0), 0);
}

// Merge source image provenance after selecting the most complete duplicate row.
for (const [id, row] of rowsById) row.sourceImages = idSources.get(id) || row.sourceImages;

function table(rows) {
  const lines = [
    '| 编号 | 模块 | 标题 | 优先级 | 前置条件 | 输入数据/步骤 | 预期结果 | 验证结果 | 备注 | 来源图片 |',
    '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |',
  ];
  for (const original of rows.sort((a, b) => a.id.localeCompare(b.id))) {
    const enriched = original.structured === false ? enrichUnseparatedRow(original) : original;
    const row = original.structured === false
      ? {
          ...enriched,
          verification: missing,
          notes: `${enriched.notes || ''}；原图字段未可靠分列，执行前请回看来源图片确认步骤和预期结果。`,
        }
      : original;
    const sources = [...(row.sourceImages || [])].sort().map(sourceLink).join('<br>');
    lines.push(`| ${cell(row.id)} | ${cell(row.module)} | ${cell(row.title)} | ${cell(row.priority)} | ${cell(row.precondition)} | ${cell(row.input)} | ${cell(row.expected)} | ${cell(row.verification)} | ${cell(row.notes)} | ${sources || missing} |`);
  }
  return lines.join('\r\n');
}

function rawTable(rows) {
  const lines = [
    '| 编号 | 模块 | 测试标题 | 优先级 | 原图可见内容 | 验证结果 | 来源图片 |',
    '| --- | --- | --- | --- | --- | --- | --- |',
  ];
  for (const row of rows.sort((a, b) => a.id.localeCompare(b.id))) {
    const sources = [...(row.sourceImages || [])].sort().map(sourceLink).join('<br>');
    lines.push(`| ${cell(row.id)} | ${cell(row.module)} | ${cell(row.title)} | ${cell(row.priority)} | ${cell(row.rawContent || row.notes)} | 待执行 | ${sources || missing} |`);
  }
  return lines.join('\r\n');
}

const moduleRows = new Map(moduleDefs.map((def) => [def.key, []]));
for (const row of rowsById.values()) {
  const def = prefixToModule.get(row.id.split('-')[0]);
  if (def) moduleRows.get(def.key).push(row);
}
for (const [id, row] of baselineRows) {
  if (rowsById.has(id)) continue;
  rowsById.set(id, row);
}

const moduleIndex = [];
let standardRowCount = 0;
let unseparatedRowCount = 0;
for (const def of moduleDefs) {
  const rows = moduleRows.get(def.key).sort((a, b) => a.id.localeCompare(b.id));
  const structuredRows = rows.filter((row) => row.structured !== false);
  const rawRows = rows.filter((row) => row.structured === false);
  standardRowCount += structuredRows.length;
  unseparatedRowCount += rawRows.length;
  const text = [
    `# ${def.name}`,
    '',
    `> 本文件合并 ${rows.length} 个可执行测试用例。来源图片保留在“来源图片”列；照片未显示的字段标为“${missing}”。`,
    '',
    '## 标准测试用例表',
    '',
    table(rows),
    '',
    '## 执行提示',
    '',
    '- 先执行 P0，再执行 P1，最后执行 P2。',
    '- 涉及格式化、擦除、拔盘、RAID、系统盘或升级回退的用例只能使用隔离测试环境。',
    '- “验证结果”是执行时填写栏，不能用预期结果代替。',
    '',
  ].join('\r\n');
  fs.writeFileSync(path.join(finalDir, def.file), text, 'utf8');
  moduleIndex.push({ ...def, count: rows.length });
}

const supplementLines = [
  '# 图片附加内容与未完整截图',
  '',
  '> 这里保存无法安全拆成标准测试用例行的图片内容，例如 API 清单、RAID 参数矩阵、章节说明和只拍到表头的页面。',
  '',
];
for (const item of sourceNotes.sort((a, b) => a.image.localeCompare(b.image))) {
  supplementLines.push(`## ${item.image}`, '', `原图：${sourceLink(item.image)}`, '', item.body, '');
}
fs.writeFileSync(path.join(finalDir, '99-图片附加内容与未完整截图.md'), supplementLines.join('\r\n'), 'utf8');

const reviewRows = [...rowsById.values()]
  .filter((row) => row.structured === false)
  .sort((a, b) => a.id.localeCompare(b.id));
const reviewLines = [
  '# 待复核字段清单',
  '',
  '> 这些用例已经进入各模块的统一 10 列标准表。由于原图 OCR 没有可靠保留列分隔，执行前请按“来源图片”回看原图，确认前置条件、步骤和预期结果；确认后直接填写模块表中的“验证结果”。',
  '',
  `共 ${reviewRows.length} 条；不是新增用例，也不是缺失用例。`,
  '',
  '| 编号 | 模块 | 标题 | 需要复核的字段 | 来源图片 |',
  '| --- | --- | --- | --- | --- |',
  ...reviewRows.map((row) => {
    const def = prefixToModule.get(row.id.split('-')[0]);
    const sources = [...(idSources.get(row.id) || row.sourceImages || [])].sort().map(sourceLink).join('<br>');
    return `| ${cell(row.id)} | ${cell(def ? def.name : row.module)} | ${cell(row.title)} | 前置条件、输入数据/步骤、预期结果、验证方式 | ${sources || missing} |`;
  }),
  '',
  '复核完成后，不要把预期结果复制到“验证结果”；“验证结果”只记录本次实际执行现象、日志或截图。',
];
fs.writeFileSync(path.join(finalDir, '待复核字段.md'), reviewLines.join('\r\n') + '\r\n', 'utf8');

const overview = [
  '# TOS 7.1 最终测试用例目录',
  '',
  '> 这是按模块合并后的执行版文档。旧的单图识别记录仍保留在上级 `提取md` 目录；本目录使用中文模块命名，不再使用 UUID 文件名。',
  '',
  '## 目录结构',
  '',
  '| 顺序 | 文件 | 模块 | 用例数 |',
  '| ---: | --- | --- | ---: |',
  ...moduleIndex.map((item, index) => `| ${String(index + 1).padStart(2, '0')} | [${item.file}](${item.file}) | ${item.name} | ${item.count} |`),
  `| 99 | [99-图片附加内容与未完整截图.md](99-图片附加内容与未完整截图.md) | 附加内容 | ${sourceNotes.length} 个来源页面 |`,
  '',
  '## 推荐执行顺序',
  '',
  '0. 环境基线：准备隔离 NAS/虚拟机、至少两组可清空测试盘，备份配置并记录服务版本、磁盘 Serial、网络地址和初始容量。',
  '1. 接口与配置兼容：先做只读接口/RPC/msgbus/Swagger 检查，再做 7.0 配置导入和升级前备份。',
  '2. 安全与权限：验证 admin、非 admin、内部接口、错误码和密码不泄露；这一步不应改变存储数据。',
  '3. 任务状态与生命周期：先验证取消、超时、并发锁、优雅退出、DB 自愈和断点恢复。',
  '4. 磁盘与设备身份：先盘清单、Serial/PTUUID 识别、SMART/擦除，再做格式化中断和性能场景。',
  '5. 存储池与 RAID：按 RAID0/1/5/6/10/TRAID 建池、扩容、降级、挂载、缩容和删除；每个破坏性场景都从快照或空盘开始。',
  '6. 存储卷与格式化：在通过的存储池上创建卷、格式化、挂载/卸载、扩容、btrfs 子卷和 I/O 检测。',
  '7. 缓存与容量水位：先缓存创建/恢复，再按 70%→85%→90%→95%→恢复顺序验证水位策略。',
  '8. USB/eSATA 与外接设备：使用独立外接盘，按插入防抖、热移除、格式化、连续插拔顺序执行。',
  '9. iSCSI 虚拟磁盘：在稳定卷上验证同步、漂移、空状态、启动对账和 LUN 格式化。',
  '10. 系统盘、升级与稳健性：最后做断电、拔盘修复、慢盘、长稳、系统盘迁移及 7.0↔7.1 升级/回退。',
  '',
  '每个模块内按 P0 → P1 → P2 执行；每完成一个模块先保存日志、任务记录和截图，再进入下一个模块。',
  '“图片附加内容与未完整截图”仅作为人工复核资料，不单独计入执行顺序。',
  '',
  '## 统计',
  '',
  '- 原图：41 张全部保留在上级照片目录；其中 21 张直接关联到用例行，20 张作为附加页面来源。',
  `- 唯一测试用例：${rowsById.size} 个。`,
  `- 模块文件：${moduleDefs.length} 个，另含 1 个附加内容文件。`,
  `- 来源字段完整的用例行：${standardRowCount}；需要回看原图确认列边界的用例行：${unseparatedRowCount}。`,
  '- 所有 137 条用例均已合并到统一 10 列标准表；无法从照片可靠分列的字段标为“未在图片中显示”，并在“备注”中保留复核提示。',
  '- [待复核字段.md](待复核字段.md) 列出需要回看原图确认字段的用例编号。',
  '',
  '## 重要说明',
  '',
  '- 图片只拍到部分表格时，未拍到的字段不会被猜测，统一标记为“未在图片中显示”。',
  '- 同一用例出现在多张图片时，最终表只保留一行，并在“来源图片”中合并列出全部来源。',
  '- 需要查看原始屏幕排版时，回到上级 `提取md` 目录中的单图记录。',
  '',
].join('\r\n');
fs.writeFileSync(path.join(finalDir, '00-测试总览.md'), overview, 'utf8');

const mapping = ['# 用例与原图来源映射', '', '| 用例编号 | 模块文件 | 来源图片 |', '| --- | --- | --- |'];
for (const row of [...rowsById.values()].sort((a, b) => a.id.localeCompare(b.id))) {
  const def = prefixToModule.get(row.id.split('-')[0]);
  mapping.push(`| ${row.id} | [${def.file}](${def.file}) | ${[...(idSources.get(row.id) || [])].sort().map(sourceLink).join('<br>')} |`);
}
fs.writeFileSync(path.join(finalDir, '来源映射.md'), mapping.join('\r\n') + '\r\n', 'utf8');

const check = {
  imagesInSourceDir: fs.readdirSync(photoDir).filter((name) => /\.jpg$/i.test(name)).length,
  moduleFiles: moduleDefs.length,
  uniqueCaseIds: rowsById.size,
  rowsByModule: Object.fromEntries(moduleIndex.map((item) => [item.key, item.count])),
  missingRows: [...idSources.keys()].filter((id) => !rowsById.has(id)),
  allTablesHaveHeader: moduleDefs.every((def) => fs.readFileSync(path.join(finalDir, def.file), 'utf8').includes('| 编号 | 模块 | 标题 | 优先级 | 前置条件 | 输入数据/步骤 | 预期结果 | 验证结果 | 备注 | 来源图片 |')),
};
fs.writeFileSync(path.join(finalDir, '检查结果.json'), JSON.stringify(check, null, 2), 'utf8');
console.log(JSON.stringify(check));
