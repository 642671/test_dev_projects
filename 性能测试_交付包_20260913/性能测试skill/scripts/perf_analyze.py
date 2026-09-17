#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perf_analyze.py — 性能测试 · CSV → 统计 JSON

把 perf_collect.py（或既有 NAS 采集器）产出的 CSV 聚合成分档统计：

  * 每列 **峰值 / 均值 / P95 / P99**（线性插值）
  * **峰值发生时刻**（峰值必须带时刻，否则会把一次性尖峰误读成持续压力）
  * **使用期 / 空闲期**拆分（判定口径：CPU>2% 或 磁盘读写合计>0.5 或 网络收发合计>0.5 MB/s）
  * **内存是否随窗口增长**（首尾四分位均值对比 + 单调性）—— 泄漏检测的基础判据
  * **采集质量**：样本数 / 坏行剔除数 / 实际窗口 / 稳态占比

多实例（同一进程名多个 PID，如 qemu、noVNC、nginx worker）用 `--multi <正则>` 指定，
会对这些实例**逐实例统计 + 按时间戳求和出合计**。

用法：

  python perf_analyze.py --in "WebServer_idle.csv" --tag 20260913
  python perf_analyze.py --in "/Volume1/public/qemu-*.csv" --multi "qemu" --app vms --tag 20260913
  python perf_analyze.py --in "*.csv" --out stats.json --hourly hourly.csv

坏行会被剔除：时间列解析失败、或任一数值列不是数字（采集器异常时的粘连行）。
"""
import argparse
import csv
import datetime
import glob
import json
import os
import re
import sys
from collections import defaultdict

MB = 1024.0 * 1024.0

COL_TIME = "时间"

# 列名：新采集器与既有 NAS 采集器都兼容。两种口径的列名不同，靠表头自动识别。
TREE_COLS = [
    ("cpu", "CPU占用(%)", "%"),
    ("pss", "PSS占用(MB)", "MB"),
    ("rss", "RSS占用(MB)", "MB"),
    ("pvt", "private_Dirty占用(MB)", "MB"),
    ("swap", "swap占用(MB)", "MB"),
    ("disk_r", "磁盘读速度(MB/s)", "MB/s"),
    ("disk_w", "磁盘写速度(MB/s)", "MB/s"),
    ("tx", "网络发送速度(MB/s)", "MB/s"),
    ("rx", "网络接收速度(MB/s)", "MB/s"),
    ("anon", "RssAnon(MB)", "MB"),
    ("file", "RssFile(MB)", "MB"),
    ("tree", "进程数", "个"),
]

HOST_COLS = [
    ("cpu", "CPU占用(%)", "%"),
    ("cpu_user", "用户态(%)", "%"),
    ("cpu_sys", "系统态(%)", "%"),
    ("iowait", "iowait(%)", "%"),
    ("softirq", "软中断(%)", "%"),
    ("mem_pct", "内存使用(%)", "%"),
    ("mem_avail", "内存可用(MB)", "MB"),
    ("swap_used", "swap使用(MB)", "MB"),
    ("load1", "load1", ""),
    ("load5", "load5", ""),
    ("load15", "load15", ""),
    ("disk_r", "磁盘读(MB/s)", "MB/s"),
    ("disk_w", "磁盘写(MB/s)", "MB/s"),
    ("tx", "网络发送(MB/s)", "MB/s"),
    ("rx", "网络接收(MB/s)", "MB/s"),
]

# 每个口径的「角色列」—— 让上层代码不必关心具体列名
ROLES = {
    "tree": {"cpu": "CPU占用(%)",
             "mem_primary": "private_Dirty占用(MB)",     # 判内存压力的第一口径
             "mem_secondary": "PSS占用(MB)",
             "io_r": "磁盘读速度(MB/s)", "io_w": "磁盘写速度(MB/s)",
             "tx": "网络发送速度(MB/s)", "rx": "网络接收速度(MB/s)",
             "growth": "private_Dirty占用(MB)"},
    "host": {"cpu": "CPU占用(%)",
             "mem_primary": "内存使用(%)",
             "mem_secondary": "内存可用(MB)",
             "io_r": "磁盘读(MB/s)", "io_w": "磁盘写(MB/s)",
             "tx": "网络发送(MB/s)", "rx": "网络接收(MB/s)",
             "growth": None},                              # 整机口径不做增长判定
}

# 运行时按表头选定；main() 里设置
COLS = TREE_COLS
ROLE = ROLES["tree"]
SCOPE = "tree"

# 时间窗过滤（--from / --to），由 main() 设置
T_FROM = None
T_TO = None


def detect_scope(header_line):
    """按 CSV 表头判定口径：tree（进程树）还是 host（整机）。"""
    h = header_line or ""
    if "PSS占用(MB)" in h or "private_Dirty占用(MB)" in h:
        return "tree"
    if "内存可用(MB)" in h or "load1" in h:
        return "host"
    return "tree"


def use_scope(scope):
    """切换当前口径的列定义。"""
    global COLS, ROLE, SCOPE
    SCOPE = scope
    COLS = HOST_COLS if scope == "host" else TREE_COLS
    ROLE = ROLES[scope]


USAGE_CPU = 2.0        # 活跃判定：CPU > 2%
USAGE_IO = 0.5         # 活跃判定：磁盘读写合计 或 网络收发合计 > 0.5 MB/s


def _setup_io():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def stat(vals):
    """峰值 / 均值 / P95 / P99（P95/P99 用线性插值，与既有报告口径一致）。"""
    if not vals:
        return {"peak": 0, "avg": 0, "p95": 0, "p99": 0}
    v = sorted(vals)

    def pct(p):
        k = (len(v) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(v) - 1)
        return v[lo] + (v[hi] - v[lo]) * (k - lo)

    return {"peak": round(v[-1], 2), "avg": round(sum(v) / len(v), 2),
            "p95": round(pct(0.95), 2), "p99": round(pct(0.99), 2)}


def _f(row, col):
    try:
        return float(row.get(col, ""))
    except (TypeError, ValueError):
        return None


def load_csv(path):
    """读一个 CSV，返回 (rows, bad_count)。坏行剔除并计数。

    若设了 T_FROM / T_TO（`--from` / `--to`），只保留该时间窗内的样本。
    时间参数允许简写成 `HH:MM:SS`，日期从数据首行推断。
    """
    rows, bad = [], 0
    try:
        data = open(path, encoding="utf-8-sig", errors="ignore").read().replace("\x00", "")
    except (IOError, OSError) as e:
        print("[跳过] %s: %s" % (path, e), file=sys.stderr)
        return rows, bad

    for r in csv.DictReader(data.splitlines()):
        t = (r.get(COL_TIME) or "").strip()
        try:
            datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        except Exception:
            bad += 1
            continue
        # 至少要有 col 里第一个存在的数值列可解析，否则算坏行
        if not any(_f(r, c) is not None for _, c, _ in COLS):
            bad += 1
            continue
        r[COL_TIME] = t
        rows.append(r)

    if rows and (T_FROM or T_TO):
        day = rows[0][COL_TIME][:10]

        def full(s):
            s = (s or "").strip()
            return (day + " " + s) if (len(s) <= 8 and s.count(":") == 2) else s

        lo, hi = (full(T_FROM) if T_FROM else ""), (full(T_TO) if T_TO else "")
        before = len(rows)
        rows = [r for r in rows
                if (not lo or r[COL_TIME] >= lo) and (not hi or r[COL_TIME] <= hi)]
        print("  时间窗过滤 %s ~ %s：%d -> %d 行" % (lo or "起", hi or "止", before, len(rows)))
    return rows, bad


def dedup_sort(rows):
    """按时间戳去重（后到覆盖）并排序 —— 多段 CSV 拼接时会重叠。"""
    uniq = {}
    for r in rows:
        uniq[r[COL_TIME]] = r
    return [uniq[t] for t in sorted(uniq)]


def is_active(r):
    """活跃判定：CPU>2% 或 磁盘读写合计>0.5 或 网络收发合计>0.5 MB/s。"""
    cpu = _f(r, ROLE["cpu"]) or 0.0
    io = (_f(r, ROLE["io_r"]) or 0.0) + (_f(r, ROLE["io_w"]) or 0.0)
    net = (_f(r, ROLE["tx"]) or 0.0) + (_f(r, ROLE["rx"]) or 0.0)
    return cpu > USAGE_CPU or io > USAGE_IO or net > USAGE_IO


def avg_of(rows, col):
    vals = [v for v in (_f(r, col) for r in rows) if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else 0


def peak_time(rows, col):
    best_t, best_v = "", None
    for r in rows:
        v = _f(r, col)
        if v is None:
            continue
        if best_v is None or v > best_v:
            best_v, best_t = v, r[COL_TIME]
    return best_t


def growth(rows, col):
    """内存是否随窗口增长：首尾各取 1/4 样本比均值 + 单调性。

    ⚠️ 用四分位均值而非首尾单点 —— 单点噪声极大（GC、一次性缓冲）。
    """
    vals = [v for v in (_f(r, col) for r in rows) if v is not None]
    n = len(vals)
    if n < 8:
        return {"first_mb": None, "last_mb": None, "delta_mb": None,
                "monotonic": None, "verdict": "样本不足"}
    q = max(n // 4, 1)
    first = sum(vals[:q]) / q
    last = sum(vals[-q:]) / q
    up = sum(1 for i in range(1, n) if vals[i] > vals[i - 1])
    mono = up / (n - 1)
    delta = last - first
    if delta > max(2.0, first * 0.05) and mono > 0.6:
        verdict = "疑泄漏"
    elif delta > max(2.0, first * 0.05):
        verdict = "有抬升但非单调，建议延长窗口复测"
    else:
        verdict = "无增长"
    return {"first_mb": round(first, 2), "last_mb": round(last, 2),
            "delta_mb": round(delta, 2), "monotonic": round(mono, 3),
            "verdict": verdict}


def thin(rows, max_points):
    """抽稀到 max_points 个点（等间隔取样，保留首尾）。

    1 秒采样跑一天有 8 万点，不抽稀会让内联 SVG 的 HTML 涨到几十 MB。
    """
    n = len(rows)
    if n <= max_points:
        return rows
    step = n / float(max_points)
    out = [rows[int(i * step)] for i in range(max_points)]
    if out[-1] is not rows[-1]:
        out[-1] = rows[-1]
    return out


def embed_series(rows, max_points=500):
    """把抽稀后的时间序列嵌进 stats.json，让报告脚本只读一个文件就能画图。"""
    rows = thin(dedup_sort(rows), max_points)
    s = {"t": [r[COL_TIME][11:] for r in rows]}      # 只留 HH:MM:SS，省体积
    for key, col, _u in COLS:
        vals = [_f(r, col) for r in rows]
        if any(v is not None for v in vals):
            s[key] = [None if v is None else round(v, 2) for v in vals]
    return s


def build_stat(rows, seglist, series_points=500):
    rows = dedup_sort(rows)
    if not rows:
        return None
    active = [r for r in rows if is_active(r)]
    idle = [r for r in rows if not is_active(r)]
    out = {
        "segments": seglist,
        "samples": len(rows),
        "window": [rows[0][COL_TIME], rows[-1][COL_TIME]],
        "series": embed_series(rows, series_points),
        "scope": SCOPE,
        "usage": {"seconds": len(active),
                  "ratio_pct": round(len(active) / len(rows) * 100.0, 1),
                  "cpu_avg": avg_of(active, ROLE["cpu"]),
                  "mem_primary_avg": avg_of(active, ROLE["mem_primary"]),
                  "mem_secondary_avg": avg_of(active, ROLE["mem_secondary"]),
                  "disk_w_avg": avg_of(active, ROLE["io_w"])},
        "idle": {"seconds": len(idle),
                 "ratio_pct": round(len(idle) / len(rows) * 100.0, 1),
                 "cpu_avg": avg_of(idle, ROLE["cpu"]),
                 "mem_primary_avg": avg_of(idle, ROLE["mem_primary"]),
                 "mem_secondary_avg": avg_of(idle, ROLE["mem_secondary"]),
                 "disk_w_avg": avg_of(idle, ROLE["io_w"])},
        "peak_time": {},
        "growth": (growth(rows, ROLE["growth"]) if ROLE.get("growth") else
                   {"first_mb": None, "last_mb": None, "delta_mb": None,
                    "monotonic": None, "verdict": "整机口径不做增长判定"}),
    }
    for key, col, _unit in COLS:
        vals = [v for v in (_f(r, col) for r in rows) if v is not None]
        if not vals:
            continue
        out[key] = stat(vals)
        out["peak_time"][key] = peak_time(rows, col)

    # 累计流量（积分：均值 × 样本数 × 采样间隔）
    iv = estimate_interval(rows)
    for key, col in (("tx", ROLE["tx"]), ("rx", ROLE["rx"])):
        vals = [v for v in (_f(r, col) for r in rows) if v is not None]
        if vals:
            out["%s_total_MB" % key] = round(sum(vals) * iv, 1)
    return out


def estimate_interval(rows):
    """从时间戳估采样间隔（秒），用于把速率积分成总量。"""
    if len(rows) < 2:
        return 1.0
    try:
        a = datetime.datetime.strptime(rows[0][COL_TIME], "%Y-%m-%d %H:%M:%S")
        b = datetime.datetime.strptime(rows[-1][COL_TIME], "%Y-%m-%d %H:%M:%S")
        return (b - a).total_seconds() / (len(rows) - 1)
    except Exception:
        return 1.0


def merge_by_time(rowsets):
    """多实例合计：按时间戳求和（逐列相加），得到合计序列。"""
    acc = defaultdict(lambda: defaultdict(float))
    seen = set()
    for rows in rowsets:
        for r in rows:
            t = r[COL_TIME]
            seen.add(t)
            for _key, col, _u in COLS:
                v = _f(r, col)
                if v is not None:
                    acc[t][col] += v
    return [{"时间": t, **{c: str(v) for c, v in acc[t].items()}} for t in sorted(seen)]


def hourly_buckets(rows, bucket_min=10):
    """按 N 分钟分桶求均值，供绘图用（点数抽稀）。"""
    buckets = defaultdict(list)
    for r in rows:
        try:
            dt = datetime.datetime.strptime(r[COL_TIME], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        key = dt.strftime("%Y-%m-%d %H:") + "%02d" % (dt.minute // bucket_min * bucket_min)
        buckets[key].append(r)
    return {k: v for k, v in sorted(buckets.items())}


def expand_inputs(spec):
    """--in 支持：单个文件 / 目录 / glob。"""
    if os.path.isdir(spec):
        return sorted(glob.glob(os.path.join(spec, "*.csv")))
    hits = sorted(glob.glob(spec))
    return hits if hits else ([spec] if os.path.exists(spec) else [])


def base_name(path):
    """从文件名取进程名：`<名字>_<pid>_<日期>.csv` 或 `<名字>_<日期>.csv` -> <名字>"""
    n = os.path.splitext(os.path.basename(path))[0]
    n = re.sub(r"_\d{8}_\d{6}$", "", n)
    n = re.sub(r"_\d+$", "", n)
    n = n.strip("_-")            # 去掉文件名前缀里的下划线/连字符
    return n or "unnamed"


def main():
    _setup_io()
    ap = argparse.ArgumentParser(description="性能测试 · CSV → 统计 JSON")
    ap.add_argument("--in", dest="inputs", required=True,
                    help="CSV 文件 / 目录 / glob，可多次指定", action="append")
    ap.add_argument("--out", default=None, help="统计 JSON 输出路径")
    ap.add_argument("--hourly", default=None, help="（可选）10 分钟分桶均值 CSV 输出路径")
    ap.add_argument("--app", default=None, help="应用名（写进 JSON，便于报告引用）")
    ap.add_argument("--tag", default=None, help="标签（默认取当天日期）")
    ap.add_argument("--multi", default=None,
                    help="多实例进程名正则；匹配到的 CSV 会逐实例统计 + 出合计")
    ap.add_argument("--bucket", type=int, default=10, help="hourly 分桶分钟数（默认 10）")
    ap.add_argument("--scope", choices=["auto", "tree", "host"], default="auto",
                    help="CSV 口径；auto=按表头自动识别（默认）")
    ap.add_argument("--from", dest="t_from", default=None,
                    help="只统计该时刻之后的样本，格式 'YYYY-MM-DD HH:MM:SS' 或 'HH:MM:SS'")
    ap.add_argument("--to", dest="t_to", default=None,
                    help="只统计该时刻之前的样本，格式同上")
    ap.add_argument("--label", default=None,
                    help="给该时间段起个名（写进 JSON，便于报告里区分）")
    ap.add_argument("--series-points", type=int, default=500,
                    help="嵌进 JSON 的趋势序列抽稀点数（默认 500；设 0 则不嵌）")
    args = ap.parse_args()

    files = []
    for spec in args.inputs:
        files.extend(expand_inputs(spec))
    files = [f for f in files if f.lower().endswith(".csv")]
    if not files:
        sys.exit("没有找到任何 CSV：%s" % args.inputs)

    # 按首个 CSV 的表头自动识别口径（tree / host）
    scope = args.scope
    if scope == "auto":
        try:
            with open(files[0], encoding="utf-8-sig", errors="ignore") as f:
                scope = detect_scope(f.readline())
        except (IOError, OSError):
            scope = "tree"
    use_scope(scope)
    global T_FROM, T_TO
    T_FROM, T_TO = args.t_from, args.t_to
    print("口径识别：%s（%s）" % (scope, "进程树" if scope == "tree" else "整机"))

    sp = args.series_points if args.series_points and args.series_points > 1 else 0
    tag = args.tag or datetime.datetime.now().strftime("%Y%m%d")
    app = args.app or base_name(files[0])

    print("分析 %d 个 CSV，tag=%s" % (len(files), tag))
    multi_re = re.compile(args.multi) if args.multi else None

    grouped = defaultdict(list)
    meta = {}
    bad_total = 0
    for f in files:
        rows, bad = load_csv(f)
        bad_total += bad
        if bad:
            print("  %s: 剔除坏行 %d" % (os.path.basename(f), bad))
        if not rows:
            print("  %s: 无有效行，跳过" % os.path.basename(f))
            continue
        name = base_name(f)
        grouped[name].append({
            "file": os.path.basename(f), "n": len(rows),
            "window": [rows[0][COL_TIME], rows[-1][COL_TIME]],
        })
        meta.setdefault(name, []).append((f, rows))
    print("共剔除坏行 %d 行" % bad_total)

    if not meta:
        sys.exit("所有 CSV 都没有有效数据")

    result = {"app": app, "tag": tag,
              "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "quality": {"files": len(files), "bad_rows": bad_total},
              "procs": {}}

    all_rows_for_hourly = {}
    for name, segs in meta.items():
        if multi_re and multi_re.search(name) and len(segs) > 1:
            # 多实例：逐实例统计 + 合计
            for i, (f, rows) in enumerate(segs, 1):
                inst = "%s#%d" % (name, i)
                st = build_stat(rows, [{"file": os.path.basename(f), "n": len(rows),
                                        "window": [rows[0][COL_TIME], rows[-1][COL_TIME]]}],
                            sp)
                if st:
                    result["procs"][inst] = st
                    all_rows_for_hourly[inst] = rows
            merged = merge_by_time([rows for _, rows in segs])
            st = build_stat(merged, [{"file": "%s 全部 %d 个实例合计" % (name, len(segs)),
                                      "n": len(merged),
                                      "window": [merged[0][COL_TIME], merged[-1][COL_TIME]]}],
                            sp)
            if st:
                result["procs"]["%s(合计)" % name] = st
                all_rows_for_hourly["%s(合计)" % name] = merged
        else:
            rows = []
            for _f_, rs in segs:
                rows.extend(rs)
            st = build_stat(rows, grouped[name], sp)
            if st:
                result["procs"][name] = st
                all_rows_for_hourly[name] = rows

    total_samples = sum(v["samples"] for v in result["procs"].values())
    result["quality"]["samples"] = total_samples
    result["quality"]["notes"] = ("网络列为整机口径，不可归因单应用；"
                                  "内存判压力请用 pvt(private_Dirty)/pss，不要用 rss")

    out = args.out or "%s_stats_%s.json" % (app, tag)
    d = os.path.dirname(os.path.abspath(out))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if args.hourly:
        d = os.path.dirname(os.path.abspath(args.hourly))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.hourly, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["时间", "进程", "CPU均", "PSS均", "private_Dirty均",
                        "磁盘写均", "网络发均", "网络收均", "样本"])
            for proc, rows in all_rows_for_hourly.items():
                for bucket, rs in hourly_buckets(rows, args.bucket).items():
                    w.writerow([bucket, proc, avg_of(rs, "CPU占用(%)"),
                                avg_of(rs, "PSS占用(MB)"),
                                avg_of(rs, "private_Dirty占用(MB)"),
                                avg_of(rs, "磁盘写速度(MB/s)"),
                                avg_of(rs, "网络发送速度(MB/s)"),
                                avg_of(rs, "网络接收速度(MB/s)"), len(rs)])

    print("OK  %s" % out)
    for name, st in result["procs"].items():
        # 汇总行按「角色列」取，两种口径都能打（进程树看 pvt/pss，整机看 mem_pct）
        prim = st.get("pvt") or st.get("mem_pct") or {}
        sec = st.get("pss") or st.get("mem_avail") or {}
        print("  %-24s 样本=%-6d CPU均=%-7s %s均=%-8s %s均=%-8s 增长=%s"
              % (name, st["samples"], st["cpu"]["avg"],
                 "pvt" if "pvt" in st else "mem%", prim.get("avg"),
                 "pss" if "pss" in st else "availMB", sec.get("avg"),
                 st["growth"]["verdict"]))
    if args.hourly:
        print("OK  %s" % args.hourly)
    return 0


if __name__ == "__main__":
    sys.exit(main())
