// zstd-smoke.js — 模拟 Codex Desktop 的 zstd 压缩请求，打给迷你路由
// 用法: node zstd-smoke.js [模型名]
'use strict';
const http = require('http');
const zlib = require('zlib');

const model = process.argv[2] || 'newapi-deepseek-v4-flash';
const body = JSON.stringify({
  model: model,
  input: '回复 OK 两个字',
  max_output_tokens: 8,
});
const comp = zlib.zstdCompressSync(Buffer.from(body, 'utf8'));
console.log('model =', model, '| zstd body:', Buffer.byteLength(body), '->', comp.length, 'bytes');

const req = http.request({
  host: '127.0.0.1', port: 15721, path: '/v1/responses', method: 'POST',
  headers: {
    'content-type': 'application/json',
    'content-encoding': 'zstd',
    'content-length': comp.length,
  },
}, (res) => {
  const chunks = [];
  res.on('data', (c) => chunks.push(c));
  res.on('end', () => {
    console.log('HTTP', res.statusCode);
    console.log(Buffer.concat(chunks).toString('utf8').slice(0, 500));
  });
});
req.on('error', (e) => { console.log('ERR', e.message); process.exit(1); });
req.end(comp);
