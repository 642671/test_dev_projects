const http = require('http');
const crypto = require('crypto');

// ---- pure-JS DER helpers ----
function readTLV(buf, pos) {
  const tag = buf[pos];
  pos++;
  let len = buf[pos];
  pos++;
  if (len & 0x80) {
    const n = len & 0x7f;
    len = 0;
    for (let i = 0; i < n; i++) len = (len << 8) | buf[pos + i];
    pos += n;
  }
  return { tag, value: buf.subarray(pos, pos + len), next: pos + len };
}
function bufToBig(buf) {
  let h = '';
  for (const b of buf) h += b.toString(16).padStart(2, '0');
  return BigInt('0x' + (h || '0'));
}
function bigToBuf(v, k) {
  let hex = v.toString(16);
  if (hex.length % 2) hex = '0' + hex;
  let b = Buffer.from(hex, 'hex');
  if (b.length < k) b = Buffer.concat([Buffer.alloc(k - b.length), b]);
  return b;
}
function modPow(base, exp, mod) {
  let r = 1n;
  base %= mod;
  while (exp > 0n) {
    if (exp & 1n) r = (r * base) % mod;
    base = (base * base) % mod;
    exp >>= 1n;
  }
  return r;
}

// Parse an SPKI (SubjectPublicKeyInfo) or raw PKCS#1 RSAPublicKey into {n, e, k}
function parsePublicKey(der) {
  const outer = readTLV(der, 0); // SEQUENCE
  if (outer.tag !== 0x30) throw new Error('not SEQUENCE');
  // Heuristic: SPKI if second child is a BIT STRING, else raw PKCS#1
  let rsapub;
  const first = readTLV(outer.value, 0);
  const second = readTLV(outer.value, first.next);
  if (second.tag === 0x03) {
    // SPKI: BIT STRING content begins with unused-bit count byte
    const spk = second.value;
    rsapub = spk.subarray(1);
  } else {
    // raw RSAPublicKey SEQUENCE already
    rsapub = outer.value;
  }
  const seq = readTLV(rsapub, 0);
  if (seq.tag !== 0x30) throw new Error('rsa seq tag ' + seq.tag);
  const nTlv = readTLV(seq.value, 0);
  const eTlv = readTLV(seq.value, nTlv.next);
  const nBig = bufToBig(nTlv.value);
  const eBig = bufToBig(eTlv.value);
  let k = nTlv.value.length;
  if (nTlv.value[0] === 0) k = nTlv.value.length - 1; // strip leading 0x00 sign byte
  return { nBig, eBig, k };
}

function rsaEncryptPkcs1(message, pemOrDer) {
  // Accept either PEM string or DER buffer
  let der;
  if (typeof pemOrDer === 'string') {
    const body = pemOrDer.split(/\r?\n/).filter((l) => l && !l.includes('-----')).join('');
    der = Buffer.from(body, 'base64');
  } else {
    der = pemOrDer;
  }
  const { nBig, eBig, k } = parsePublicKey(der);
  const m = Buffer.from(message, 'utf8');
  if (m.length > k - 11) throw new Error('message too long');
  const psLen = k - 3 - m.length;
  const ps = Buffer.alloc(psLen);
  for (let i = 0; i < psLen; i++) ps[i] = 1 + Math.floor(Math.random() * 255);
  const eb = Buffer.concat([Buffer.from([0x00, 0x02]), ps, Buffer.from([0x00]), m]);
  const mInt = bufToBig(eb);
  const c = modPow(mInt, eBig, nBig);
  return bigToBuf(c, k).toString('base64');
}

async function main() {
  // 1) Validate parser against REAL SPKI key fetched from NAS
  const realDer = await new Promise((resolve, reject) => {
    http.get('http://10.18.15.135:8181/v2/welcome', (res) => {
      const tok = res.headers['x-rsa-token'];
      res.resume();
      if (!tok) return reject(new Error('no token'));
      const pem = Buffer.from(tok, 'base64').toString('utf8');
      const body = pem.split(/\r?\n/).filter((l) => l && !l.includes('-----')).join('');
      resolve(Buffer.from(body, 'base64'));
    }).on('error', reject);
  });
  const parsed = parsePublicKey(realDer);
  const jwk = crypto.createPublicKey({ key: realDer, format: 'der', type: 'spki' }).export({ format: 'jwk' });
  const jwkN = Buffer.from(jwk.n, 'base64url').toString('hex');
  const jwkE = Buffer.from(jwk.e, 'base64url').toString('hex');
  const myN = parsed.nBig.toString(16);
  const myE = parsed.eBig.toString(16);
  console.log('REAL key k bytes:', parsed.k);
  console.log('REAL n match:', jwkN === myN, 'e match:', parseInt(jwkE, 16).toString(16) === myE);
  console.log('REAL e (dec):', parsed.eBig.toString());

  // 2) Round-trip: generate own pair, JS-encrypt, native-decrypt
  const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
  const pubDer = publicKey.export({ type: 'spki', format: 'der' });
  const msg = 'Admin123';
  const cipher = rsaEncryptPkcs1(msg, pubDer);
  const dec = crypto.privateDecrypt(
    { key: privateKey, padding: crypto.constants.RSA_PKCS1_PADDING },
    Buffer.from(cipher, 'base64')
  );
  console.log('ROUNDTRIP decrypt ok:', dec.toString() === msg, 'cipher b64 len:', cipher.length);

  // Also: JS-encrypt the REAL key and verify ciphertext is k bytes (2048-bit => cipher b64 len 344)
  const realCipher = rsaEncryptPkcs1(msg, realDer);
  console.log('REAL cipher b64 len:', realCipher.length, '(expect 344)');
}

main().catch((e) => { console.error('FAIL', e); process.exit(1); });
