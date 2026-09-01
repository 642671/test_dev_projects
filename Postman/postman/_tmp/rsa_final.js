// Standalone copy of the function that will be injected as pm.rsaEncryptPassword
function buildRsaEncrypt(scope) {
  scope.rsaEncryptPassword = function (message, keyInput) {
    function readTLV(buf, pos) {
      var tag = buf[pos]; pos++;
      var len = buf[pos]; pos++;
      if (len & 0x80) {
        var n = len & 0x7f;
        len = 0;
        for (var i = 0; i < n; i++) len = (len << 8) | buf[pos + i];
        pos += n;
      }
      return { tag: tag, value: buf.subarray(pos, pos + len), next: pos + len };
    }
    function bufToBig(buf) {
      var h = '';
      for (var i = 0; i < buf.length; i++) h += buf[i].toString(16).padStart(2, '0');
      return BigInt('0x' + (h || '0'));
    }
    function bigToBuf(v, k) {
      var hex = v.toString(16);
      if (hex.length % 2) hex = '0' + hex;
      var out = new Uint8Array(k);
      var idx = k;
      for (var i = hex.length - 2; i >= 0; i -= 2) {
        idx--;
        out[idx] = parseInt(hex.substr(i, 2), 16);
      }
      return out;
    }
    function modPow(base, exp, mod) {
      var r = 1n; base %= mod;
      while (exp > 0n) {
        if (exp & 1n) r = (r * base) % mod;
        base = (base * base) % mod;
        exp >>= 1n;
      }
      return r;
    }
    function parsePublicKey(der) {
      var outer = readTLV(der, 0);
      var first = readTLV(outer.value, 0);
      var second = readTLV(outer.value, first.next);
      var rsapub;
      if (second.tag === 0x03) {
        rsapub = second.value.subarray(1);
      } else {
        rsapub = outer.value;
      }
      var seq = readTLV(rsapub, 0);
      var nTlv = readTLV(seq.value, 0);
      var eTlv = readTLV(seq.value, nTlv.next);
      var nBig = bufToBig(nTlv.value);
      var eBig = bufToBig(eTlv.value);
      var k = nTlv.value.length;
      if (nTlv.value[0] === 0) k = nTlv.value.length - 1;
      return { nBig: nBig, eBig: eBig, k: k };
    }

    var key = String(keyInput).trim();
    var body;
    if (key.indexOf('-----BEGIN') === 0) {
      body = key.split(/\r?\n/).filter(function (l) { return l && l.indexOf('-----') < 0; }).join('');
    } else {
      body = key;
    }
    var bin = atob(body);
    var der = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) der[i] = bin.charCodeAt(i);

    var pk = parsePublicKey(der);
    var m = [];
    for (var j = 0; j < message.length; j++) m.push(message.charCodeAt(j) & 0xff);
    if (m.length > pk.k - 11) throw new Error('message too long for RSA');
    var psLen = pk.k - 3 - m.length;
    var ps = [];
    var rnd = (typeof crypto !== 'undefined' && crypto.getRandomValues) ? function () {
      var a = new Uint32Array(1); crypto.getRandomValues(a); return a[0];
    } : function () { return Math.floor(Math.random() * 0xffffffff); };
    for (var p = 0; p < psLen; p++) ps.push(1 + (rnd() % 255));
    var eb = new Uint8Array(pk.k);
    eb[0] = 0x00; eb[1] = 0x02;
    for (var q = 0; q < psLen; q++) eb[2 + q] = ps[q];
    eb[2 + psLen] = 0x00;
    for (var t = 0; t < m.length; t++) eb[3 + psLen + t] = m[t];

    var c = modPow(bufToBig(eb), pk.eBig, pk.nBig);
    var cbuf = bigToBuf(c, pk.k);
    var b64 = '';
    for (var z = 0; z < cbuf.length; z++) b64 += String.fromCharCode(cbuf[z]);
    return btoa(b64);
  };
}

// ---- test ----
const http = require('http');
const crypto = require('crypto');
const scope = {};
buildRsaEncrypt(scope);

function base64UrlToBuf(s) { return Buffer.from(s, 'base64url'); }

async function main() {
  const realDer = await new Promise((resolve, reject) => {
    http.get('http://10.18.15.135:8181/v2/welcome', (res) => {
      const tok = res.headers['x-rsa-token']; res.resume();
      if (!tok) return reject(new Error('no token'));
      const pem = Buffer.from(tok, 'base64').toString('utf8');
      const body = pem.split(/\r?\n/).filter((l) => l && !l.includes('-----')).join('');
      resolve(Buffer.from(body, 'base64'));
    }).on('error', reject);
  });

  // Verify the injected-style function works on a PEM input (base64 of PEM)
  const keyB64 = realDer.toString('base64'); // base64 of DER, but pass as base64 to function -> decode -> der
  const cipherReal = scope.rsaEncryptPassword('Admin123', keyB64);
  console.log('REAL cipher b64 len:', cipherReal.length, '(expect 344)');

  // Round-trip with generated key
  const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
  const pubDer = publicKey.export({ type: 'spki', format: 'der' });
  const cipher = scope.rsaEncryptPassword('Admin123', pubDer.toString('base64'));
  const dec = crypto.privateDecrypt(
    { key: privateKey, padding: crypto.constants.RSA_PKCS1_PADDING },
    Buffer.from(cipher, 'base64')
  );
  console.log('ROUNDTRIP decrypt ok:', dec.toString() === 'Admin123');

  // Also test PEM-string input path
  const pubPem = publicKey.export({ type: 'spki', format: 'pem' });
  const cipher2 = scope.rsaEncryptPassword('Admin123', pubPem);
  const dec2 = crypto.privateDecrypt(
    { key: privateKey, padding: crypto.constants.RSA_PKCS1_PADDING },
    Buffer.from(cipher2, 'base64')
  );
  console.log('PEM input decrypt ok:', dec2.toString() === 'Admin123');
}

main().catch((e) => { console.error('FAIL', e); process.exit(1); });
