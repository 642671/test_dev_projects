#!/usr/bin/env python3
"""
apply-newapi-copy-and-trim-gpt.py

需求（用户 2026-09-23）：
  1. 清除 GPT-5.6 之前的 GPT 模型：gpt-5.4 / gpt-5.4-mini / gpt-5.5 / gpt-5.2
  2. 选择器里展示两组 NewAPI 模型：
       - newapi-*       -> Noontec NewAPI (New Key)   保持原命名
       - newapi-copy-*  -> Noontec NewAPI (Old Key)   第二组，copy 前缀
  3. 去掉与 Codex 自带模型重复的条目：gpt-6-luna / gpt-6-sol
     （Codex 自带这两条，我们的目录里再放一份，选择器就会出现两个同名项）

为什么改 DB 而不是改文件：
  cc-switch 在启动时会用 cc-switch.db 里的 provider 配置重新生成
  C:\\Users\\twm\\.codex\\config.toml 和 cc-switch-model-catalog.json，
  直接改这两个文件会在下次重启时被覆盖。

顺带加固（2026-09-23 补充）：
  cc-switch 的官方模型目录来自 codex-official-models-cache.json（上游是
  github.com/openai/codex）。该缓存里仍列有 gpt-5.4 / gpt-5.5，只要用户
  在 cc-switch 里手动"同步官方模型"，被清掉的旧 GPT 就会回灌到选择器。
  所以本脚本同时把旧 GPT 从该缓存里剔除，让"清除"变成可重复执行的动作。

可见模型是怎么来的（实测结论）：
  * 官方路由 modelSelection.mode = "all" -> 取 codex-official.modelCatalog 的全部
  * 其它路由 mode = "include"           -> 取 route.modelSelection.models
                                            与目标 provider.modelCatalog 的交集
  * route.aliases 会额外生成一个可见别名条目
  所以：删官方旧模型 = 改 codex-official.modelCatalog；
        加 copy 组     = 目标 provider 加模型定义 + 新增一条路由。

用法：
  py -3 apply-newapi-copy-and-trim-gpt.py --dry-run    # 只打印将要做的改动
  py -3 apply-newapi-copy-and-trim-gpt.py              # 实际写入
"""

import argparse
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

DB = Path(r"C:\Users\twm\.cc-switch\cc-switch.db")
CACHE_PATH = Path(r"C:\Users\twm\.cc-switch\codex-official-models-cache.json")

ROUTER_ID = "codex-multirouter"
OFFICIAL_ID = "codex-official"
SRC_ID = "universal-codex-950cc769853e4620b148532ead68beb2"  # Noontec NewAPI (New Key)
DST_ID = "universal-codex-newapi-noontec-old-key-20260923"  # Noontec NewAPI (Old Key)

COPY_ROUTE_ID = "router-universal-codex-newapi-noontec-copy"
COPY_ROUTE_LABEL = "Noontec NewAPI Copy (Old Key)"
DROP_PARENT_ROUTE_ID = "router-universal-codex-newapi-noontec"

# GPT-5.6 之前的 GPT 模型
DROP_GPT = ["gpt-5.4", "gpt-5.4-mini", "gpt-5.5", "gpt-5.2"]

# 与 Codex 自带模型重名、会造成选择器重复的条目
DROP_DUPLICATE = ["gpt-6-luna", "gpt-6-sol"]

# 源可见名 -> (copy 可见名, 上游真实模型名)
COPY_MAP = [
    (
        "newapi-deepseek-v4-flash",
        "newapi-copy-deepseek-v4-flash",
        "deepseek-v4-flash",
    ),
    (
        "newapi-deepseek-v4-flash-vision-exp",
        "newapi-copy-deepseek-v4-flash-vision-exp",
        "deepseek-v4-flash-vision-exp",
    ),
]

# 早期改名留下的别名，会让选择器里出现旧名字 deepseek-v4-flash-noontec-newapi
STALE_ALIASES = ["deepseek-v4-flash-noontec-newapi"]


def load_provider(con, pid):
    row = con.execute(
        "select settings_config from providers where id=? and app_type='codex'", (pid,)
    ).fetchone()
    if row is None:
        raise SystemExit("找不到 codex provider: " + pid)
    return json.loads(row[0])


def save_provider(con, pid, cfg):
    con.execute(
        "update providers set settings_config=? where id=? and app_type='codex'",
        (json.dumps(cfg, ensure_ascii=False, separators=(",", ":")), pid),
    )


def models_of(cfg):
    return (cfg.get("modelCatalog") or {}).get("models") or []


def model_name(m):
    return m.get("id") or m.get("model")


def drop_models(cfg, names):
    mc = cfg.setdefault("modelCatalog", {})
    models = mc.get("models") or []
    kept, removed = [], []
    for m in models:
        (removed if model_name(m) in names else kept).append(m)
    mc["models"] = kept
    return [model_name(m) for m in removed]


def make_copy_model(template, new_name, upstream):
    m = json.loads(json.dumps(template))  # deep copy
    for key in ("model", "id", "slug", "displayName", "display_name", "description",
                "name"):
        if key in m:
            m[key] = new_name
    m["upstreamModel"] = upstream
    m["upstream_model"] = upstream
    return m


def add_copy_models(cfg, source_cfg):
    """把 source_cfg 里对应的条目复制成 copy 命名，追加进 cfg.modelCatalog。"""
    src_by_name = {model_name(m): m for m in models_of(source_cfg)}
    dst = models_of(cfg)
    have = {model_name(m) for m in dst}
    added = []
    for src_name, copy_name, upstream in COPY_MAP:
        if src_name not in src_by_name:
            raise SystemExit("源 provider 缺少模型定义: " + src_name)
        if copy_name in have:
            continue
        dst.append(make_copy_model(src_by_name[src_name], copy_name, upstream))
        added.append(copy_name)
    cfg.setdefault("modelCatalog", {})["models"] = dst
    return added


def strip_stale_aliases(route):
    aliases = route.get("aliases") or {}
    gone = [a for a in STALE_ALIASES if a in aliases]
    for a in gone:
        aliases.pop(a, None)
    route["aliases"] = aliases
    return gone


def build_copy_route(dst_provider_name):
    return {
        "id": COPY_ROUTE_ID,
        "label": COPY_ROUTE_LABEL,
        "enabled": True,
        "targetProviderId": DST_ID,
        "modelSelection": {
            "mode": "include",
            "models": [c[1] for c in COPY_MAP],
        },
        "matchPrefixes": [],
        "aliases": {},
        "authPolicy": {"source": "provider_config"},
    }


def trim_official_cache(drop_names):
    """把旧 GPT 从官方模型缓存里剔除，防止重新同步官方模型时回灌。

    返回 (新内容, 被移除的名字列表)；文件不存在时返回 (None, None)。
    """
    if not CACHE_PATH.exists():
        return None, None
    data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    models = data.get("models") or []

    def name_of(m):
        return m.get("slug") or m.get("id") or m.get("model")

    kept, removed = [], []
    for m in models:
        (removed if name_of(m) in drop_names else kept).append(m)
    data["models"] = kept
    return data, [name_of(m) for m in removed]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if not DB.exists():
        raise SystemExit("找不到数据库: " + str(DB))

    con = sqlite3.connect(str(DB))
    official = load_provider(con, OFFICIAL_ID)
    router = load_provider(con, ROUTER_ID)
    src = load_provider(con, SRC_ID)
    dst = load_provider(con, DST_ID)

    report = []

    report.append(("official 移除旧 GPT", drop_models(official, DROP_GPT)))
    report.append(("router  移除旧 GPT", drop_models(router, DROP_GPT)))
    report.append(("official 移除重复项", drop_models(official, DROP_DUPLICATE)))
    report.append(("router  移除重复项", drop_models(router, DROP_DUPLICATE)))
    report.append(("old-key provider 新增 copy 模型", add_copy_models(dst, src)))
    report.append(("router  新增 copy 模型", add_copy_models(router, src)))

    cache_data, cache_removed = trim_official_cache(DROP_GPT + DROP_DUPLICATE)
    if cache_data is None:
        report.append(("官方模型缓存", ["文件不存在，跳过"]))
    else:
        report.append(("官方模型缓存移除旧 GPT", cache_removed))

    routing = router.setdefault("codexRouting", {})
    routes = routing.setdefault("routes", [])

    aliases_gone = []
    for r in routes:
        aliases_gone += strip_stale_aliases(r)
    report.append(("清除旧别名", aliases_gone))

    if not any(r.get("id") == COPY_ROUTE_ID for r in routes):
        routes.append(build_copy_route(DST_ID))
        report.append(("新增 copy 路由", [COPY_ROUTE_ID]))
    else:
        report.append(("新增 copy 路由", ["已存在，跳过"]))

    spawn = routing.get("spawnAgentModels")
    if isinstance(spawn, list):
        spawn = [
            m
            for m in spawn
            if m not in DROP_GPT
            and m not in DROP_DUPLICATE
            and m not in STALE_ALIASES
        ]
        for _, copy_name, _ in COPY_MAP:
            if copy_name not in spawn:
                spawn.append(copy_name)
        routing["spawnAgentModels"] = spawn

    for title, items in report:
        print("%-26s %s" % (title + ":", ", ".join(items) if items else "(无变化)"))

    proj = con.execute(
        "select count(*) from settings where key like 'codex_multirouter_projection:%'"
    ).fetchone()[0]
    print("%-26s %d 条（将删除，交给 cc-switch 重启后重建）" % ("投影缓存", proj))

    if args.dry_run:
        print("\n--dry-run：未写入。")
        return

    if not args.no_backup:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        bak = DB.with_name("cc-switch.db.bak-trimcopy-" + stamp)
        shutil.copy2(DB, bak)
        print("已备份数据库: " + str(bak))
        if cache_data is not None:
            cbak = CACHE_PATH.with_name(
                CACHE_PATH.name + ".bak-trimcopy-" + stamp
            )
            shutil.copy2(CACHE_PATH, cbak)
            print("已备份官方模型缓存: " + str(cbak))

    save_provider(con, OFFICIAL_ID, official)
    save_provider(con, ROUTER_ID, router)
    save_provider(con, DST_ID, dst)
    con.execute(
        "delete from settings where key like 'codex_multirouter_projection:%'"
    )
    con.commit()
    con.close()

    if cache_data is not None:
        CACHE_PATH.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("已写入官方模型缓存。")
    print("已写入数据库，投影缓存已清除。重启 cc-switch 后生效。")


if __name__ == "__main__":
    sys.exit(main())
