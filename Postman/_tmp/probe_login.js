const http = require('http');

function readTLV(buf, pos) {
  var tag = buf[pos]; pos++;
  var len = buf[pos]; pos++;
  if (len & 0x80) { var n = len & 0x7f; len = 0; for (var i = 0; i < n; i++) len = (len << 8) | buf[pos + i]; pos += n; }
  return { tag: tag, value: buf.subarray(pos, pos + len), next: pos + len };
}
function bufToBig(buf) { var h = ''; for (var i = 0; i < buf.length; i++) h += buf[i].toString(16).padStart(2, '0'); return BigInt('0x' + (h || '0')); }
function bigToBuf(v, k) { var hex = v.toString(16); if (hex.length % 2) hex = '0' + hex; var out = new Uint8Array(k); var idx = k; for (var i = hex.length - 2; i >= 0; i -= 2) { idx--; out[idx] = parseInt(hex.substr(i, 2), 16); } return out; }
function modPow(b, e, m) { var r = 1n; b %= m; while (e > 0n) { if (e & 1n) r = (r * b) % m; b = (b * b) % m; e >>= 1n; } return r; }
function parsePublicKey(der) {
  var outer = readTLV(der, 0); var first = readTLV(outer.value, 0); var second = readTLV(outer.value, first.next);
  var rsapub = (second.tag === 0x03) ? second.value.subarray(1) : outer.value;
  var seq = readTLV(rsapub, 0); var nTlv = readTLV(seq.value, 0); var eTlv = readTLV(seq.value, nTlv.next);
  var nBig = bufToBig(nTlv.value); var eBig = bufToBig(eTlv.value);
  var k = nTlv.value.length; if (nTlv.value[0] === 0) k = nTlv.value.length - 1;
  return { nBig: nBig, eBig: eBig, k: k };
}
function keyBytesDer(keyInput) {
  var key = String(keyInput).trim(); var pemText = null;
  if (key.indexOf('-----BEGIN') === 0) pemText = key;
  else {
    var bin = atob(key);
    if (bin.indexOf('-----BEGIN') === 0) pemText = bin;
    else { var dr = new Uint8Array(bin.length); for (var di = 0; di < bin.length; di++) dr[di] = bin.charCodeAt(di); return dr; }
  }
  var body = pemText.split(/\r?\n/).filter(function (l) { return l && l.indexOf('-----') < 0; }).join('');
  var b = atob(body); var d = new Uint8Array(b.length); for (var dj = 0; dj < b.length; dj++) d[dj] = b.charCodeAt(dj); return d;
}
function rsaEncrypt(message, keyInput) {
  var der = keyBytesDer(keyInput);
  var pk = parsePublicKey(der);
  var m = []; for (var j = 0; j < message.length; j++) m.push(message.charCodeAt(j) & 0xff);
  var psLen = pk.k - 3 - m.length; var ps = []; for (var p = 0; p < psLen; p++) ps.push(1 + ((Math.random() * 255) | 0));
  var eb = new Uint8Array(pk.k); eb[0] = 0; eb[1] = 2; for (var q = 0; q < psLen; q++) eb[2 + q] = ps[q]; eb[2 + psLen] = 0;
  for (var t = 0; t < m.length; t++) eb[3 + psLen + t] = m[t];
  var c = modPow(bufToBig(eb), pk.eBig, pk.nBig); var cbuf = bigToBuf(c, pk.k);
  var b64 = ''; for (var z = 0; z < cbuf.length; z++) b64 += String.fromCharCode(cbuf[z]); return btoa(b64);
}
function get(path, headers) {
  return new Promise((resolve) => {
    http.get({ host: '10.18.15.135', port: 8181, path: path, headers: headers || {} }, (res) => {
      let data = ''; res.on('data', (c) => data += c); res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    }).on('error', (e) => resolve({ error: e.message }));
  });
}
function post(path, headers, body) {
  return new Promise((resolve) => {
    const req = http.request({ host: '10.18.15.135', port: 8181, path: path, method: 'POST', headers: headers }, (res) => {
      let data = ''; res.on('data', (c) => data += c); res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', (e) => resolve({ error: e.message })); req.end(body);
  });
}
function cookieVal(setCookie, name) {
  if (!setCookie) return null;
  if (Array.isArray(setCookie)) setCookie = setCookie.join('\n');
  var m = setCookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
  return m ? m[1] : null;
}

(async () => {
  const lang = await get('/v2/lang/tos');
  let langCsrf = cookieVal(lang.headers['set-cookie'], 'X-Csrf-Token');
  console.log('lang status', lang.status, 'lang csrf set', !!langCsrf);
  const wel = await get('/v2/welcome');
  let setCookies = wel.headers['set-cookie'];
  let pubB64 = wel.headers['x-rsa-token'];
  console.log('welcome status', wel.status, 'rsa b64 len', (pubB64 || '').length);
  // 传 base64(PEM)（即 X-Rsa-Token 原值），模拟集合脚本现在的传参
  const enc = rsaEncrypt('Admin123', pubB64);
  const payload = JSON.stringify({ username: 'test', password: enc, code: '', remember: true, slidecode: 1 });
  const csrf = langCsrf;
  const login = await post('/v2/login', { 'content-type': 'application/json', 'x-csrf-token': csrf }, payload);
  console.log('login status', login.status, 'rsa len', enc.length);
  console.log('--- login Set-Cookie ---');
  let lsc = login.headers['set-cookie'];
  console.log(Array.isArray(lsc) ? lsc.join('\n') : (lsc || '(none)'));
  console.log('--- body ---'); console.log(login.body.slice(0, 300));
})();
