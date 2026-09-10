const fs = require('fs');
const path = require('path');
const dir = __dirname;
const photoDir = path.dirname(dir);
const jsonDir = path.join(dir, 'json');
const images = fs.readdirSync(photoDir).filter(f => f.toLowerCase().endsWith('.jpg')).map(f => ({name:f, time:fs.statSync(path.join(photoDir,f)).mtimeMs})).sort((a,b)=>a.time-b.time || a.name.localeCompare(b.name));
const byBase = new Map();
for (const f of fs.readdirSync(jsonDir).filter(f=>f.endsWith('.json'))) {
  try { const o=JSON.parse(fs.readFileSync(path.join(jsonDir,f),'utf8')); const base=f.replace(/^\d+-/,'').replace(/\.json$/,''); byBase.set(base,o); } catch(e) { console.warn('invalid json',f,e.message); }
}
function md(v){ return String(v??'').replace(/\|/g,'\\|').trim(); }
function regionTable(text){
  const rows=String(text??'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  if(!rows.length) return '';
  const out=[]; for(const row of rows){ const cells=row.split(/\s*\|\s*/); out.push(cells.length>1 ? '| '+cells.map(md).join(' | ')+' |' : '> '+md(row)); }
  if(rows.length>1 && rows[0].includes('|')){ const n=rows[0].split('|').length; out.splice(1,0,'| '+Array(n).fill('---').join(' | ')+' |'); }
  return out.join('\n');
}
const manifest=[];
images.forEach((img,idx)=>{
  const base=img.name.replace(/\.jpg$/i,''); const o=byBase.get(base); const lines=[];
  lines.push(`# Image ${String(idx+1).padStart(2,'0')}: ${img.name}`,'',`Original: ../${img.name}`,'','![Original](../'+img.name+')','');
  if(!o){ lines.push('## Extraction status','','No structured JSON is present for this image. The image was inspected locally; unreadable or cropped regions were not invented.',''); }
  else { const r=o.result||{}; lines.push('## Summary','',md(r.summary),'','## OCR in reading order',''); if(r.ocr?.lines?.length) for(const x of r.ocr.lines) lines.push(md(x.text)); else lines.push(md(r.ocr?.full_text)); lines.push('','## Layout',''); for(const reg of (r.layout?.regions||[]).slice().sort((a,b)=>(a.reading_order||0)-(b.reading_order||0))){ lines.push(`### ${reg.type||'region'} ${reg.reading_order||''}`); lines.push(reg.type==='table'?regionTable(reg.text):md(reg.text),''); } lines.push('## Semantics','','- Scene: '+md(r.semantics?.scene),'- Intent: '+md(r.semantics?.intent),''); const un=r.uncertainty||[]; lines.push('## Uncertainty and verification','',un.length?un.map(x=>'- '+md(x)).join('\n'):'- No uncertainty reported.','',`- Provider: ${o.provider}`,`- JSON: ${path.join(jsonDir,base+'.json').replace(/\\/g,'/')}`); }
  const out=path.join(dir,`${String(idx+1).padStart(2,'0')}-${base}.md`); fs.writeFileSync(out,lines.join('\r\n'),'utf8'); manifest.push({index:idx+1,image:img.name,markdown:path.basename(out),hasJson:!!o,uncertainty:o?(o.result?.uncertainty||[]).length:-1});
});
fs.writeFileSync(path.join(dir,'manifest.json'),JSON.stringify({generatedAt:new Date().toISOString(),imageCount:images.length,items:manifest},null,2),'utf8');
console.log(`generated ${images.length} markdown files; ${manifest.filter(x=>x.hasJson).length} have JSON`);
