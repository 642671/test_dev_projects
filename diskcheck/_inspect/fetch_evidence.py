import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding


BASE = "http://10.18.15.135:8181"
OUT = Path(r"D:\test_dev_projects\diskcheck\evidence")
USERNAME = "test"


def request(opener, url, method="GET", body=None, headers=None, timeout=60):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/json, text/plain, */*")
    req.add_header("User-Agent", "Codex-DiskCheck-Evidence/1.0")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), raw
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def main():
    password = os.environ.get("TOS_TEST_PASSWORD", "")
    if not password:
        print("MISSING_PASSWORD")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    status, headers, raw = request(opener, f"{BASE}/tos/", timeout=30)
    if status != 200:
        print(f"BOOTSTRAP_FAILED {status} {raw[:300]!r}")
        return 1

    pub_b64 = headers.get("X-Rsa-Token", "") or headers.get("x-rsa-token", "")
    set_cookie = headers.get("Set-Cookie", "") or headers.get("set-cookie", "")
    csrf_match = re.search(r"(?i)(?:^|;)\s*X-Csrf-Token=([^;]+)", set_cookie)
    csrf = csrf_match.group(1).strip() if csrf_match else ""
    if not csrf:
        csrf = headers.get("X-Csrf-Token", "") or headers.get("x-csrf-token", "")

    if not pub_b64 or not csrf:
        print(f"CONTEXT_MISSING pub={bool(pub_b64)} csrf={bool(csrf)}")
        return 1

    try:
        pem = base64.b64decode(pub_b64, validate=True).decode("utf-8")
        public_key = serialization.load_pem_public_key(pem.encode("utf-8"))
        encrypted = base64.b64encode(
            public_key.encrypt(password.encode("utf-8"), padding.PKCS1v15())
        ).decode("ascii")
    except Exception as exc:
        print(f"RSA_FAILED {type(exc).__name__}: {exc}")
        return 1

    status, headers, raw = request(
        opener,
        f"{BASE}/v2/login",
        method="POST",
        body={
            "username": USERNAME,
            "password": encrypted,
            "code": "",
            "remember": True,
            "slidecode": 1,
        },
        headers={"X-Csrf-Token": csrf},
        timeout=30,
    )
    login_body = raw.decode("utf-8", "replace")
    (OUT / "tos_login_response.json").write_text(
        json.dumps({"status": status, "body": login_body}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"LOGIN_STATUS={status}")
    print(f"LOGIN_BODY={login_body[:400]}")
    if status != 200:
        return 1

    try:
        login_json = json.loads(login_body)
        if not login_json.get("code"):
            print(f"LOGIN_BUSINESS_FAILED {login_json!r}")
            return 1
    except Exception as exc:
        print(f"LOGIN_JSON_FAILED {type(exc).__name__}: {exc}")
        return 1

    endpoints = [
        ("/diskcheck/api/health", "diskcheck_health.json"),
        ("/diskcheck/api/v1/devices", "diskcheck_devices.json"),
        ("/diskcheck/api/v1/jobs", "diskcheck_jobs.json"),
        ("/diskcheck/api/v1/guardian", "diskcheck_guardian.json"),
        ("/diskcheck/api/v1/audit-policy", "diskcheck_audit_policy.json"),
        ("/diskcheck/api/v1/audit-events?limit=1000", "diskcheck_audit_events.json"),
        ("/v2/Initialise/GetDeviceName", "tos_get_device_name.json"),
        ("/v2/desktop/init", "tos_desktop_init.json"),
        ("/v2/system/info", "tos_system_info.json"),
        ("/v2/system/hostname", "tos_hostname.json"),
    ]
    for endpoint, filename in endpoints:
        status, headers, raw = request(opener, f"{BASE}{endpoint}", headers={"X-Csrf-Token": csrf})
        text = raw.decode("utf-8", "replace")
        (OUT / filename).write_text(
            json.dumps({"status": status, "body": text}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{endpoint} STATUS={status} BYTES={len(raw)}")

    devices_text = (OUT / "diskcheck_devices.json").read_text(encoding="utf-8")
    try:
        devices_payload = json.loads(devices_text)
    except Exception:
        devices_payload = {}
    devices_body = devices_payload.get("body", "{}")
    try:
        devices_data = json.loads(devices_body)
    except Exception:
        devices_data = {}
    devices = devices_data.get("devices", [])
    print(f"DEVICE_COUNT={len(devices)}")
    for device in devices:
        device_id = device.get("id") or device.get("device_id")
        if not device_id:
            continue
        endpoint = f"/diskcheck/api/v1/devices/{urllib.parse.quote(str(device_id))}/smart?refresh=1"
        status, headers, raw = request(opener, f"{BASE}{endpoint}", headers={"X-Csrf-Token": csrf})
        filename = f"smart_{device_id}.json"
        (OUT / filename).write_text(
            json.dumps({"status": status, "body": raw.decode("utf-8", "replace")}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"SMART {device_id} STATUS={status} BYTES={len(raw)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
