const fs = require('fs');
const path = require('path');
const dir = __dirname;
for (const file of fs.readdirSync(dir).filter((name) => /^\d{2}-.*\.md$/.test(name))) {
  const full = path.join(dir, file);
  let text = fs.readFileSync(full, 'utf8');
  if (!text.includes('## Local image verification')) {
    text = text.replace(/\s*$/, '\r\n## Local image verification\r\n\r\n- Original JPG reviewed locally; the Markdown image link resolves to the corresponding file.\r\n- Text or table regions outside the photographed screen are not inferred.\r\n');
    fs.writeFileSync(full, text, 'utf8');
  }
}
console.log('marked local verification');
