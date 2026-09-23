#!/usr/bin/env python3
"""Clone the active Noontec NewAPI provider and switch it to a new API key.

The active provider keeps its original provider ID so all existing routes and
compatibility records continue to work. A copy with the old key is retained as
a separate provider for later use.
"""

from __future__ import annotations

import argparse
import getpass
import json
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(r"C:\Users\twm\.cc-switch\cc-switch.db")
BACKUP_ROOT = Path(r"C:\Users\twm\.cc-switch\backups")
CONFIG_PATH = Path(r"C:\Users\twm\.codex\config.toml")
CATALOG_PATH = Path(r"C:\Users\twm\.codex\cc-switch-model-catalog.json")
SETTINGS_PATH = Path(r"C:\Users\twm\.cc-switch\settings.json")

SOURCE_PROVIDER_ID = "universal-codex-950cc769853e4620b148532ead68beb2"
ROUTER_PROVIDER_ID = "codex-multirouter"
ROUTE_ID = "router-universal-codex-newapi-noontec"
BACKUP_PROVIDER_ID = "universal-codex-newapi-noontec-old-key-20260923"

ACTIVE_PROVIDER_NAME = "Noontec NewAPI (New Key)"
BACKUP_PROVIDER_NAME = "Noontec NewAPI (Old Key)"

CHECK_URL = "http://10.18.2.100/v1/responses"
CHECK_MODEL = "deepseek-v4-flash"
CHECK_TEXT = "KEY_CHECK_OK"


def now_ms() -> int:
    return int(time.time() * 1000)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_key() -> str:
    key = getpass.getpass("New NewAPI key (hidden): ").strip()
    if not key:
        raise RuntimeError("empty API key")
    if not key.startswith("sk-"):
        raise RuntimeError("API key does not start with sk-")
    return key


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=30000")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def extract_response_text(body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return ""

    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return " ".join(chunks).strip()


def check_key(api_key: str) -> tuple[int, bool]:
    payload = {
        "model": CHECK_MODEL,
        "input": f"Reply with exactly {CHECK_TEXT}.",
        "reasoning": {"effort": "max"},
        "stream": False,
        "store": False,
    }
    request = urllib.request.Request(
        CHECK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=120) as response:
            status = int(response.status)
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        status = int(error.code)
        body = error.read().decode("utf-8", errors="replace")
        return status, False

    text = extract_response_text(body)
    semantic_ok = CHECK_TEXT.casefold() in text.casefold()
    print(f"key_check_response_length={len(text)}")
    print(f"key_check_response_preview={text[:160]!r}")
    return status, semantic_ok


def provider_row(connection: sqlite3.Connection, provider_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM providers WHERE id=? AND app_type='codex'",
        (provider_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"provider not found: {provider_id}")
    return row


def parse_json_object(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid JSON in {label}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object in {label}")
    return value


def insert_provider_copy(
    connection: sqlite3.Connection,
    source: sqlite3.Row,
    backup_provider_id: str,
    backup_provider_name: str,
) -> None:
    columns = [
        row["name"]
        for row in connection.execute("PRAGMA table_info(providers)")
    ]
    values = dict(source)
    values["id"] = backup_provider_id
    values["name"] = backup_provider_name
    values["created_at"] = now_ms()
    values["is_current"] = 0
    values["in_failover_queue"] = 0
    values["notes"] = (
        "Old API key retained for later use. "
        "The active provider keeps the original provider ID and routes."
    )
    if values.get("sort_index") is not None:
        values["sort_index"] = int(values["sort_index"]) + 1

    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(f'"{column}"' for column in columns)
    connection.execute(
        f"INSERT INTO providers ({column_sql}) VALUES ({placeholders})",
        [values[column] for column in columns],
    )


def update_active_provider(
    connection: sqlite3.Connection,
    provider_id: str,
    api_key: str,
) -> None:
    notes = (
        "New API key activated on 2026-09-23. "
        "Old-key provider: universal-codex-newapi-noontec-old-key-20260923."
    )
    cursor = connection.execute(
        """
        UPDATE providers
        SET name=?,
            notes=?,
            settings_config=json_set(
                settings_config,
                '$.auth.OPENAI_API_KEY',
                ?
            )
        WHERE id=? AND app_type='codex'
        """,
        (ACTIVE_PROVIDER_NAME, notes, api_key, provider_id),
    )
    if cursor.rowcount != 1:
        raise RuntimeError("active provider update did not affect exactly one row")


def update_router_and_projection(connection: sqlite3.Connection) -> None:
    router = provider_row(connection, ROUTER_PROVIDER_ID)
    router_config = parse_json_object(
        router["settings_config"],
        "codex-multirouter.settings_config",
    )

    routes = router_config.get("codexRouting", {}).get("routes", [])
    matching_routes = [
        route
        for route in routes
        if route.get("id") == ROUTE_ID
        and route.get("targetProviderId") == SOURCE_PROVIDER_ID
    ]
    if len(matching_routes) != 1:
        raise RuntimeError(
            "expected exactly one matching NewAPI route, "
            f"found {len(matching_routes)}"
        )
    matching_routes[0]["label"] = ACTIVE_PROVIDER_NAME

    connection.execute(
        "UPDATE providers SET settings_config=? WHERE id=? AND app_type='codex'",
        (
            json.dumps(router_config, ensure_ascii=False, separators=(",", ":")),
            ROUTER_PROVIDER_ID,
        ),
    )

    projection_key = f"codex_multirouter_projection:{ROUTER_PROVIDER_ID}"
    projection_row = connection.execute(
        "SELECT value FROM settings WHERE key=?",
        (projection_key,),
    ).fetchone()
    if projection_row is None:
        raise RuntimeError(f"projection setting not found: {projection_key}")

    projection = parse_json_object(projection_row["value"], projection_key)
    projection_matches = 0
    for route in projection.get("routes", []):
        if (
            route.get("routeId") == ROUTE_ID
            and route.get("targetProviderId") == SOURCE_PROVIDER_ID
        ):
            route["routeLabel"] = ACTIVE_PROVIDER_NAME
            route["targetProviderName"] = ACTIVE_PROVIDER_NAME
            projection_matches += 1
    if projection_matches == 0:
        raise RuntimeError("no matching route in codex multirouter projection")
    projection["generatedAt"] = utc_now()

    connection.execute(
        "UPDATE settings SET value=? WHERE key=?",
        (
            json.dumps(projection, ensure_ascii=False, separators=(",", ":")),
            projection_key,
        ),
    )


def compare_clone_payload(active: dict, backup: dict) -> bool:
    ignored = {"id", "name", "created_at", "sort_index", "notes", "auth"}
    active_copy = dict(active)
    backup_copy = dict(backup)
    for value in (active_copy, backup_copy):
        value.pop("auth", None)
        for key in ignored:
            value.pop(key, None)
    return json.dumps(active_copy, sort_keys=True) == json.dumps(
        backup_copy,
        sort_keys=True,
    )


def create_backup_snapshot() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_ROOT / f"newapi-new-key-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    source = sqlite3.connect(DB_PATH, timeout=30)
    destination = sqlite3.connect(backup_dir / "cc-switch.db")
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    for source_path in (CONFIG_PATH, CATALOG_PATH, SETTINGS_PATH):
        if source_path.exists():
            shutil.copy2(source_path, backup_dir / source_path.name)

    return backup_dir


def apply_change(api_key: str) -> dict:
    active_before = provider_row(connect_db(), SOURCE_PROVIDER_ID)
    active_settings_before = parse_json_object(
        active_before["settings_config"],
        "active provider settings_config",
    )
    old_key = (
        active_settings_before.get("auth", {}).get("OPENAI_API_KEY", "")
    )
    if not old_key:
        raise RuntimeError("active provider has no OPENAI_API_KEY")

    backup_dir = create_backup_snapshot()
    connection = connect_db()
    try:
        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            "SELECT 1 FROM providers WHERE id=? AND app_type='codex'",
            (BACKUP_PROVIDER_ID,),
        ).fetchone()
        if existing is not None:
            raise RuntimeError(f"backup provider already exists: {BACKUP_PROVIDER_ID}")

        source = provider_row(connection, SOURCE_PROVIDER_ID)
        insert_provider_copy(
            connection,
            source,
            BACKUP_PROVIDER_ID,
            BACKUP_PROVIDER_NAME,
        )
        update_active_provider(connection, SOURCE_PROVIDER_ID, api_key)
        update_router_and_projection(connection)

        active_after = provider_row(connection, SOURCE_PROVIDER_ID)
        backup_after = provider_row(connection, BACKUP_PROVIDER_ID)
        active_settings = parse_json_object(
            active_after["settings_config"],
            "active provider settings_config after update",
        )
        backup_settings = parse_json_object(
            backup_after["settings_config"],
            "backup provider settings_config",
        )

        new_key_active = (
            active_settings.get("auth", {}).get("OPENAI_API_KEY") == api_key
        )
        old_key_preserved = (
            backup_settings.get("auth", {}).get("OPENAI_API_KEY") == old_key
        )
        payload_identical = compare_clone_payload(
            active_settings,
            backup_settings,
        )
        if not new_key_active:
            raise RuntimeError("active provider does not contain the new key")
        if not old_key_preserved:
            raise RuntimeError("backup provider does not contain the old key")
        if not payload_identical:
            raise RuntimeError(
                "provider model or routing payload differs between active and backup"
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return {
        "applied": True,
        "active_provider_id": SOURCE_PROVIDER_ID,
        "active_provider_name": ACTIVE_PROVIDER_NAME,
        "backup_provider_id": BACKUP_PROVIDER_ID,
        "backup_provider_name": BACKUP_PROVIDER_NAME,
        "new_key_active": True,
        "old_key_preserved": True,
        "models_and_payload_identical": True,
        "backup_dir": str(backup_dir),
        "restart_required": True,
    }


def verify_change(api_key: str) -> dict:
    connection = connect_db()
    try:
        active = provider_row(connection, SOURCE_PROVIDER_ID)
        old_key_provider = provider_row(connection, BACKUP_PROVIDER_ID)
    finally:
        connection.close()

    active_settings = parse_json_object(
        active["settings_config"],
        "active provider settings_config",
    )
    old_key_settings = parse_json_object(
        old_key_provider["settings_config"],
        "old-key provider settings_config",
    )
    active_key = active_settings.get("auth", {}).get("OPENAI_API_KEY", "")
    old_key = old_key_settings.get("auth", {}).get("OPENAI_API_KEY", "")

    return {
        "verified": (
            active["name"] == ACTIVE_PROVIDER_NAME
            and old_key_provider["name"] == BACKUP_PROVIDER_NAME
            and active_key == api_key
            and old_key != active_key
            and compare_clone_payload(active_settings, old_key_settings)
        ),
        "active_provider_id": SOURCE_PROVIDER_ID,
        "active_provider_name": active["name"],
        "backup_provider_id": BACKUP_PROVIDER_ID,
        "backup_provider_name": old_key_provider["name"],
        "active_key_matches_input": active_key == api_key,
        "old_key_is_distinct": old_key != active_key,
        "models_and_payload_identical": compare_clone_payload(
            active_settings,
            old_key_settings,
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-key",
        action="store_true",
        help="Check the supplied key directly against NewAPI without changing the DB.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the supplied key against the database and NewAPI without changing it.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Check the key and apply the provider clone/switch transaction.",
    )
    parser.add_argument(
        "--skip-key-check",
        action="store_true",
        help="Skip the direct NewAPI key check during apply.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_modes = [args.check_key, args.verify, args.apply]
    if sum(1 for selected in selected_modes if selected) != 1:
        raise RuntimeError("choose exactly one of --check-key, --verify, or --apply")

    api_key = read_key()
    if args.check_key or args.verify or not args.skip_key_check:
        status, semantic_ok = check_key(api_key)
        print(f"key_check_status={status}")
        print(f"key_check_semantic={str(semantic_ok).lower()}")
        if status != 200:
            raise RuntimeError("new API key check failed")
        if not semantic_ok:
            raise RuntimeError("new API key did not return the expected semantic text")

    if args.check_key:
        print("key_check_applied=False")
        return 0

    if args.verify:
        result = verify_change(api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["verified"]:
            raise RuntimeError("database verification failed")
        return 0

    result = apply_change(api_key)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
