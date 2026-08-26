const fs = require('fs');
const path = require('path');

const dir = __dirname;
const photoDir = path.dirname(dir);
const docFiles = fs.readdirSync(dir)
  .filter((name) => /^\d{2}-.*\.md$/.test(name))
  .sort();
const imageFiles = fs.readdirSync(photoDir)
  .filter((name) => /\.jpg$/i.test(name))
  .sort();

const checks = [];
for (const file of docFiles) {
  const fullPath = path.join(dir, file);
  const text = fs.readFileSync(fullPath, 'utf8');
  const imageMatch = text.match(/!\[[^\]]*\]\((\.\/[^(]+|\.\.\/[^)]+\.jpg)\)/i);
  const relativeImage = imageMatch ? imageMatch[1].replace(/^\.\//, '') : null;
  const imagePath = relativeImage ? path.resolve(dir, relativeImage) : null;
  const caseIds = [...new Set(text.match(/\b[A-Z][A-Z0-9]*-\d{3}\b/g) || [])];
  const issues = [];
  if (!imageMatch) issues.push('missing image link');
  if (!imagePath || !fs.existsSync(imagePath)) issues.push('linked image missing');
  if (text.length < 200) issues.push('document too short');
  if (text.includes('\uFFFD')) issues.push('UTF-8 replacement character');
  if (!/OCR|原文提取|Extraction status/.test(text)) issues.push('missing OCR/original extraction section');
  checks.push({
    document: file,
    image: relativeImage,
    imagePresent: Boolean(imagePath && fs.existsSync(imagePath)),
    utf8Replacement: text.includes('\uFFFD'),
    hasExtractionSection: /OCR|原文提取|Extraction status/.test(text),
    characters: text.length,
    caseIds,
    status: issues.length ? 'review' : 'pass',
    issues,
  });
}

const summaryPath = path.join(dir, 'all_modules_summary.md');
const summary = fs.existsSync(summaryPath) ? fs.readFileSync(summaryPath, 'utf8') : '';
const summaryChecks = {
  exists: fs.existsSync(summaryPath),
  hasCompleteness: summary.includes('## Completeness'),
  hasModuleArray: summary.includes('## Module Array'),
  hasImageIndex: summary.includes('## Image Index'),
  hasCaseIdList: summary.includes('## Case ID List'),
};
const stats = {
  images: imageFiles.length,
  markdown: docFiles.length,
  passed: checks.filter((item) => item.status === 'pass').length,
  review: checks.filter((item) => item.status === 'review').length,
  brokenLinks: checks.filter((item) => !item.imagePresent).length,
  utf8Replacement: checks.filter((item) => item.utf8Replacement).length,
  missingExtractionSection: checks.filter((item) => !item.hasExtractionSection).length,
  uniqueCaseIds: new Set(checks.flatMap((item) => item.caseIds)).size,
};
const result = { generatedAt: new Date().toISOString(), stats, summary: summaryChecks, documents: checks };
fs.writeFileSync(path.join(dir, 'verification-report.json'), JSON.stringify(result, null, 2), 'utf8');

const lines = [
  '# Photo Extraction Verification Report',
  '',
  '> Automated local verification after the final document rewrite. Original JPG files were not modified.',
  '',
  '## Totals',
  '',
  '| Check | Result |',
  '| --- | --- |',
  `| JPG images | ${stats.images} |`,
  `| Single-image Markdown | ${stats.markdown} |`,
  `| Passed documents | ${stats.passed} |`,
  `| Documents requiring review | ${stats.review} |`,
  `| Broken image links | ${stats.brokenLinks} |`,
  `| UTF-8 replacement characters | ${stats.utf8Replacement} |`,
  `| Missing extraction sections | ${stats.missingExtractionSection} |`,
  `| Unique case IDs | ${stats.uniqueCaseIds} |`,
  '',
  '## Summary Checks',
  '',
  '| Item | Result |',
  '| --- | --- |',
  ...Object.entries(summaryChecks).map(([key, value]) => `| ${key} | ${value ? 'pass' : 'review'} |`),
  '',
  '## Document Checks',
  '',
  '| Document | Image | IDs | Status | Issues |',
  '| --- | --- | ---: | --- | --- |',
  ...checks.map((item) => `| [${item.document}](${item.document}) | ${item.image || 'missing'} | ${item.caseIds.length} | ${item.status} | ${item.issues.join('; ') || 'none'} |`),
  '',
  '## Interpretation',
  '',
  '- `pass` means the local Markdown has a resolvable JPG link, enough content, valid UTF-8, and an extraction/original-content section.',
  '- A pass does not claim that a blurry or cropped screen region contains text that is not visible; those areas remain marked in the corresponding document when applicable.',
];
fs.writeFileSync(path.join(dir, 'verification-report.md'), lines.join('\r\n') + '\r\n', 'utf8');
console.log(JSON.stringify(stats));
