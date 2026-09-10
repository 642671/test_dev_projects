const http = require("http");

const host = process.env.TOS_HOST || "10.18.15.136";
const port = Number(process.env.TOS_PORT || "8181");
const username = process.env.TOS_USER || "test";
const password = process.env.TOS_PASSWORD;

function request(method, path, headers = {}, body = null, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        host,
        port,
        path,
        method,
        headers,
      },
      (res) => {
        let data = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: data,
          });
        });
      },
    );

    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error(`request timed out: ${method} ${path}`));
    });
    req.on("error", reject);
    if (body) {
      req.write(body);
    }
    req.end();
  });
}

function cookieValue(setCookie, name) {
  if (!setCookie) {
    return null;
  }
  const values = Array.isArray(setCookie) ? setCookie : [setCookie];
  for (const value of values) {
    const match = value.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`, "i"));
    if (match) {
      return match[1];
    }
  }
  return null;
}

function readTlv(buf, pos) {
  const tag = buf[pos++];
  let len = buf[pos++];
  if (len & 0x80) {
    const count = len & 0x7f;
    len = 0;
    for (let i = 0; i < count; i++) {
      len = (len << 8) | buf[pos + i];
    }
    pos += count;
  }
  return {
    tag,
    value: buf.subarray(pos, pos + len),
    next: pos + len,
  };
}

function bufferToBig(buf) {
  let hex = "";
  for (let i = 0; i < buf.length; i++) {
    hex += buf[i].toString(16).padStart(2, "0");
  }
  return BigInt(`0x${hex || "0"}`);
}

function bigToBuffer(value, size) {
  let hex = value.toString(16);
  if (hex.length % 2) {
    hex = `0${hex}`;
  }
  const out = new Uint8Array(size);
  let index = size;
  for (let i = hex.length - 2; i >= 0; i -= 2) {
    index--;
    out[index] = parseInt(hex.substr(i, 2), 16);
  }
  return out;
}

function modPow(base, exponent, modulus) {
  let result = 1n;
  let b = base % modulus;
  let e = exponent;
  while (e > 0n) {
    if (e & 1n) {
      result = (result * b) % modulus;
    }
    b = (b * b) % modulus;
    e >>= 1n;
  }
  return result;
}

function parsePublicKey(der) {
  const outer = readTlv(der, 0);
  const first = readTlv(outer.value, 0);
  const second = readTlv(outer.value, first.next);
  const rsaPub =
    second.tag === 0x03 ? second.value.subarray(1) : outer.value;
  const seq = readTlv(rsaPub, 0);
  const nTlv = readTlv(seq.value, 0);
  const eTlv = readTlv(seq.value, nTlv.next);
  const nBig = bufferToBig(nTlv.value);
  const eBig = bufferToBig(eTlv.value);
  let keySize = nTlv.value.length;
  if (nTlv.value[0] === 0) {
    keySize = nTlv.value.length - 1;
  }
  return { nBig, eBig, keySize };
}

function keyBytesDer(keyInput) {
  const key = String(keyInput).trim();
  if (key.startsWith("-----BEGIN")) {
    const body = key
      .split(/\r?\n/)
      .filter((line) => line && !line.startsWith("-----"))
      .join("");
    const binary = atob(body);
    const der = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      der[i] = binary.charCodeAt(i);
    }
    return der;
  }
  const binary = atob(key);
  if (binary.startsWith("-----BEGIN")) {
    return keyBytesDer(binary);
  }
  const der = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    der[i] = binary.charCodeAt(i);
  }
  return der;
}

function encryptPassword(plain, rsaToken) {
  const der = keyBytesDer(rsaToken);
  const pk = parsePublicKey(der);
  const message = [];
  for (let i = 0; i < plain.length; i++) {
    message.push(plain.charCodeAt(i) & 0xff);
  }
  const paddingSize = pk.keySize - 3 - message.length;
  const padded = new Uint8Array(pk.keySize);
  padded[0] = 0;
  padded[1] = 2;
  for (let i = 0; i < paddingSize; i++) {
    padded[2 + i] = 1 + ((Math.random() * 255) | 0);
  }
  padded[2 + paddingSize] = 0;
  for (let i = 0; i < message.length; i++) {
    padded[3 + paddingSize + i] = message[i];
  }
  const cipher = modPow(bufferToBig(padded), pk.eBig, pk.nBig);
  const cipherBytes = bigToBuffer(cipher, pk.keySize);
  let binary = "";
  for (let i = 0; i < cipherBytes.length; i++) {
    binary += String.fromCharCode(cipherBytes[i]);
  }
  return btoa(binary);
}

function jsonBody(response) {
  try {
    return JSON.parse(response.body);
  } catch {
    return null;
  }
}

function printDisk(disk, label = "DISK") {
  const device = disk.device || disk.path || disk.DEVNAME || "";
  const line = {
    device,
    name: disk.name || disk.display_name || "",
    slot: disk.slot || disk.slot_no || disk.index || "",
    serial: disk.serial || disk.IDSerial || "",
    model: disk.model || disk.product || "",
    type: disk.type || disk.device_type || "",
    capacity: disk.capacity || disk.size || "",
  };
  if (
    device.includes("sdj") ||
    label === "ALL" ||
    label === "STATUS" ||
    label === "OVERVIEW"
  ) {
    console.log(label, JSON.stringify(line));
  }
}

async function main() {
  if (!password) {
    throw new Error("TOS_PASSWORD is required");
  }

  const lang = await request("GET", "/tos/");
  let csrf = cookieValue(lang.headers["set-cookie"], "X-Csrf-Token");

  const welcomeHeaders = {};
  if (csrf) {
    welcomeHeaders["X-Csrf-Token"] = csrf;
  }
  const welcome = await request("GET", "/v2/welcome", welcomeHeaders);
  const rsaToken = welcome.headers["x-rsa-token"];
  if (!rsaToken) {
    throw new Error("welcome did not return X-Rsa-Token");
  }
  csrf = cookieValue(welcome.headers["set-cookie"], "X-Csrf-Token") || csrf;

  const encryptedPassword = encryptPassword(password, rsaToken);
  console.log("BOOTSTRAP_STATUS", lang.status);
  console.log("WELCOME_STATUS", welcome.status);
  console.log("CSRF_PRESENT", !!csrf);
  console.log("RSA_KEY_PRESENT", !!rsaToken);
  console.log("ENCRYPTED_PASSWORD_LENGTH", encryptedPassword.length);
  const loginBody = JSON.stringify({
    username,
    password: encryptedPassword,
    code: "",
    remember: true,
    slidecode: 1,
  });
  const loginHeaders = {
    "content-type": "application/json",
  };
  if (csrf) {
    loginHeaders["X-Csrf-Token"] = csrf;
    loginHeaders.cookie = `X-Csrf-Token=${csrf}`;
  }

  const login = await request("POST", "/v2/login", loginHeaders, loginBody);
  const loginJson = jsonBody(login);
  console.log("LOGIN_STATUS", login.status);
  if (login.status !== 200 || !loginJson || loginJson.code !== true) {
    console.log("LOGIN_BODY", login.body.slice(0, 300));
    throw new Error("TOS login failed");
  }

  const session = cookieValue(login.headers["set-cookie"], "TMSESSNAME");
  const loginCsrf = cookieValue(login.headers["set-cookie"], "X-Csrf-Token");
  const currentUser = cookieValue(login.headers["set-cookie"], "tos_current_username");
  csrf = loginCsrf || csrf;

  const cookieParts = [];
  if (csrf) {
    cookieParts.push(`X-Csrf-Token=${csrf}`);
  }
  if (session) {
    cookieParts.push(`TMSESSNAME=${session}`);
  }
  if (currentUser) {
    cookieParts.push(`tos_current_username=${currentUser}`);
    cookieParts.push(`userName=${currentUser}`);
  }
  cookieParts.push("loginStatus=true");
  const cookie = cookieParts.join("; ");

  const authHeaders = {
    "content-type": "application/json",
    cookie,
    "X-Csrf-Token": csrf,
  };

  const diskList = await request(
    "GET",
    "/v2/disk/GetDiskListData",
    authHeaders,
  );
  const parsed = jsonBody(diskList);
  console.log("DISK_LIST_STATUS", diskList.status);
  if (parsed && parsed.data) {
    const disks = Array.isArray(parsed.data) ? parsed.data : [parsed.data];
    disks.forEach(printDisk);
    console.log("DISK_LIST_COUNT", disks.length);
    disks.forEach((disk) => printDisk(disk, "ALL"));
  } else {
    console.log("DISK_LIST_BODY", diskList.body.slice(0, 1000));
  }

  const diskStatus = await request(
    "GET",
    "/v2/disk/GetDiskStatus",
    authHeaders,
  );
  const statusParsed = jsonBody(diskStatus);
  console.log("DISK_STATUS_STATUS", diskStatus.status);
  if (statusParsed && statusParsed.data) {
    const disks = Array.isArray(statusParsed.data)
      ? statusParsed.data
      : [statusParsed.data];
    disks.forEach(printDisk);
    console.log("DISK_STATUS_COUNT", disks.length);
    disks.forEach((disk) => printDisk(disk, "STATUS"));
  } else {
    console.log("DISK_STATUS_BODY", diskStatus.body.slice(0, 1000));
  }

  const overview = await request(
    "GET",
    "/v2/disk/GetOverview",
    authHeaders,
  );
  const overviewParsed = jsonBody(overview);
  console.log("OVERVIEW_STATUS", overview.status);
  if (overviewParsed && overviewParsed.data) {
    const data = Array.isArray(overviewParsed.data)
      ? overviewParsed.data
      : [overviewParsed.data];
    data.forEach(printDisk);
    console.log("OVERVIEW_COUNT", data.length);
    data.forEach((disk) => printDisk(disk, "OVERVIEW"));
  } else {
    console.log("OVERVIEW_BODY", overview.body.slice(0, 1000));
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
