// minirouter.js — Codex 双路迷你路由（零依赖，无托盘，不碰配置）
//
// 监听 127.0.0.1:15721，替代 CCSwitchMulti 的本地路由器。只做透明转发：
//   1) 模型名以 gpt/o1/o3/o4 开头 -> ChatGPT 官方后端（chatgpt.com/backend-api/codex/responses），
//      经本机 HTTP 代理 127.0.0.1:7897 出网，Authorization 原样透传（Codex 自带的登录凭据）。
//   2) 其它模型（deepseek-*/newapi-*）-> Noontec NewAPI（http://10.18.2.100/v1），
//      Authorization 替换为环境变量 TWM_NEWAPI_API_KEY，可见模型名映射为 NewAPI 真实模型名。
// 请求体只改 model 字段（NewAPI 侧），其余字节原样转发；SSE 流式响应直通。
'use strict';

const http = require('http');
const net = require('net');
const tls = require('tls');
const fs = require('fs');
const zlib = require('zlib');

const LISTEN_HOST = '127.0.0.1';
const LISTEN_PORT = 15721;
const PROXY_HOST = '127.0.0.1';
const PROXY_PORT = 7897;
const OFFICIAL_HOST = 'chatgpt.com';
const OFFICIAL_PROXY_PATH = '/backend-api/codex/responses';
const NEWAPI_HOST = '10.18.2.100';
const NEWAPI_PORT = 80;
const MAX_BODY = 64 * 1024 * 1024; // 64 MB，图片等附件都在内
const CATALOG_PATH = 'C:\\Users\\twm\\.codex\\cc-switch-model-catalog.json';

const OFFICIAL_PREFIXES = ['gpt', 'o1', 'o3', 'o4'];
// 选择器中的可见模型名 -> NewAPI 真实模型名
const NEWAPI_MODEL_MAP = {
  'newapi-deepseek-v4-flash': 'deepseek-v4-flash',
  'newapi-deepseek-v4-flash-vision-exp': 'deepseek-v4-flash-vision-exp',
  'deepseek-v4-flash-noontec-newapi': 'deepseek-v4-flash',
};
const HOP_BY_HOP = new Set([
  'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
  'te', 'trailer', 'transfer-encoding', 'upgrade', 'proxy-connection',
  'content-length', 'host',
]);

// ---------- 请求体解码 ----------
// Codex Desktop 发给本地路由的请求体是 zstd 压缩的（content-encoding: zstd 或裸 zstd 帧）。
// 解压后才能提取 model / 转发到 NewAPI；转发到 ChatGPT 时保留原始字节原样透传。
function decodeBody(buf, contentEncoding) {
  const enc = String(contentEncoding || '').toLowerCase().trim();
  const magic = buf.length >= 4 && buf[0] === 0x28 && buf[1] === 0xb5 && buf[2] === 0x2f && buf[3] === 0xfd;
  if (enc === '' || enc === 'identity') {
    if (magic) return { enc: 'zstd', raw: buf, text: zlib.zstdDecompressSync(buf).toString('utf8') };
    return { enc: null, raw: buf, text: buf.toString('utf8') };
  }
  if (enc === 'zstd') return { enc: 'zstd', raw: buf, text: zlib.zstdDecompressSync(buf).toString('utf8') };
  if (enc === 'gzip') return { enc: 'gzip', raw: buf, text: zlib.gunzipSync(buf).toString('utf8') };
  if (enc === 'deflate') return { enc: 'deflate', raw: buf, text: zlib.inflateSync(buf).toString('utf8') };
  throw new Error('不支持的压缩编码: ' + enc);
}

// ---------- 日志 ----------
const LOG_FILE = 'D:\\test_dev_projects\\docs\\codex-model-integration\\scripts\\minirouter\\router.log';
function log() {
  const t = new Date().toISOString();
  const line = '[' + t + '] ' + Array.prototype.join.call(arguments, ' ');
  console.log(line);
  try { fs.appendFileSync(LOG_FILE, line + '\n'); } catch (e) {}
}

// ---------- 小工具 ----------
function sendText(res, code, text) {
  if (res.headersSent) { res.end(); return; }
  res.writeHead(code, { 'content-type': 'text/plain; charset=utf-8' });
  res.end(text);
}

function readCatalogIds() {
  try {
    const raw = fs.readFileSync(CATALOG_PATH, 'utf8');
    const j = JSON.parse(raw);
    if (Array.isArray(j.models)) {
      const ids = j.models.map((m) => m && m.id).filter((x) => typeof x === 'string');
      if (ids.length > 0) return ids;
    }
  } catch (err) {
    log('catalog 读取失败，使用内置模型列表:', err.message);
  }
  return [
    'gpt-5.4', 'gpt-5.4-mini', 'gpt-5.5',
    'gpt-5.6-luna', 'gpt-5.6-sol', 'gpt-5.6-terra',
    'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp', 'deepseek-v4-pro',
    'newapi-deepseek-v4-flash', 'newapi-deepseek-v4-flash-vision-exp',
  ];
}

function pickHeaders(src, overrides) {
  const out = {};
  for (const [k, v] of Object.entries(src || {})) {
    const lk = k.toLowerCase();
    if (HOP_BY_HOP.has(lk)) continue;
    out[k] = Array.isArray(v) ? v.join(', ') : String(v);
  }
  for (const [k, v] of Object.entries(overrides || {})) out[k] = v;
  return out;
}

function routeFor(name) {
  const m = String(name || '');
  for (const p of OFFICIAL_PREFIXES) {
    if (m.startsWith(p)) return { kind: 'official', visible: m, upstream: m };
  }
  return { kind: 'newapi', visible: m, upstream: NEWAPI_MODEL_MAP[m] || m };
}

// ---------- GET /v1/models ----------
function handleModels(req, res) {
  const ids = readCatalogIds();
  const data = ids.map((id) => ({ id: id, object: 'model', owned_by: 'mini-router', created: 0 }));
  const body = JSON.stringify({ object: 'list', data: data });
  res.writeHead(200, { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) });
  res.end(body);
}

// ---------- NewAPI 转发（纯 HTTP，直连） ----------
function forwardNewapi(serverRes, req, decoded, route) {
  const key = process.env.TWM_NEWAPI_API_KEY || '';
  if (!key) {
    return sendText(serverRes, 500,
      '环境变量 TWM_NEWAPI_API_KEY 未设置。请用 start-minirouter.ps1 启动（它会从注册表补上）。');
  }
  let parsed;
  try { parsed = JSON.parse(decoded.text); } catch (e) {
    log('!!! NewAPI 请求体解析失败:', e.message);
    return sendText(serverRes, 400, '请求体不是 JSON: ' + e.message);
  }
  if (typeof parsed === 'object' && parsed !== null) {
    parsed.model = route.upstream; // 映射到 NewAPI 真实模型名
  }
  const newBody = Buffer.from(JSON.stringify(parsed), 'utf8');
  const pathname = req.url.split('?')[0];
  const headers = pickHeaders(req.headers, {
    host: NEWAPI_HOST + ':' + NEWAPI_PORT,
    authorization: 'Bearer ' + key,
    'content-length': String(newBody.length),
  });
  if (decoded.enc) {
    // 原请求体是压缩的（zstd/gzip），已解压转明文 -> 去掉压缩头，避免 NewAPI 误读
    for (const k of Object.keys(headers)) {
      if (k.toLowerCase() === 'content-encoding') delete headers[k];
    }
  }
  log('POST', pathname, 'visible=' + route.visible, '-> NEWAPI', 'model=' + route.upstream, decoded.enc ? '(解压)' : '');

  const started = Date.now();
  const up = http.request({
    host: NEWAPI_HOST, port: NEWAPI_PORT, path: pathname, method: 'POST', headers: headers,
  }, (upRes) => {
    const out = [];
    for (const [k, v] of Object.entries(upRes.headers)) {
      if (HOP_BY_HOP.has(k.toLowerCase())) continue;
      out.push([k, v]);
    }
    serverRes.writeHead(upRes.statusCode || 502, out);
    upRes.pipe(serverRes);
    serverRes.on('close', () => upRes.destroy());
    log('   <-', upRes.statusCode, '(' + (Date.now() - started) + 'ms)');
  });
  up.setTimeout(600000, () => up.destroy(new Error('upstream timeout 600s')));
  up.on('error', (e) => {
    if (!serverRes.headersSent) sendText(serverRes, 502, 'NewAPI 转发错误: ' + e.message);
    else serverRes.end();
  });
  up.write(newBody);
  up.end();
}

// ---------- 官方转发（CONNECT 过本机代理 -> TLS -> 手动 HTTP 透传） ----------
function forwardOfficial(serverRes, req, bodyBuffer, route) {
  log('POST', req.url.split('?')[0], 'visible=' + route.visible,
    '-> ChatGPT(proxy ' + PROXY_HOST + ':' + PROXY_PORT + ')');
  const started = Date.now();

  const tunnel = net.connect(PROXY_PORT, PROXY_HOST);
  tunnel.setTimeout(15000, () => finish('代理连接超时: ' + PROXY_HOST + ':' + PROXY_PORT));
  tunnel.on('error', (e) => finish('连接代理 ' + PROXY_HOST + ':' + PROXY_PORT + ' 失败: ' + e.message));
  tunnel.on('connect', () => {
    tunnel.write(
      'CONNECT ' + OFFICIAL_HOST + ':443 HTTP/1.1\r\n' +
      'Host: ' + OFFICIAL_HOST + ':443\r\n' +
      'Proxy-Connection: keep-alive\r\n\r\n'
    );
  });

  let buf = '';
  let done = false;
  function finish(msg) {
    if (done) return;
    done = true;
    tunnel.destroy();
    sendText(serverRes, 502, msg);
  }

  tunnel.on('data', (chunk) => {
    buf += chunk.toString('latin1');
    const idx = buf.indexOf('\r\n\r\n');
    if (idx === -1) return;
    const head = buf.slice(0, idx);
    buf = buf.slice(idx + 4);
    tunnel.removeAllListeners('data');
    const m = head.match(/^HTTP\/1\.\d (\d{3})\s/);
    if (!m || Number(m[1]) !== 200) {
      return finish('代理拒绝 CONNECT: ' + head.split('\r\n')[0] + '（检查 127.0.0.1:7897 的代理软件是否在运行）');
    }
    if (tunnel.listenerCount('data')) tunnel.removeAllListeners('data');
    const tlsSocket = tls.connect({ socket: tunnel, servername: OFFICIAL_HOST }, () => {
      const headers = pickHeaders(req.headers, {
        host: OFFICIAL_HOST,
        'content-length': String(bodyBuffer.length),
      });
      let headStr = 'POST ' + OFFICIAL_PROXY_PATH + ' HTTP/1.1\r\n';
      for (const [k, v] of Object.entries(headers)) headStr += k + ': ' + v + '\r\n';
      headStr += '\r\n';
      tlsSocket.write(Buffer.concat([Buffer.from(headStr, 'latin1'), bodyBuffer]));
      tlsSocket.setTimeout(600000, () => { if (!serverRes.writableEnded) serverRes.end(); });
      relayRaw(tlsSocket, serverRes, () => log('   <-', route.visible, '(' + (Date.now() - started) + 'ms)'));
    });
    tlsSocket.on('error', (e) => finish('TLS 到 chatgpt.com 失败: ' + e.message));
  });
  tunnel.on('timeout', () => finish('代理连接超时: ' + PROXY_HOST + ':' + PROXY_PORT));
}

// 手动解析上游响应的头，然后原样透传 body（SSE 逐块直通）
function relayRaw(socket, serverRes, onDone) {
  let headBuf = Buffer.alloc(0);
  let headDone = false;
  socket.on('data', (chunk) => {
    if (headDone) {
      if (!serverRes.writableEnded) serverRes.write(chunk);
      return;
    }
    headBuf = Buffer.concat([headBuf, chunk]);
    const idx = headBuf.indexOf('\r\n\r\n');
    if (idx === -1) return;
    const headStr = headBuf.slice(0, idx).toString('latin1');
    const rest = headBuf.slice(idx + 4);
    headBuf = null;
    headDone = true;
    const lines = headStr.split('\r\n');
    const m = lines[0].match(/^HTTP\/1\.\d (\d{3})/);
    const status = m ? Number(m[1]) : 502;
    if (!m) {
      serverRes.writeHead(502, { 'content-type': 'text/plain' });
      serverRes.end('上游返回异常状态行: ' + lines[0]);
      socket.destroy();
      return;
    }
    const out = [];
    for (const line of lines.slice(1)) {
      const i = line.indexOf(':');
      if (i <= 0) continue;
      const name = line.slice(0, i).trim();
      if (HOP_BY_HOP.has(name.toLowerCase())) continue;
      out.push([name, line.slice(i + 1).trim()]);
    }
    serverRes.writeHead(status, out);
    if (rest.length) serverRes.write(rest);
    socket.removeAllListeners('data');
    socket.on('data', (c) => { if (!serverRes.writableEnded) serverRes.write(c); });
    socket.on('end', () => serverRes.end());
    socket.on('error', () => { if (!serverRes.writableEnded) serverRes.end(); });
    serverRes.on('close', () => socket.destroy());
    if (onDone) serverRes.on('finish', onDone);
  });
  socket.on('end', () => { if (!headDone) sendText(serverRes, 502, '上游在返回头之前断开'); });
}

// ---------- 主服务 ----------
const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url.split('?')[0] === '/v1/models') {
    return handleModels(req, res);
  }
  if (req.method !== 'POST') return sendText(res, 405, 'method not allowed: ' + req.method);
  const pathname = req.url.split('?')[0];
  const chunks = [];
  let size = 0;
  req.on('data', (c) => {
    size += c.length;
    if (size > MAX_BODY) { req.destroy(); return sendText(res, 413, '请求体超过 ' + MAX_BODY + ' 字节'); }
    chunks.push(c);
  });
  req.on('end', () => {
    const body = Buffer.concat(chunks);
    let modelName = '';
    let decoded;
    try {
      decoded = decodeBody(body, req.headers['content-encoding']);
      const j = JSON.parse(decoded.text);
      modelName = j && typeof j.model === 'string' ? j.model : '';
    } catch (e) {
      log('!!! 请求体解析失败 (' + (e.code || '') + ') ' + e.message);
      return sendText(res, 400, '请求体不是 JSON: ' + e.message);
    }
    if (!modelName) return sendText(res, 400, '请求体缺少 model 字段');
    const route = routeFor(modelName);
    if (route.kind === 'official') forwardOfficial(res, req, decoded.raw, route);
    else forwardNewapi(res, req, decoded, route);
  });
  req.on('error', (e) => sendText(res, 400, '读取请求失败: ' + e.message));
});

server.on('error', (e) => {
  if (e && e.code === 'EADDRINUSE') {
    console.error('端口 ' + LISTEN_PORT + ' 已被占用——CCSwitchMulti 或另一个路由器实例还在运行。先退出它再启动。');
  } else {
    console.error('server error:', e);
  }
  process.exit(1);
});

server.listen(LISTEN_PORT, LISTEN_HOST, () => {
  const ids = readCatalogIds();
  log('Mini Codex Router 就绪: http://' + LISTEN_HOST + ':' + LISTEN_PORT + '/v1');
  log('  官方上游: ' + OFFICIAL_HOST + ':' + OFFICIAL_PROXY_PATH + '（经代理 ' + PROXY_HOST + ':' + PROXY_PORT + '，认证透传）');
  log('  NewAPI  : http://' + NEWAPI_HOST + ':' + NEWAPI_PORT + '/v1（key=环境变量 TWM_NEWAPI_API_KEY）');
  log('  ' + ids.length + ' 个模型: ' + ids.join(', '));
  log('  请求体: zstd/gzip 自动解压（兼容 Codex Desktop 的压缩请求）');
});
