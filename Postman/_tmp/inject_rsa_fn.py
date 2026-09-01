#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把纯 JS 的 RSA PKCS#1 v1.5 加密函数内联进用到加密的请求前置脚本，
并改为直接调用局部 rsaEncryptPassword，避免依赖集合级 pm 自定义属性。"""
import glob
import os
import yaml

ROOT = r"D:\test_dev_projects\Postman\postman\collections\TEST-TNAS"

FN = r"""var rsaEncryptPassword = function (message, keyInput) {
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
    for (var i = hex.length - 2; i >= 0; i -= 2) { idx--; out[idx] = parseInt(hex.substr(i, 2), 16); }
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
    var rsapub = (second.tag === 0x03) ? second.value.subarray(1) : outer.value;
    var seq = readTLV(rsapub, 0);
    var nTlv = readTLV(seq.value, 0);
    var eTlv = readTLV(seq.value, nTlv.next);
    var nBig = bufToBig(nTlv.value);
    var eBig = bufToBig(eTlv.value);
    var k = nTlv.value.length;
    if (nTlv.value[0] === 0) k = nTlv.value.length - 1;
    return { nBig: nBig, eBig: eBig, k: k };
  }
  function keyBytesDer(keyInput) {
    var key = String(keyInput).trim();
    var pemText = null;
    if (key.indexOf('-----BEGIN') === 0) {
      pemText = key;
    } else {
      var bin = atob(key);
      if (bin.indexOf('-----BEGIN') === 0) pemText = bin;
      else {
        var dr = new Uint8Array(bin.length);
        for (var di = 0; di < bin.length; di++) dr[di] = bin.charCodeAt(di);
        return dr;
      }
    }
    var body = pemText.split(/\r?\n/).filter(function (l) { return l && l.indexOf('-----') < 0; }).join('');
    var b = atob(body);
    var d = new Uint8Array(b.length);
    for (var dj = 0; dj < b.length; dj++) d[dj] = b.charCodeAt(dj);
    return d;
  }
  var der = keyBytesDer(keyInput);
  var pk = parsePublicKey(der);
  var m = [];
  for (var mi = 0; mi < message.length; mi++) m.push(message.charCodeAt(mi) & 0xff);
  if (m.length > pk.k - 11) throw new Error('message too long for RSA');
  var psLen = pk.k - 3 - m.length;
  var rnd = (typeof crypto !== 'undefined' && crypto.getRandomValues) ? function () {
    var a = new Uint32Array(1); crypto.getRandomValues(a); return a[0];
  } : function () { return Math.floor(Math.random() * 0xffffffff); };
  var ps = [];
  for (var pi = 0; pi < psLen; pi++) ps.push(1 + (rnd() % 255));
  var eb = new Uint8Array(pk.k);
  eb[0] = 0x00; eb[1] = 0x02;
  for (var qi = 0; qi < psLen; qi++) eb[2 + qi] = ps[qi];
  eb[2 + psLen] = 0x00;
  for (var ti = 0; ti < m.length; ti++) eb[3 + psLen + ti] = m[ti];
  var c = modPow(bufToBig(eb), pk.eBig, pk.nBig);
  var cbuf = bigToBuf(c, pk.k);
  var b64 = '';
  for (var zi = 0; zi < cbuf.length; zi++) b64 += String.fromCharCode(cbuf[zi]);
  return btoa(b64);
};

"""


def main():
    targets = []
    for path in glob.glob(os.path.join(ROOT, "**", "*.request.yaml"), recursive=True):
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        if "executeAsync" in raw or "rsaEncryptPassword" in raw:
            targets.append(path)

    for path in targets:
        with open(path, "r", encoding="utf-8") as fh:
            d = yaml.safe_load(fh)
        hit = False
        for sc in d.get("scripts") or []:
            if not isinstance(sc, dict) or sc.get("type") != "beforeRequest":
                continue
            code = sc.get("code") or ""
            if "rsaEncryptPassword(" not in code:
                continue
            if "var rsaEncryptPassword = function" in code:
                continue
            # 仅在未内联时注入，并把调用改为局部函数
            code = FN + code
            code = code.replace("pm.rsaEncryptPassword(", "rsaEncryptPassword(")
            sc["code"] = code
            hit = True
        if hit:
            with open(path, "w", encoding="utf-8") as fh:
                yaml.safe_dump(d, fh, allow_unicode=True, sort_keys=False)
            print("injected:", os.path.relpath(path, ROOT))
        else:
            print("  skip:", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
