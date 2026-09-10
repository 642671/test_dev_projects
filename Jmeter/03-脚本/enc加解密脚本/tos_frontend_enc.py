#!/usr/bin/env python3
"""Reproduce TOS 7 frontend AES-GCM request-body encryption.

The File Share frontend wraps JSON request data as ``{"enc": "..."}`` for
requests without an explicit Content-Type.  The encryption context is derived
from the response ``Date`` and ``X-Rsa-Token`` headers; this utility fetches
those public values by default and never sends or stores login credentials.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


DEFAULT_BOOTSTRAP_PATH = "/v2/lang/FileManager"
NONCE_BYTES = 12
TAG_BYTES = 16


def parse_server_date(value: str) -> datetime:
    """Parse the HTTP Date used by the frontend and normalize it to UTC."""
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        raise ValueError(f"server date must include a timezone: {value!r}")
    return parsed.astimezone(timezone.utc)


def make_salt(public_key: str, server_date: str) -> str:
    """Match the minified frontend's MakeSalt(publicKey) function exactly."""
    utc_date = parse_server_date(server_date)
    hour = utc_date.hour
    minute_bucket = utc_date.minute // 10 * 10
    salted = public_key[:hour] + str(hour) + public_key[hour:]
    return salted[:minute_bucket] + str(minute_bucket) + salted[minute_bucket:]


def derive_key(public_key: str, server_date: str) -> bytes:
    """Return the 32 ASCII bytes used as the AES-256-GCM key."""
    return hashlib.md5(make_salt(public_key, server_date).encode("utf-8")).hexdigest().encode("ascii")


def encode_security_code(server_date: str) -> str:
    """Match ``window.btoa(store.getters.getUtcDate)`` in the frontend."""
    return base64.b64encode(server_date.encode("ascii")).decode("ascii")


def encrypt_text(plaintext: str, public_key: str, server_date: str, *, nonce: bytes | None = None) -> str:
    """Return frontend-compatible hexadecimal ``enc`` text for one JSON string."""
    selected_nonce = nonce if nonce is not None else get_random_bytes(NONCE_BYTES)
    if len(selected_nonce) != NONCE_BYTES:
        raise ValueError(f"AES-GCM nonce must be {NONCE_BYTES} bytes")
    cipher = AES.new(derive_key(public_key, server_date), AES.MODE_GCM, nonce=selected_nonce, mac_len=TAG_BYTES)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    return (selected_nonce + ciphertext + tag).hex()


def decrypt_text(enc: str, public_key: str, server_date: str) -> str:
    """Authenticate and decrypt an ``enc`` value captured from the frontend."""
    try:
        raw = bytes.fromhex(enc)
    except ValueError as exc:
        raise ValueError("enc must be an even-length hexadecimal string") from exc
    if len(raw) < NONCE_BYTES + TAG_BYTES:
        raise ValueError("enc is shorter than an AES-GCM nonce and authentication tag")
    nonce = raw[:NONCE_BYTES]
    ciphertext = raw[NONCE_BYTES:-TAG_BYTES]
    tag = raw[-TAG_BYTES:]
    cipher = AES.new(derive_key(public_key, server_date), AES.MODE_GCM, nonce=nonce, mac_len=TAG_BYTES)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")


def fetch_context(base_url: str, bootstrap_path: str, *, insecure: bool, timeout: float) -> tuple[str, str]:
    """Fetch the public key and server date that a fresh frontend receives."""
    url = f"{base_url.rstrip('/')}/{bootstrap_path.lstrip('/')}"
    response = requests.get(url, headers={"Accept": "application/json, text/plain, */*"}, verify=not insecure, timeout=timeout)
    response.raise_for_status()
    server_date = response.headers.get("Date", "")
    token = response.headers.get("X-Rsa-Token", "")
    if not server_date:
        raise RuntimeError(f"{url} did not return a Date header")
    if not token:
        raise RuntimeError(f"{url} did not return an X-Rsa-Token header")
    try:
        public_key = base64.b64decode(token, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError("X-Rsa-Token is not valid Base64 UTF-8 public-key text") from exc
    return public_key, server_date


def load_context(args: argparse.Namespace) -> tuple[str, str]:
    if args.public_key_file:
        if not args.server_date:
            raise SystemExit("--server-date is required with --public-key-file")
        return args.public_key_file.read_text(encoding="utf-8"), args.server_date
    if args.server_date:
        raise SystemExit("--server-date requires --public-key-file")
    return fetch_context(args.base_url, args.bootstrap_path, insecure=args.insecure, timeout=args.timeout)


def compact_json(raw_json: str) -> str:
    """Validate user input and emit JSON.stringify-compatible compact JSON."""
    try:
        value: Any = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid --json value: {exc}") from exc
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encrypt", "decrypt"))
    parser.add_argument("--base-url", default="https://10.18.8.135:5443", help="TOS base URL used to fetch public encryption context")
    parser.add_argument("--bootstrap-path", default=DEFAULT_BOOTSTRAP_PATH, help=f"public endpoint returning Date and X-Rsa-Token (default: {DEFAULT_BOOTSTRAP_PATH})")
    parser.add_argument("--insecure", action="store_true", help="disable TLS certificate verification for self-signed TOS certificates")
    parser.add_argument("--timeout", type=float, default=15.0, help="bootstrap HTTP timeout in seconds")
    parser.add_argument("--public-key-file", type=Path, help="historical public-key text; requires --server-date")
    parser.add_argument("--server-date", help="historical HTTP Date matching --public-key-file")
    parser.add_argument("--json", help="plaintext JSON object or array to encrypt")
    parser.add_argument("--enc", help="hexadecimal enc value to decrypt")
    parser.add_argument("--show-security-code", action="store_true", help="include the matching X-Security-Code value in encryption output")
    args = parser.parse_args(argv)
    if args.operation == "encrypt" and not args.json:
        parser.error("encrypt requires --json")
    if args.operation == "decrypt" and not args.enc:
        parser.error("decrypt requires --enc")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    public_key, server_date = load_context(args)
    if args.operation == "decrypt":
        print(decrypt_text(args.enc, public_key, server_date))
        return 0

    encrypted = {"enc": encrypt_text(compact_json(args.json), public_key, server_date)}
    if args.show_security_code:
        print(
            json.dumps(
                {"headers": {"X-Security-Code": encode_security_code(server_date)}, "body": encrypted},
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps(encrypted, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
