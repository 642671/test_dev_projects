#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perf_report.py — 性能测试 · 报告生成（Markdown + 自包含 HTML）

三种报告体裁，每种都能出 `.md` 和 `.html` 两种格式：

  monitor  监控报告 —— 同一个应用的**使用期 vs 空闲期**，进程树级，PSS 为中心
  perf     性能报告 —— 同一进程的**空闲 vs 负载**（多场景并列），峰值/均值/P95/P99
  summary  汇总报告 —— **多应用横向**对比 + 方法学提示

**纯标准库**（json/html/argparse/datetime/re/math），不依赖 matplotlib 等任何第三方包，
也不依赖 k6/JMeter —— 只要手上有 CSV/JSON，就能出报告。图表是**手绘内联 SVG**，
产物是单文件、断网可看、零外部请求。

用法：

  # 监控报告（输入是 perf_analyze.py 产出的 stats.json）
  python perf_report.py --kind monitor -i WebServer_stats.json --md r.md --html r.html

  # 性能报告（空闲 + 负载 两份输入，多场景并列）
  python perf_report.py --kind perf -i idle.json -i load.json --labels 空闲,4路转码 \\
      --md r.md --html r.html

  # 汇总报告（多应用横向）
  python perf_report.py --kind summary -i emby.json -i jellyfin.json -i qb.json \\
      --md r.md --html r.html

  # 接口压测结果直接出报告
  python perf_report.py --kind perf --from-k6 k6_summary.json --md r.md --html r.html
  python perf_report.py --kind perf --from-jmeter result.jtl   --md r.md --html r.html

  # CI：出现不通过则退出码 1
  python perf_report.py --kind perf -i load.json --fail-on FAIL --html r.html
"""
import argparse
import csv
import datetime
import html
import json
import math
import os
import re
import sys

# ---------------------------------------------------------------- 状态与阈值

STATUS_ORDER = {"FAIL": 0, "WARN": 1, "NA": 2, "PASS": 3}
STATUS_LABEL = {"PASS": "✓ 通过", "WARN": "! 待确认", "FAIL": "✗ 不通过", "NA": "– 未采集"}
STATUS_CLS = {"PASS": "ok", "WARN": "warn", "FAIL": "bad", "NA": "na"}

# 默认阈值。**业界参考值，不是业务验收标准** —— 报告里会显式回显这一点。
DEFAULT_THRESHOLDS = {
    "cpu_pct": 70,            # 整机 / 应用 CPU 上限（%）
    "mem_pct": 70,            # 整机内存使用率上限（%）
    "disk_util_pct": 80,      # 磁盘利用率上限（%）
    "iowait_pct": 30,         # %iowait 上限
    "net_bw_pct": 30,         # 带宽占用上限（%）
    "load_per_core": 0.7,     # Load Average / 核数 上限
    "error_rate_pct": 0.2,    # 压测失败率上限
    "success_rate_pct": 99.5,  # 成功率下限
    "avg_rt_ms": 200,         # 平均响应时间上限
    "p95_rt_ms": 500,         # P95 响应时间上限
    "p99_rt_ms": 1000,        # P99 响应时间上限
    "proc_mem_peak_mb": 1024,  # 单进程内存峰值上限（private_Dirty，MB）—— 超过需讨论评估
    "gc_full_count": 0,       # Full GC 次数（应为 0）
    "slow_query": 0,          # 慢查询条数（应为 0）
    "deadlock": 0,            # 死锁次数（应为 0）
}

# 展示用指标定义：(key, 中文名, 单位, 阈值key, 判定模式)
#   模式 max  —— 越低越好
#        min  —— 越高越好
#        zero —— 必须为 0
#        info —— 无阈值，只展示
METRIC_DEFS = [
    ("cpu",     "CPU（单核口径）",   "%",    "cpu_pct",        "max"),
    ("pss",     "PSS",               "MB",   None,             "info"),
    ("rss",     "RSS",               "MB",   None,             "info"),
    ("pvt",     "private_Dirty",     "MB",   None,             "info"),
    ("anon",    "RssAnon",           "MB",   None,             "info"),
    ("file",    "RssFile（页缓存）", "MB",   None,             "info"),
    ("swap",    "swap",              "MB",   None,             "info"),
    ("disk_r",  "磁盘读",            "MB/s", None,             "info"),
    ("disk_w",  "磁盘写",            "MB/s", None,             "info"),
    ("tx",      "网络发送（整机）",  "MB/s", "net_bw_pct",     "info"),
    ("rx",      "网络接收（整机）",  "MB/s", None,             "info"),
    ("tree",    "进程树规模",        "个",   None,             "info"),
]

API_METRIC_DEFS = [
    ("avg_rt",     "平均响应时间", "ms",  "avg_rt_ms",       "max"),
    ("p95_rt",     "P95 响应时间", "ms",  "p95_rt_ms",       "max"),
    ("p99_rt",     "P99 响应时间", "ms",  "p99_rt_ms",       "max"),
    ("max_rt",     "最大响应时间", "ms",  None,              "info"),
    ("min_rt",     "最小响应时间", "ms",  None,              "info"),
    ("tps",        "TPS / 吞吐量", "req/s", None,            "info"),
    ("error_rate", "错误率",       "%",   "error_rate_pct",  "max"),
    ("success_rate", "成功率",     "%",   "success_rate_pct", "min"),
]

KIND_TITLE = {"monitor": "应用资源监控报告", "perf": "性能测试报告", "summary": "性能测试汇总报告"}


def _setup_io():
    """Windows 控制台 cp936 下打印非 ASCII 会 UnicodeEncodeError —— 先掰成 utf-8。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ---------------------------------------------------------------- 取值小工具

def dig(obj, path, default=None):
    """按 'a.b.c' 安全取值，任一层缺失都返回 default。"""
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, default)
        elif isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else default
        else:
            return default
        if cur is None:
            return default
    return cur


def num(x):
    """转数；转不动返回 None（**None 不等于 0** —— 判定成 NA 而不是 FAIL）。"""
    if x is None or isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def ec(v):
    """转义并把 None 兜底成「（无）」—— html.escape(None) 会直接抛异常。"""
    return html.escape("（无）" if v is None else str(v))


def md_cell(s):
    """Markdown 单元格转义：`|` 与换行必须处理，否则表格炸。"""
    if s is None:
        s = "（无）"
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def fmt(v, unit=""):
    """数值 + 单位；None 显示「未采集」，**不显示 0**。"""
    n = num(v)
    if n is None:
        return "未采集"
    if abs(n - round(n)) < 1e-9:
        s = "%d" % round(n)
    elif abs(n) >= 100:
        s = "%.1f" % n
    else:
        s = "%.2f" % n
    return s + unit if unit else s


def r1(v):
    n = num(v)
    return None if n is None else round(n, 1)


# ---------------------------------------------------------------- 阈值判定

def judge(value, limit, mode):
    """判定单条指标。**value 为 None 一律 NA，绝不升级成 FAIL。**

    采不到 Full GC ≠ Full GC 超标 —— 误判会让团队去修一个不存在的故障。
    """
    v = num(value)
    lim = num(limit)
    if v is None:
        return "NA"
    if mode == "info" or lim is None:
        return "PASS"
    if mode == "zero":
        return "PASS" if v <= 0 else "FAIL"
    if mode == "max":
        if v <= lim:
            return "PASS"
        return "WARN" if v <= lim * 1.2 else "FAIL"
    if mode == "min":
        if v >= lim:
            return "PASS"
        return "WARN" if v >= lim * 0.98 else "FAIL"
    return "PASS"


def overall(checks):
    """总判定：任一 FAIL → FAIL；否则任一 WARN → WARN；否则 PASS。

    NA 不参与升级（但会在报告里单独列出，提醒「这些没测到」）。
    """
    st = [c["status"] for c in checks]
    if "FAIL" in st:
        return "FAIL"
    if "WARN" in st:
        return "WARN"
    if all(s == "NA" for s in st) and st:
        return "NA"
    return "PASS"


# ---------------------------------------------------------------- 手绘 SVG
#
# 七条坑（全部已处理）：
#   1. None 不能当 0 —— 缺采样点会断线分段，否则曲线周期性掉 0 会得出反结论
#   2. html.escape 不能用在 SVG 标记上 —— 只对 <text> 的文本内容转义
#   3. 除零三处 —— d1==d0 / len(points)==1 / max(vals)==0
#   4. 点数爆炸 —— 调用方已抽稀，这里再兜一层
#   5. 浮点尾巴 —— 一律 round
#   6. 中文字体 —— font-family 显式写
#   7. 不用 <style> 块 —— 只写 presentation attributes

SVG_FONT = "Segoe UI,Microsoft YaHei,sans-serif"
PALETTE = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2", "#be185d", "#65a30d"]


def _segments(ts, vs):
    """把含 None 的序列切成若干连续段 —— 缺数据要断线，不能连成 0。"""
    segs, cur = [], []
    for i, v in enumerate(vs):
        if v is None:
            if len(cur) > 1:
                segs.append(cur)
            cur = []
        else:
            cur.append((ts[i], v))
    if len(cur) > 1:
        segs.append(cur)
    elif len(cur) == 1:
        segs.append(cur)
    return segs


def _nice_max(v):
    """把最大值向上取整到好看的刻度。"""
    if v <= 0:
        return 1.0
    exp = math.floor(math.log10(v))
    base = 10 ** exp
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10):
        if v <= m * base:
            return m * base
    return 10 * base


def svg_line(series_list, width=780, height=240, y_unit="", title="", max_ticks=6):
    """多序列折线图。series_list = [{"name","v":[...], "t":[...]}]"""
    if not series_list:
        return '<p class="muted">（无可绘制数据）</p>'
    ts = series_list[0].get("t") or []
    n = len(ts)
    if n < 2:
        return '<p class="muted">（采样点不足 2 个，无法绘制趋势）</p>'

    all_vals = [v for s in series_list for v in (s.get("v") or []) if v is not None]
    if not all_vals:
        return '<p class="muted">（该指标无有效数据）</p>'
    ymax = _nice_max(max(all_vals))
    ymin = 0.0
    if ymax == ymin:                       # 除零保护：所有值相等（空载基线很常见）
        ymax = ymin + 1.0

    pad_l, pad_r, pad_t, pad_b = 62, 16, 16, 34
    w = max(width - pad_l - pad_r, 10)
    h = max(height - pad_t - pad_b, 10)

    def X(i):
        return pad_l + (w * i / (n - 1) if n > 1 else 0)

    def Y(v):
        return pad_t + h - (h * (v - ymin) / (ymax - ymin))

    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="100%%" '
           'height="%d" role="img" font-family="%s">' % (width, height, height, SVG_FONT)]

    # 网格 + Y 轴刻度
    ticks = min(max_ticks, 5)
    for k in range(ticks + 1):
        v = ymin + (ymax - ymin) * k / ticks
        y = round(Y(v), 1)
        out.append('<line x1="%d" y1="%s" x2="%d" y2="%s" stroke="#eceff3" stroke-width="1"/>'
                   % (pad_l, y, pad_l + w, y))
        out.append('<text x="%d" y="%s" font-size="10" fill="#8a93a2" text-anchor="end">%s</text>'
                   % (pad_l - 6, round(y + 3, 1), ec(("%g" % round(v, 2)))))
    # X 轴首中尾三个时间标签
    for i in (0, n // 2, n - 1):
        if 0 <= i < n:
            out.append('<text x="%s" y="%d" font-size="10" fill="#8a93a2" text-anchor="middle">%s</text>'
                       % (round(X(i), 1), height - 12, ec(ts[i])))

    # 折线（断线分段）
    for si, s in enumerate(series_list):
        color = PALETTE[si % len(PALETTE)]
        vs = s.get("v") or []
        if len(vs) != n:
            vs = (vs + [None] * n)[:n]
        for seg in _segments(ts, vs):
            pts = " ".join("%s,%s" % (round(X(i), 1), round(Y(v), 1))
                           for i, v in ((ts.index(t), v) for t, v in seg))
            # 用枚举下标而非 ts.index（时间戳可能重复）
            pts = " ".join("%s,%s" % (round(X(idx), 1), round(Y(v), 1))
                           for idx, (_t, v) in _with_index(ts, vs, seg))
            if len(seg) == 1:
                idx = ts.index(seg[0][0])
                out.append('<circle cx="%s" cy="%s" r="2.5" fill="%s"/>'
                           % (round(X(idx), 1), round(Y(seg[0][1]), 1), color))
            else:
                out.append('<polyline fill="none" stroke="%s" stroke-width="1.8" '
                           'stroke-linejoin="round" points="%s"/>' % (color, pts))

    # 图例
    lx = pad_l + 4
    for si, s in enumerate(series_list):
        color = PALETTE[si % len(PALETTE)]
        out.append('<rect x="%d" y="%d" width="10" height="3" fill="%s"/>' % (lx, pad_t + 2, color))
        out.append('<text x="%d" y="%d" font-size="11" fill="#5b6472">%s</text>'
                   % (lx + 14, pad_t + 6, ec(s.get("name", ""))))
        lx += 18 + 7 * len(str(s.get("name", "")))
    if y_unit:
        out.append('<text x="%d" y="%d" font-size="10" fill="#8a93a2">%s</text>'
                   % (pad_l - 56, pad_t - 4, ec(y_unit)))
    out.append("</svg>")
    return "".join(out)


def _with_index(ts, vs, seg):
    """给分段里的点补回全局下标（时间戳可能重复，不能用 list.index）。"""
    want = set(id(x) for x in seg)
    out = []
    for i, v in enumerate(vs):
        if v is None:
            continue
        if i < len(ts):
            out.append((i, (ts[i], v)))
    # 只保留落在该段值域里的连续块
    idxs = [i for i, v in enumerate(vs) if v is not None]
    res, cur = [], []
    for i in idxs:
        if cur and i != cur[-1] + 1:
            if cur:
                res.append(cur)
            cur = []
        cur.append(i)
    if cur:
        res.append(cur)
    for run in res:
        if run and run[0] == idxs[idxs.index(run[0])]:
            pass
    # 简化：按连续块重建，与 _segments 顺序一致
    blocks, cur = [], []
    for i in range(len(vs)):
        if vs[i] is None:
            if cur:
                blocks.append(cur)
            cur = []
        else:
            cur.append(i)
    if cur:
        blocks.append(cur)
    target = [i for i in range(len(vs)) if vs[i] is not None]
    # 找到与 seg 长度相同且值一致的那个块
    for b in blocks:
        if len(b) == len(seg) and all(abs(vs[b[k]] - seg[k][1]) < 1e-9 for k in range(len(b))):
            return [(b[k], (ts[b[k]], vs[b[k]])) for k in range(len(b))]
    if blocks:
        b = blocks[0]
        return [(b[k], (ts[b[k]], vs[b[k]])) for k in range(len(b))]
    return []


def svg_bars(items, width=780, height=200, y_unit="", name_key="name", val_key="value"):
    """柱状图。items = [{"name":..., "value":...}]"""
    items = [it for it in (items or []) if num(it.get(val_key)) is not None]
    if not items:
        return '<p class="muted">（无可绘制数据）</p>'
    vmax = _nice_max(max(num(it[val_key]) for it in items))
    if vmax <= 0:
        vmax = 1.0
    pad_l, pad_r, pad_t, pad_b = 62, 16, 16, 30
    w = max(width - pad_l - pad_r, 10)
    h = max(height - pad_t - pad_b, 10)
    bw = max(w / float(len(items)) * 0.62, 2)
    gap = w / float(len(items))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="100%%" '
           'height="%d" role="img" font-family="%s">' % (width, height, height, SVG_FONT)]
    for k in range(5):
        v = vmax * k / 4.0
        y = round(pad_t + h - h * k / 4.0, 1)
        out.append('<line x1="%d" y1="%s" x2="%d" y2="%s" stroke="#eceff3" stroke-width="1"/>'
                   % (pad_l, y, pad_l + w, y))
        out.append('<text x="%d" y="%s" font-size="10" fill="#8a93a2" text-anchor="end">%s</text>'
                   % (pad_l - 6, round(y + 3, 1), ec("%g" % round(v, 2))))
    for i, it in enumerate(items):
        v = num(it[val_key])
        bh = h * v / vmax
        x = round(pad_l + gap * i + (gap - bw) / 2.0, 1)
        y = round(pad_t + h - bh, 1)
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" rx="2"/>'
                   % (x, y, round(bw, 1), round(max(bh, 0.5), 1), PALETTE[0]))
        lab = str(it.get(name_key, ""))
        out.append('<text x="%s" y="%d" font-size="10" fill="#5b6472" text-anchor="middle">%s</text>'
                   % (round(pad_l + gap * i + gap / 2.0, 1), height - 12,
                      ec(lab[:14])))
    if y_unit:
        out.append('<text x="%d" y="%d" font-size="10" fill="#8a93a2">%s</text>'
                   % (pad_l - 56, pad_t - 4, ec(y_unit)))
    out.append("</svg>")
    return "".join(out)


def svg_meter(pct, limit=None, width=180, height=12):
    """利用率条。超限变红。"""
    v = num(pct)
    if v is None:
        return '<span class="muted">未采集</span>'
    v = max(0.0, min(v, 100.0))
    color = "#059669"
    lim = num(limit)
    if lim is not None and v > lim:
        color = "#d97706" if v <= lim * 1.2 else "#dc2626"
    fw = round(width * v / 100.0, 1)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'font-family="%s">' % (width, height, width, height, SVG_FONT)]
    out.append('<rect x="0" y="0" width="%d" height="%d" rx="6" fill="#eceff3"/>' % (width, height))
    out.append('<rect x="0" y="0" width="%s" height="%d" rx="6" fill="%s"/>' % (fw, height, color))
    if lim is not None:
        out.append('<line x1="%s" y1="0" x2="%s" y2="%d" stroke="#1f2430" stroke-width="1" '
                   'stroke-dasharray="2,2"/>' % (round(width * min(lim, 100) / 100.0, 1),
                                                 round(width * min(lim, 100) / 100.0, 1), height))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- 输入归一化

def normalize(data, label=None, kind_hint=None):
    """把 perf_analyze 的 stats.json（或手写 results.json）统一成内部结构。

    兼容两种形状：
      A. stats.json  —— 顶层有 "procs"，每个 proc 直接带 cpu/pss/pvt/... 统计
      B. results.json —— 顶层有 "metrics"，形如 {"cpu": {"idle":{...}, "load":{...}}}
    """
    data = data or {}
    ctx = {
        "kind": kind_hint or data.get("kind") or "monitor",
        "label": label or data.get("app") or data.get("meta", {}).get("title") or "未命名",
        "meta": data.get("meta") or {},
        "quality": data.get("quality") or {},
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "scenarios": [],       # [{"name":..., "procs": {name: procstat}}]
        "procs": {},           # 单场景便捷视图
        "analysis": data.get("analysis") or {},
        "coverage": data.get("coverage") or [],
        "leak": data.get("leak") or {},
        "amplification": data.get("amplification") or [],
        "raw": data,
    }
    for k, v in (data.get("thresholds") or {}).items():
        if num(v) is not None:
            ctx["thresholds"][k] = v

    procs = data.get("procs")
    if isinstance(procs, dict) and procs:
        # 形状 A
        ctx["procs"] = procs
        ctx["scenarios"] = [{"name": label or data.get("app") or "本次采集", "procs": procs}]
        if kind_hint is None and len(procs) > 1:
            ctx["kind"] = "summary"
    elif isinstance(data.get("metrics"), dict) and data["metrics"]:
        # 形状 B：metrics[key][scenario] = {avg,peak,p95,p99}
        metrics = data["metrics"]
        scen_names = []
        for _k, by_scen in metrics.items():
            if isinstance(by_scen, dict):
                for sn in by_scen:
                    if sn not in ("unit", "scope") and sn not in scen_names:
                        scen_names.append(sn)
        for sn in scen_names:
            p = {}
            for k, by_scen in metrics.items():
                if isinstance(by_scen, dict) and isinstance(by_scen.get(sn), dict):
                    p[k] = by_scen[sn]
            ctx["scenarios"].append({"name": sn, "procs": {"": p}})
        if ctx["scenarios"]:
            ctx["procs"] = {sn["name"]: sn["procs"][""] for sn in ctx["scenarios"]}
        if kind_hint is None:
            ctx["kind"] = "perf" if len(ctx["scenarios"]) > 1 else "monitor"
    return ctx


def merge_scenarios(ctxs, labels=None):
    """把多份单场景 ctx 合成一个多场景 ctx（性能报告 / 汇总报告用）。"""
    base = ctxs[0]
    out = dict(base)
    out["scenarios"] = []
    for i, c in enumerate(ctxs):
        name = (labels[i] if labels and i < len(labels) else None) or c["label"] or ("场景%d" % (i + 1))
        proc = c["procs"] or {}
        out["scenarios"].append({"name": name, "procs": proc})
    out["thresholds"] = base["thresholds"]
    return out


# ---------------------------------------------------------------- 判定与放大倍数

def proc_mem_check(ctx):
    """单进程内存峰值检查 —— **单独一条评审红线，不属于常规指标表**。

    判定口径：优先 `private_Dirty`（真实匿名内存），缺失时退回 `PSS`。
    **绝不用 RSS** —— RSS 含 `RssFile`（mmap 页缓存，内核可随时回收），
    实测某做种应用 RSS 5918 MB 而真实匿名仅 140 MB，用 RSS 判会全线误报。

    返回 (状态, 明细 dict) 或 (None, None)（无数据/无阈值时）。
    """
    lim = num(ctx["thresholds"].get("proc_mem_peak_mb"))
    if lim is None:
        return None, None
    # 每个场景各出一个值（该场景内所有进程的最大峰值），状态取全局最差
    values, worst = {}, None
    for sc in ctx["scenarios"]:
        sc_worst = None
        for pn, ps in (sc["procs"] or {}).items():
            if not isinstance(ps, dict):
                continue
            # 优先 private_Dirty；没有则退 PSS
            for key, label in (("pvt", "private_Dirty"), ("pss", "PSS")):
                v = num(dig(ps, key + ".peak"))
                if v is None:
                    continue
                if sc_worst is None or v > sc_worst["peak_mb"]:
                    sc_worst = {"proc": pn or "（默认）", "metric": label, "peak_mb": v}
                break
        values[sc["name"]] = sc_worst["peak_mb"] if sc_worst else None
        if sc_worst and (worst is None or sc_worst["peak_mb"] > worst["peak_mb"]):
            worst = {"scenario": sc["name"], **sc_worst}
    if worst is None:
        return None, None
    st = "PASS" if worst["peak_mb"] <= lim else "WARN"
    return st, {"limit_mb": lim, "values": values, **worst}


def build_concerns(ctx):
    """逐项给出「有没有问题」的**明确结论** —— 读者要的是一句话答案，不是翻表。

    这是报告的「问题清单」章节：每个关注点一行，给出 ✅/⚠️/❌/– 与依据。
    """
    out = []

    def add(name, verdict, why):
        out.append({"name": name, "verdict": verdict, "why": why})

    V_OK, V_WARN, V_BAD, V_NA = "✅ 无", "⚠️ 需关注", "❌ 有", "– 未采集"

    # ── 1) 内存泄漏（最常被问的一条）
    leak = find_leak(ctx)
    if leak and (leak.get("evidence") or []):
        v = leak.get("verdict")
        ev = leak.get("evidence") or []
        worst = None
        for e in ev:
            d = num(e.get("delta_mb"))
            if d is not None and (worst is None or abs(d) > abs(worst.get("delta_mb", 0))):
                worst = e
        if worst:
            detail = ("各窗口 private_Dirty 净变化最大 **%+.2f MB**（%.2f → %.2f），单调度 %.3f"
                      % (worst["delta_mb"], worst["first_mb"], worst["last_mb"], worst["monotonic"]))
        else:
            detail = "有长窗口数据"
        # 窗口够不够长？< 30 分钟只能排除「快速泄漏」，判不出慢泄漏
        win_min = None
        for sc in ctx["scenarios"]:
            for ps in (sc["procs"] or {}).values():
                w = ps.get("window") or []
                if len(w) == 2:
                    try:
                        t0 = datetime.datetime.strptime(w[0], "%Y-%m-%d %H:%M:%S")
                        t1 = datetime.datetime.strptime(w[1], "%Y-%m-%d %H:%M:%S")
                        m = (t1 - t0).total_seconds() / 60.0
                        win_min = m if win_min is None else max(win_min, m)
                    except Exception:
                        pass
        short = win_min is not None and win_min < 30
        caveat = ("；⚠️ **本报告窗口仅 %.0f 分钟，只能排除「快速泄漏」，慢泄漏需长稳（≥8 小时）才能判**"
                  % win_min) if short else ""
        if v == "NO_LEAK":
            add("**内存泄漏**", V_OK,
                detail + " —— **均无单调爬升**（判据：净变化 >5% 且单调度 >0.6 才算疑泄漏）" + caveat)
        elif v == "SUSPECT":
            add("**内存泄漏**", V_WARN, detail + " —— **疑似，建议延长窗口复测**")
        else:
            add("**内存泄漏**", V_BAD, detail)
    else:
        add("**内存泄漏**", V_NA, "未做长稳 / churn 测试，无法判定")

    # ── 2) 单进程内存峰值（1GB 红线）
    pm = ctx.get("proc_mem")
    if pm:
        peak, lim = pm["peak_mb"], pm["limit_mb"]
        ok = peak <= lim
        add("**单进程内存峰值**", V_OK if ok else V_WARN,
            "峰值 **%.1f MB**（private_Dirty），红线 %.0f MB —— %s"
            % (peak, lim, "未超线" if ok else "**超线，需团队讨论评估**"))
    else:
        add("**单进程内存峰值**", V_NA, "无进程级内存数据")

    # ── 3) CPU / 磁盘 / 网络 是否瓶颈（从指标判定推）
    def by_key(k):
        for c in ctx.get("checks") or []:
            if c["key"] == k:
                return c
        return None

    for key, label, limit_hint in (("cpu", "**CPU 瓶颈**", "thresholds"),):
        c = by_key(key)
        if not c or c["status"] == "NA":
            add(label, V_NA, "未采集该指标")
            continue
        vals = [num(v) for v in c["values"].values() if num(v) is not None]
        peak = max(vals) if vals else None
        lim = c.get("limit")
        if c["status"] == "PASS":
            add(label, V_OK, "峰值 %.2f%s，未超阈值 %s" % (peak or 0, c["unit"], lim if lim is not None else "—"))
        elif c["status"] == "WARN":
            add(label, V_WARN, "峰值 %.2f%s，**接近阈值 %s**" % (peak or 0, c["unit"], lim))
        else:
            add(label, V_BAD, "峰值 %.2f%s，**超过阈值 %s**" % (peak or 0, c["unit"], lim))

    # ── 3.5) 磁盘 I/O（整机口径看 iowait；进程树口径退化为「进程磁盘读写峰值」）
    c_io = by_key("iowait")
    if c_io and c_io["status"] != "NA":
        vals = [num(v) for v in c_io["values"].values() if num(v) is not None]
        pk = max(vals) if vals else 0
        if c_io["status"] == "PASS":
            add("**磁盘 I/O 瓶颈**", V_OK, "整机 `%iowait` 峰值 %.2f%%，远低于阈值 %s%%" % (pk, c_io.get("limit")))
        else:
            add("**磁盘 I/O 瓶颈**", V_BAD if c_io["status"] == "FAIL" else V_WARN,
                "整机 `%iowait` 峰值 %.2f%%，超过阈值 %s%%" % (pk, c_io.get("limit")))
    else:
        rd = dr = None
        for sc in ctx["scenarios"]:
            for ps in (sc["procs"] or {}).values():
                for k, var in (("disk_r", "rd"), ("disk_w", "dr")):
                    v = num(dig(ps, k + ".peak"))
                    if v is None:
                        continue
                    if var == "rd" and (rd is None or v > rd):
                        rd = v
                    if var == "dr" and (dr is None or v > dr):
                        dr = v
        if rd is None and dr is None:
            add("**磁盘 I/O 瓶颈**", V_NA, "本口径未采集磁盘指标")
        else:
            worst = max(x for x in (rd, dr) if x is not None)
            add("**磁盘 I/O 瓶颈**", V_OK if worst < 100 else V_WARN,
                "进程磁盘读写峰值 **读 %.2f / 写 %.2f MB/s**（本口径无 `%%util`；阈值参考：`%%util` ≤80%%）"
                % (rd or 0, dr or 0))

    # ── 4) 网络带宽是否打满
    tx = None
    for sc in ctx["scenarios"]:
        for ps in (sc["procs"] or {}).values():
            v = num(dig(ps, "tx.peak"))
            if v is not None and (tx is None or v > tx):
                tx = v
    if tx is None:
        add("**网络带宽瓶颈**", V_NA, "未采集网络指标")
    else:
        # 千兆 ≈119 MB/s；≥100 MB/s 视为打满
        if tx >= 100:
            add("**网络带宽瓶颈**", V_WARN, "发送峰值 **%.2f MB/s（%.0f Mbps）**，**已接近链路上限**" % (tx, tx * 8))
        elif tx >= 30:
            add("**网络带宽瓶颈**", V_OK, "发送峰值 %.2f MB/s（%.0f Mbps），占用明显但未打满" % (tx, tx * 8))
        else:
            add("**网络带宽瓶颈**", V_OK, "发送峰值 %.2f MB/s（%.0f Mbps），占用很低" % (tx, tx * 8))

    # ── 5) 错误率
    c = by_key("error_rate") or by_key("success_rate")
    if c and c["status"] != "NA":
        vals = [num(v) for v in c["values"].values() if num(v) is not None]
        if c["status"] == "PASS":
            add("**错误率**", V_OK, "%s 峰值 %s%s，在阈值内" % (c["label"], max(vals) if vals else "—", c["unit"]))
        else:
            add("**错误率**", V_BAD, "%s 峰值 %s%s，**超过阈值 %s**" % (c["label"], max(vals) if vals else "—", c["unit"], c.get("limit")))
    else:
        add("**错误率**", V_NA, "本次为非请求-响应类负载，无错误率口径（以拉流成功/失败代替）")

    # ── 6) 稳定性（多场景时给放大倍数是否异常）
    amp = ctx.get("amplification") or []
    if len(ctx["scenarios"]) >= 2:
        cpu_amps = [x for x in amp if "CPU" in x["metric"] and x.get("ratio") is not None]
        if cpu_amps:
            mx = max(cpu_amps, key=lambda x: x["ratio"])
            add("**负载放大（相对基线）**", V_OK,
                "CPU 放大最高 **%s×**（%s：%.2f → %.2f）" % (mx["ratio"], mx["scene"], mx["idle"], mx["load"]))
    # 手工补充项（输入 JSON 的 analysis.concerns）
    for c2 in ((ctx.get("analysis") or {}).get("concerns") or []):
        if isinstance(c2, dict) and c2.get("name"):
            add(c2["name"], c2.get("verdict", "–"), c2.get("why", ""))
    return out


def build_checks(ctx):
    """对每个场景的每条指标做阈值判定，返回 [{metric,label,unit,values:{scen:...},status,limit,mode}]。"""
    defs = API_METRIC_DEFS if ctx.get("is_api") else METRIC_DEFS
    checks = []
    for key, cname, unit, tkey, mode in defs:
        values, present = {}, False
        for sc in ctx["scenarios"]:
            proc = sc["procs"]
            # 单进程取第一个；多进程取「合计」优先，否则第一个
            stat = None
            if "合计" in " ".join(proc.keys()):
                for pn, ps in proc.items():
                    if "合计" in pn:
                        stat = ps
                        break
            if stat is None and proc:
                stat = list(proc.values())[0]
            v = None
            if stat:
                if key in ("avg_rt", "p95_rt", "p99_rt", "max_rt", "min_rt"):
                    mp = {"avg_rt": "avg", "p95_rt": "p95", "p99_rt": "p99",
                          "max_rt": "peak", "min_rt": "min"}
                    v = dig(stat, "rt_ms." + mp[key])
                elif key in stat and isinstance(stat[key], dict):
                    v = stat[key].get("avg")
                else:
                    v = stat.get(key)
            if num(v) is not None:
                present = True
            values[sc["name"]] = v
        if not present:
            status = "NA"
        else:
            worst = "PASS"
            for sc in ctx["scenarios"]:
                st = judge(values[sc["name"]], ctx["thresholds"].get(tkey), mode)
                if STATUS_ORDER[st] < STATUS_ORDER[worst]:
                    worst = st
            status = worst
        checks.append({"key": key, "label": cname, "unit": unit, "values": values,
                       "status": status, "limit": ctx["thresholds"].get(tkey), "mode": mode,
                       "metric": cname})

    # 单进程内存峰值 —— 单独一条评审红线（只在应用侧口径下有意义）
    if not ctx.get("is_api"):
        st, info = proc_mem_check(ctx)
        if st is not None:
            ctx["proc_mem"] = info
            checks.append({"key": "proc_mem_peak", "label": "单进程内存峰值（private_Dirty）",
                           "unit": "MB", "values": info["values"],
                           "status": st, "limit": info["limit_mb"], "mode": "max",
                           "metric": "单进程内存峰值", "note": info})
    return checks


def amplification_of(ctx):
    """各场景相对**基线场景**（第一个）的放大倍数。

    多场景报告里每个场景都跟基线比，而不是只比前两个 —— 否则 4 场景报告
    只能看到第 2 个场景的倍数，后面两个白采了。
    """
    scs = ctx["scenarios"]
    if len(scs) < 2:
        return []
    base = scs[0]

    def first(p):
        if not p:
            return None
        if "合计" in " ".join(p.keys()):
            for pn, ps in p.items():
                if "合计" in pn:
                    return ps
        return list(p.values())[0]

    sb = first(base["procs"])
    if not sb:
        return []
    out = []
    for sc in scs[1:]:
        ss = first(sc["procs"])
        if not ss:
            continue
        for key, cname, unit, _t, _m in METRIC_DEFS:
            vb = dig(sb, key + ".avg")
            vs = dig(ss, key + ".avg")
            nb, ns = num(vb), num(vs)
            if nb is None or ns is None:
                continue
            if nb > 0:
                ratio = round(ns / nb, 1)
            else:
                ratio = None      # 基线为 0 时倍数为无穷，不写数字
            out.append({"scene": sc["name"], "metric": cname, "unit": unit,
                        "idle": nb, "load": ns, "ratio": ratio})
    return out


def find_leak(ctx):
    """从采集结果里提取泄漏判据（若有 growth 字段）。"""
    if ctx.get("leak"):
        return ctx["leak"]
    ev = []
    for sc in ctx["scenarios"]:
        for pn, ps in (sc["procs"] or {}).items():
            g = ps.get("growth") if isinstance(ps, dict) else None
            if g and g.get("verdict"):
                ev.append({"proc": pn, "scenario": sc["name"], **g})
    if not ev:
        return {}
    bad = [e for e in ev if "疑泄漏" in str(e.get("verdict"))]
    v = "SUSPECT" if bad else "NO_LEAK"
    return {"verdict": v, "rounds": [], "evidence": ev}


# ---------------------------------------------------------------- Markdown 渲染

def render_markdown(ctx):
    kind = ctx["kind"]
    L = []
    a = L.append

    a("# %s" % (ctx["meta"].get("title") or ("%s · %s" % (ctx["label"], KIND_TITLE[kind]))))
    a("")
    meta_line = []
    m = ctx["meta"]
    if m.get("device"):
        meta_line.append("**设备**：%s" % m["device"])
    if m.get("cpu_scope"):
        meta_line.append("**CPU 口径**：%s" % m["cpu_scope"])
    if m.get("interval_s"):
        meta_line.append("**采样间隔**：%ss" % m["interval_s"])
    if m.get("method"):
        meta_line.append("**方法**：%s" % m["method"])
    if m.get("env"):
        meta_line.append("**环境**：%s" % m["env"])
    if meta_line:
        a("> " + "　·　".join(meta_line))
        a("")

    checks = ctx["checks"]
    ov = ctx["overall"]

    # ---- 结论概览
    a("## 一、结论概览")
    a("")
    a("| 总判定 | 通过 | 待确认 | 不通过 | 未采集 |")
    a("|---|---|---|---|---|")
    cnt = {k: 0 for k in STATUS_ORDER}
    for c in checks:
        cnt[c["status"]] = cnt.get(c["status"], 0) + 1
    a("| **%s** | %d | %d | %d | %d |"
      % (STATUS_LABEL[ov], cnt.get("PASS", 0), cnt.get("WARN", 0),
         cnt.get("FAIL", 0), cnt.get("NA", 0)))
    a("")
    failed = [c for c in checks if c["status"] == "FAIL"]
    warned = [c for c in checks if c["status"] == "WARN"]
    na = [c for c in checks if c["status"] == "NA"]
    if failed:
        a("**未通过**：%s" % "、".join(c["label"] for c in failed))
        a("")
    if warned:
        a("**待确认**：%s" % "、".join(c["label"] for c in warned))
        a("")
    if na:
        a("**未采集**（采不到 ≠ 达标，详见「采集覆盖度」）：%s" % "、".join(c["label"] for c in na))
        a("")

    # ---- 问题清单：逐项给明确结论
    cons = ctx.get("concerns") or []
    if cons:
        a("### 问题清单（逐项结论）")
        a("")
        a("> 一眼看清「有没有问题」—— 不用翻后面的表。")
        a("")
        a("| 关注点 | 结论 | 依据 |")
        a("|---|---|---|")
        for c in cons:
            a("| %s | **%s** | %s |" % (c["name"], c["verdict"], md_cell(c["why"])))
        a("")

    # ---- 监控概况
    a("## 二、监控概况")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    q = ctx["quality"]
    a("| 场景数 | %d（%s） |" % (len(ctx["scenarios"]),
                                 "、".join(s["name"] for s in ctx["scenarios"])))
    a("| 样本数 | %s |" % md_cell(q.get("samples", "—")))
    a("| 坏行剔除 | %s |" % md_cell(q.get("bad_rows", "—")))
    if m.get("window"):
        a("| 采集窗口 | %s |" % md_cell(m["window"]))
    a("")

    pinfo = []
    for sc in ctx["scenarios"]:
        for pn, ps in (sc["procs"] or {}).items():
            pinfo.append((sc["name"], pn, ps))
    if pinfo:
        a("| 场景 | 进程组 | 样本 | 实际窗口 |")
        a("|---|---|---|---|")
        for scn, pn, ps in pinfo:
            w = ps.get("window") or []
            a("| %s | %s | %s | %s |"
              % (md_cell(scn), md_cell(pn or "（默认）"), md_cell(ps.get("samples", "—")),
                 md_cell(" → ".join(w) if w else "—")))
        a("")

    # ---- 指标统计
    a("## 三、指标统计" + ("（%d 个场景）" % len(ctx["scenarios"])
                          if len(ctx["scenarios"]) > 1 else ""))
    a("")
    scen_names = [s["name"] for s in ctx["scenarios"]]
    hdr = ["指标", "单位"] + ["%s 均值" % s for s in scen_names] + ["阈值", "判定"]
    a("| " + " | ".join(hdr) + " |")
    a("|" + "---|" * len(hdr))
    for c in checks:
        row = [c["label"], c["unit"]]
        for s in scen_names:
            row.append(fmt(c["values"].get(s), ""))
        row.append(fmt(c["limit"], "") if c["limit"] is not None else "—")
        row.append(STATUS_LABEL[c["status"]])
        a("| " + " | ".join(md_cell(x) for x in row) + " |")
    a("")
    a("> 阈值来源：**默认参考值（业界参考，非业务验收标准）**。要按项目验收标准判定，用 "
      "`--thresholds <json>` 覆盖。")
    a("")

    # ---- 峰值与时刻
    a("## 四、峰值与发生时刻")
    a("")
    a("> 峰值必须带时刻 —— 否则会把一次性尖峰（如批量写入收尾、缓存刷盘）误读成持续压力。")
    a("")
    a("| 场景 | 进程组 | 指标 | 峰值 | 发生时刻 |")
    a("|---|---|---|---|---|")
    any_row = False
    for sc in ctx["scenarios"]:
        for pn, ps in (sc["procs"] or {}).items():
            pt = ps.get("peak_time") or {}
            for key, cname, unit, _t, _m in METRIC_DEFS:
                pk = dig(ps, key + ".peak")
                if num(pk) is None:
                    continue
                any_row = True
                a("| %s | %s | %s | %s | %s |"
                  % (md_cell(sc["name"]), md_cell(pn or "（默认）"), md_cell(cname),
                     md_cell(fmt(pk, unit)), md_cell(pt.get(key, "—"))))
    if not any_row:
        a("| _（无数据）_ | | | | |")
    a("")

    # ---- 使用 vs 空闲（monitor 体裁核心）
    if kind == "monitor":
        a("## 五、使用期间 vs 空闲期间")
        a("")
        a("> 判定口径：**CPU > 2% 或 磁盘读写合计 > 0.5 MB/s 或 网络收发合计 > 0.5 MB/s = 使用**。")
        a("")
        a("| 进程组 | 使用样本 | 占比 | 使用期CPU均值 | 空闲样本 | 占比 | 空闲期CPU均值 | 空闲期PSS均值 |")
        a("|---|---|---|---|---|---|---|---|")
        for sc in ctx["scenarios"]:
            for pn, ps in (sc["procs"] or {}).items():
                u, i = ps.get("usage") or {}, ps.get("idle") or {}
                a("| %s | %s | %s%% | %s | %s | %s%% | %s | %s |"
                  % (md_cell(pn or "（默认）"), ec(u.get("seconds", "—")), ec(u.get("ratio_pct", "—")),
                     ec(u.get("cpu_avg", "—")), ec(i.get("seconds", "—")), ec(i.get("ratio_pct", "—")),
                     ec(i.get("cpu_avg", "—")), ec(i.get("pss_avg", "—"))))
        a("")

    # ---- 放大倍数
    amp = ctx.get("amplification") or []
    if amp:
        base_name = ctx["scenarios"][0]["name"] if ctx["scenarios"] else "基线"
        a("## 六、各场景相对基线的放大倍数")
        a("")
        a("| 场景 | 指标 | 基线均值 | 该场景均值 | 放大倍数 |")
        a("|---|---|---|---|---|")
        for x in amp:
            ratio = "∞" if x.get("ratio") is None and num(x.get("load")) else (
                "%s×" % x["ratio"] if x.get("ratio") is not None else "—")
            a("| %s | %s | %s | %s | **%s** |"
              % (md_cell(x.get("scene", "—")), md_cell(x["metric"]),
                 md_cell(fmt(x.get("idle"))), md_cell(fmt(x.get("load"))), md_cell(ratio)))
        a("")
        a("> 基线场景为「%s」。放大倍数用于说明量级差异；窗口不同、素材不同时**不宜作精确比较**。"
          % md_cell(base_name))
        a("")

    # ---- 泄漏判定
    leak = find_leak(ctx)
    if leak:
        a("## 七、内存回落与泄漏判定")
        a("")
        verdict = leak.get("verdict")
        txt = {"NO_LEAK": "**未发现内存泄漏迹象**", "SUSPECT": "**疑似内存泄漏，建议延长窗口复测**",
               "LEAK": "**判定存在内存泄漏**"}.get(verdict, "**判定：%s**" % ec(verdict))
        a(txt)
        a("")
        ev = leak.get("evidence") or []
        if ev:
            a("| 场景 | 进程 | 首段均值 | 末段均值 | 变化 | 单调度 | 判定 |")
            a("|---|---|---|---|---|---|---|")
            for e in ev:
                a("| %s | %s | %s | %s | %s | %s | %s |"
                  % (md_cell(e.get("scenario", "—")), md_cell(e.get("proc", "—")),
                     md_cell(fmt(e.get("first_mb"), " MB")), md_cell(fmt(e.get("last_mb"), " MB")),
                     md_cell(fmt(e.get("delta_mb"), " MB")), md_cell(e.get("monotonic", "—")),
                     md_cell(e.get("verdict", "—"))))
            a("")
        a("> 判据：**末段均值 − 首段均值**（各取 1/4 样本，避免单点噪声）配合**单调度**"
          "（相邻递增占比）。空闲期内存不归零属正常设计，只要**无单调爬升**即可判无泄漏。")
        a("")

    # ---- 采集覆盖度
    a("## 八、采集覆盖度与未测项")
    a("")
    a("> **采不到 ≠ 达标。** 下列指标本次没有采到，报告里一律显示「未采集」而**不填 0**。")
    a("")
    a("| 项 | 状态 | 说明 |")
    a("|---|---|---|")
    cov = list(ctx.get("coverage") or [])
    for c in checks:
        if c["status"] == "NA":
            cov.append({"item": c["label"], "status": "NA", "reason": "本次采集无该指标数据"})
    if cov:
        label = {"OK": "✅ 已采", "DEGRADED": "⚠️ 口径降级", "NA": "❌ 未采集"}
        for c in cov:
            a("| %s | %s | %s |" % (md_cell(c.get("item")), md_cell(label.get(c.get("status"), c.get("status"))),
                                    md_cell(c.get("reason", ""))))
    else:
        a("| _（全部指标均已采到）_ | ✅ 已采 | — |")
    a("")

    # ---- 口径声明
    a("## 九、口径声明")
    a("")
    a("- **网络列为整机口径**：Linux 没有逐进程网络字节计数（`/proc/<pid>/net/dev` 属于整个网络命名空间），"
      "因此该列取自整机数据，**不可归因给单个应用/功能**。")
    a("- **内存判压力请用 `private_Dirty` 或 `PSS`，不要用 RSS**：RSS 含 `RssFile`（mmap 文件页缓存，"
      "内核可随时回收），会被严重放大。")
    a("- **CPU 为单核口径**：100% = 1 个核，4 核跑满 = 400%。")
    a("- **评审红线（硬性）**：**单个进程的内存峰值超过 1 GB** —— 超过即需团队讨论评估，"
      "不是「达标/不达标」的二元判定。判定口径用 `private_Dirty`（真实匿名内存），"
      "**不用 RSS**（RSS 含可回收的 mmap 页缓存，会把页缓存误判成占用）。")
    a("- **其余阈值为业界参考值**（CPU ≤70%、`%util` ≤80%、错误率 ≤0.2% 等），"
      "**非业务验收标准**，**需各项目组结合自身业务具体讨论定夺**。"
      "本报告判定用的是**达标线**口径；源材料另有**警戒值**口径（CPU 75%~80%、磁盘繁忙率 <70%），"
      "两者含义不同，**勿混用**。")
    if kind == "summary":
        a("- **跨应用对比的适用边界**：不同应用若采样窗口不同、素材不同，均值不可直接精确比较。")
    a("")

    # ---- 已撤回的结论（summary）
    if kind == "summary":
        wd = (ctx.get("analysis") or {}).get("withdrawn") or []
        if wd:
            a("## 十、已撤回的结论")
            a("")
            a("> 保留纠错记录是报告质量的一部分。")
            a("")
            for w in wd:
                a("- %s" % md_cell(w))
            a("")

    ov2 = ctx.get("analysis") or {}
    if ov2.get("bottleneck") or ov2.get("suggestions"):
        a("## 瓶颈分析与建议")
        a("")
        if ov2.get("bottleneck"):
            a("**瓶颈定位**：%s" % md_cell(ov2["bottleneck"]))
            a("")
        for s in (ov2.get("evidence") or []):
            a("- %s" % md_cell(s))
        if ov2.get("evidence"):
            a("")
        for i, s in enumerate(ov2.get("suggestions") or [], 1):
            a("%d. %s" % (i, md_cell(s)))
        a("")

    a("---")
    a("")
    a(" *由 `性能测试` skill 的 `perf_report.py` 于 %s 生成。指标口径见 "
      "`references/metrics.md`，方法学陷阱见 `references/methodology-pitfalls.md`。*"
      % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- HTML 渲染
#
# ⚠️ CSS 里含 `width:100%` —— 必须用 __TOKEN__ 占位替换，**不能走 % 格式化**
#    （`%` 会被当成格式符，直接把替换炸掉）。照 UID_迁移测试/scripts/uid_verify.py 的做法。

PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--text:#1f2430;--muted:#6b7280;--border:#e6e9ef;
      --ok:#059669;--warn:#d97706;--bad:#dc2626;--na:#9ca3af;--accent:#2563eb}
*{box-sizing:border-box}
body{font-family:"Segoe UI","Microsoft YaHei",system-ui,sans-serif;margin:0;
     background:var(--bg);color:var(--text);line-height:1.65}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 10px}
h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
h3{font-size:14px;margin:20px 0 8px;color:#39414f}
p.meta{color:#4b5563;font-size:13px;margin:4px 0}
code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:12.5px}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);
      border:1px solid var(--border);border-radius:8px;overflow:hidden}
th,td{padding:7px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{background:#f0f3f7;font-weight:600}
tr:last-child td{border-bottom:none}
td.st,th.st{text-align:center;white-space:nowrap;font-weight:600}
td.ok{color:var(--ok)} td.warn{color:var(--warn)} td.bad{color:var(--bad)} td.na{color:var(--na)}
.cards{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;
      padding:10px 16px;min-width:104px;text-align:center}
.card span{display:block;font-size:21px;font-weight:700;line-height:1.25}
.card.ok span{color:var(--ok)} .card.warn span{color:var(--warn)}
.card.bad span{color:var(--bad)} .card.na span{color:var(--na)}
.kpis{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}
.kpi{flex:1 1 160px;background:var(--card);border:1px solid var(--border);
     border-left:3px solid var(--accent);border-radius:10px;padding:12px 16px}
.kpi b{display:block;font-size:22px;font-weight:700;margin-top:4px}
.kpi small{color:var(--muted);font-size:12px}
.note{background:#eef4ff;border-left:3px solid var(--accent);padding:10px 14px;
      border-radius:6px;font-size:13px;margin:12px 0}
.note.warn{background:#fff7ed;border-left-color:var(--warn)}
.note.bad{background:#fef2f2;border-left-color:var(--bad)}
.note.ok{background:#f0fdf4;border-left-color:var(--ok)}
.muted{color:var(--muted)}
.chart{background:var(--card);border:1px solid var(--border);border-radius:10px;
       padding:12px 14px;margin:12px 0}
details{background:var(--card);border:1px solid var(--border);border-radius:8px;
        padding:8px 12px;margin:10px 0;font-size:13px}
summary{cursor:pointer;font-weight:600}
footer{margin-top:34px;padding-top:14px;border-top:1px solid var(--border);
       color:var(--muted);font-size:12.5px}
</style></head><body><div class="wrap">
__BODY__
<footer>由 <code>性能测试</code> skill 的 <code>perf_report.py</code> 生成于 __TS__。
指标口径见 <code>references/metrics.md</code>，方法学陷阱见 <code>references/methodology-pitfalls.md</code>。</footer>
</div></body></html>"""


def _tbl(headers, rows, cls=None):
    out = ["<table%s><thead><tr>" % (' class="%s"' % cls if cls else "")]
    out += ["<th>%s</th>" % ec(h) for h in headers]
    out += ["</tr></thead><tbody>"]
    for r in rows:
        out.append("<tr>" + "".join(r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_html(ctx):
    kind = ctx["kind"]
    b = []
    m, q = ctx["meta"], ctx["quality"]
    checks = ctx["checks"]
    ov = ctx["overall"]

    b.append("<h1>%s</h1>" % ec(m.get("title") or ("%s · %s" % (ctx["label"], KIND_TITLE[kind]))))
    if m.get("subtitle"):
        b.append('<p class="meta"><b>%s</b></p>' % ec(m["subtitle"]))
    line = []
    for k, lbl in (("device", "设备"), ("cpu_scope", "CPU 口径"), ("interval_s", "采样间隔"),
                   ("method", "方法"), ("env", "环境")):
        if m.get(k):
            line.append("%s：%s" % (lbl, ec(m[k])))
    if line:
        b.append('<p class="meta">%s</p>' % "　·　".join(line))

    cnt = {k: 0 for k in STATUS_ORDER}
    for c in checks:
        cnt[c["status"]] = cnt.get(c["status"], 0) + 1
    b.append('<div class="cards">')
    for st in ("PASS", "WARN", "FAIL", "NA"):
        b.append('<div class="card %s"><span>%d</span>%s</div>'
                 % (STATUS_CLS[st], cnt.get(st, 0), ec(STATUS_LABEL[st])))
    b.append("</div>")
    cls = {"PASS": "ok", "WARN": "warn", "FAIL": "bad", "NA": ""}[ov]
    b.append('<div class="note %s"><b>总判定：%s</b>%s</div>'
             % (cls, ec(STATUS_LABEL[ov]),
                ("　未通过：" + ec("、".join(c["label"] for c in checks if c["status"] == "FAIL")))
                if cnt.get("FAIL") else ""))

    # 问题清单（逐项结论）—— 放在最显眼处
    cons = ctx.get("concerns") or []
    if cons:
        b.append("<h2>问题清单</h2>")
        b.append('<div class="note">一眼看清「有没有问题」—— 不用翻后面的表。</div>')
        rows = []
        for c in cons:
            v = c["verdict"]
            cls = ("ok" if v.startswith("✅") else
                   "warn" if v.startswith("⚠️") else
                   "bad" if v.startswith("❌") else "")
            rows.append(["<td>%s</td>" % ec(c["name"].replace("**", "")),
                         '<td class="st %s">%s</td>' % (cls, ec(v)),
                         "<td>%s</td>" % ec(c["why"].replace("**", ""))])
        b.append(_tbl(["关注点", "结论", "依据"], rows))

    # KPI 卡（取前 4 条有值的指标）
    kpis = [c for c in checks if num(c["values"].get(ctx["scenarios"][0]["name"])) is not None][:4]
    if kpis:
        b.append('<div class="kpis">')
        for c in kpis:
            v = c["values"].get(ctx["scenarios"][0]["name"])
            b.append('<div class="kpi"><small>%s</small><b>%s</b><small>%s</small></div>'
                     % (ec(c["label"] + ("" if len(ctx["scenarios"]) == 1 else
                                         "（%s）" % ctx["scenarios"][0]["name"])),
                        ec(fmt(v, "")), ec(c["unit"])))
        b.append("</div>")

    # 指标统计
    b.append("<h2>一、指标统计</h2>")
    scen_names = [s["name"] for s in ctx["scenarios"]]
    hdr = ["指标", "单位"] + ["%s 均值" % s for s in scen_names] + ["阈值", "判定"]
    rows = []
    for c in checks:
        tds = ["<td>%s</td>" % ec(c["label"]), "<td>%s</td>" % ec(c["unit"])]
        for s in scen_names:
            tds.append("<td>%s</td>" % ec(fmt(c["values"].get(s), "")))
        tds.append("<td>%s</td>" % ec(fmt(c["limit"], "") if c["limit"] is not None else "—"))
        tds.append('<td class="st %s">%s</td>' % (STATUS_CLS[c["status"]], ec(STATUS_LABEL[c["status"]])))
        rows.append(tds)
    b.append(_tbl(hdr, rows))
    b.append('<div class="note">阈值来源：<b>默认参考值（业界参考，非业务验收标准）</b>。'
             '按项目验收标准判定请用 <code>--thresholds</code> 覆盖。</div>')

    # 资源利用率条
    meters = []
    for c in checks:
        if c["key"] in ("cpu", "mem_pct") or c["unit"] == "%":
            v = num(c["values"].get(scen_names[0]))
            if v is not None:
                meters.append((c["label"], v, c["limit"]))
    if meters:
        b.append("<h3>资源利用率</h3><div class=\"chart\">")
        for lbl, v, lim in meters:
            b.append("<div style=\"display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px\">"
                     "<span style=\"width:190px\">%s</span>%s<span>%s</span></div>"
                     % (ec(lbl), svg_meter(v, lim), ec(fmt(v, "%"))))
        b.append("</div>")

    # 趋势图
    charts = []
    for sc in ctx["scenarios"]:
        for pn, ps in (sc["procs"] or {}).items():
            ser = ps.get("series") or {}
            ts = ser.get("t") or []
            if len(ts) < 2:
                continue
            charts.append((sc["name"], pn, ser))
    if charts:
        b.append('<h2>二、趋势图</h2>')
        for scn, pn, ser in charts:
            ts = ser["t"]
            def mk(keys, title, unit):
                sl = [{"name": k, "t": ts, "v": ser.get(k) or []} for k in keys if ser.get(k)]
                if not sl:
                    return ""
                return ('<div class="chart"><h3>%s（%s / %s）</h3>%s</div>'
                        % (ec(title), ec(scn), ec(pn or "默认"), svg_line(sl, y_unit=unit)))
            b.append(mk(["cpu"], "CPU（单核口径）", "%"))
            b.append(mk(["pss", "pvt", "rss"], "内存：PSS / private_Dirty / RSS", "MB"))
            b.append(mk(["disk_r", "disk_w"], "磁盘读写", "MB/s"))
            b.append(mk(["tx", "rx"], "网络收发（整机口径）", "MB/s"))

    # 峰值时刻
    rows = []
    for sc in ctx["scenarios"]:
        for pn, ps in (sc["procs"] or {}).items():
            pt = ps.get("peak_time") or {}
            for key, cname, unit, _t, _m in METRIC_DEFS:
                pk = dig(ps, key + ".peak")
                if num(pk) is None:
                    continue
                rows.append(["<td>%s</td>" % ec(sc["name"]), "<td>%s</td>" % ec(pn or "默认"),
                             "<td>%s</td>" % ec(cname), "<td>%s</td>" % ec(fmt(pk, unit)),
                             "<td>%s</td>" % ec(pt.get(key, "—"))])
    if rows:
        b.append("<h2>三、峰值与发生时刻</h2>")
        b.append('<div class="note">峰值必须带时刻 —— 否则会把一次性尖峰'
                 '（如批量写入收尾）误读成持续压力。</div>')
        b.append(_tbl(["场景", "进程组", "指标", "峰值", "发生时刻"], rows))

    # 使用 vs 空闲
    if kind == "monitor":
        rows = []
        for sc in ctx["scenarios"]:
            for pn, ps in (sc["procs"] or {}).items():
                u, i = ps.get("usage") or {}, ps.get("idle") or {}
                rows.append(["<td>%s</td>" % ec(pn or "默认"),
                             "<td>%s</td>" % ec(u.get("seconds", "—")),
                             "<td>%s%%</td>" % ec(u.get("ratio_pct", "—")),
                             "<td>%s</td>" % ec(u.get("cpu_avg", "—")),
                             "<td>%s</td>" % ec(i.get("seconds", "—")),
                             "<td>%s%%</td>" % ec(i.get("ratio_pct", "—")),
                             "<td>%s</td>" % ec(i.get("cpu_avg", "—")),
                             "<td>%s</td>" % ec(i.get("pss_avg", "—"))])
        if rows:
            b.append("<h2>四、使用期间 vs 空闲期间</h2>")
            b.append('<div class="note">判定口径：<b>CPU &gt; 2% 或 磁盘读写合计 &gt; 0.5 MB/s '
                     '或 网络收发合计 &gt; 0.5 MB/s = 使用</b>。</div>')
            b.append(_tbl(["进程组", "使用样本", "占比", "使用期CPU均", "空闲样本", "占比",
                           "空闲期CPU均", "空闲期PSS均"], rows))

    # 放大倍数
    amp = ctx.get("amplification") or []
    if amp:
        b.append("<h2>五、各场景相对基线的放大倍数</h2>")
        rows = []
        for x in amp:
            ratio = ("∞" if x.get("ratio") is None and num(x.get("load"))
                     else ("%s×" % x["ratio"] if x.get("ratio") is not None else "—"))
            rows.append(["<td>%s</td>" % ec(x.get("scene", "—")),
                         "<td>%s</td>" % ec(x["metric"]), "<td>%s</td>" % ec(fmt(x.get("idle"))),
                         "<td>%s</td>" % ec(fmt(x.get("load"))),
                         "<td><b>%s</b></td>" % ec(ratio)])
        b.append(_tbl(["场景", "指标", "基线均值", "该场景均值", "放大倍数"], rows))
        b.append('<div class="note">基线场景为「%s」。放大倍数用于说明量级差异；'
                 '窗口不同、素材不同时<b>不宜作精确比较</b>。</div>'
                 % ec(ctx["scenarios"][0]["name"] if ctx["scenarios"] else "基线"))

    # 泄漏
    leak = find_leak(ctx)
    if leak:
        b.append("<h2>六、内存回落与泄漏判定</h2>")
        v = leak.get("verdict")
        msg = {"NO_LEAK": ("ok", "未发现内存泄漏迹象"),
               "SUSPECT": ("warn", "疑似内存泄漏，建议延长窗口复测"),
               "LEAK": ("bad", "判定存在内存泄漏")}.get(v, ("", str(v)))
        b.append('<div class="note %s"><b>%s</b></div>' % (msg[0], ec(msg[1])))
        ev = leak.get("evidence") or []
        if ev:
            rows = []
            for e in ev:
                rows.append(["<td>%s</td>" % ec(e.get("scenario", "—")),
                             "<td>%s</td>" % ec(e.get("proc", "—")),
                             "<td>%s</td>" % ec(fmt(e.get("first_mb"), " MB")),
                             "<td>%s</td>" % ec(fmt(e.get("last_mb"), " MB")),
                             "<td>%s</td>" % ec(fmt(e.get("delta_mb"), " MB")),
                             "<td>%s</td>" % ec(e.get("monotonic", "—")),
                             "<td>%s</td>" % ec(e.get("verdict", "—"))])
            b.append(_tbl(["场景", "进程", "首段均值", "末段均值", "变化", "单调度", "判定"], rows))
        b.append('<div class="note">判据：<b>末段均值 − 首段均值</b>（各取 1/4 样本，避免单点噪声）'
                 '配合<b>单调度</b>（相邻递增占比）。空闲期内存不归零属正常设计，'
                 '只要<b>无单调爬升</b>即可判无泄漏。</div>')

    # 覆盖度
    b.append("<h2>七、采集覆盖度与未测项</h2>")
    b.append('<div class="note warn"><b>采不到 ≠ 达标。</b>下列指标本次没有采到，'
             '一律显示「未采集」而<b>不填 0</b>。</div>')
    cov = list(ctx.get("coverage") or [])
    for c in checks:
        if c["status"] == "NA":
            cov.append({"item": c["label"], "status": "NA", "reason": "本次采集无该指标数据"})
    lab = {"OK": "✅ 已采", "DEGRADED": "⚠️ 口径降级", "NA": "❌ 未采集"}
    if cov:
        b.append(_tbl(["项", "状态", "说明"],
                      [["<td>%s</td>" % ec(c.get("item")),
                        "<td>%s</td>" % ec(lab.get(c.get("status"), c.get("status"))),
                        "<td>%s</td>" % ec(c.get("reason", ""))] for c in cov]))
    else:
        b.append('<div class="note ok">全部指标均已采到。</div>')

    # 口径声明
    b.append("<h2>八、口径声明</h2>")
    b.append("<ul>")
    for t in [
        "<b>网络列为整机口径</b>：Linux 没有逐进程网络字节计数（<code>/proc/&lt;pid&gt;/net/dev</code> "
        "属于整个网络命名空间），因此该列取自整机数据，<b>不可归因给单个应用/功能</b>。",
        "<b>内存判压力请用 <code>private_Dirty</code> 或 <code>PSS</code>，不要用 RSS</b>："
        "RSS 含 <code>RssFile</code>（mmap 文件页缓存，内核可随时回收），会被严重放大。",
        "<b>CPU 为单核口径</b>：100% = 1 个核，4 核跑满 = 400%。",
        "<b>评审红线（硬性）</b>：<b>单个进程的内存峰值超过 1 GB</b> —— 超过即需团队讨论评估，"
        "不是「达标 / 不达标」的二元判定。判定口径用 <code>private_Dirty</code>（真实匿名内存），"
        "<b>不用 RSS</b>（RSS 含可回收的 mmap 页缓存，会把页缓存误判成占用）。",
        "<b>其余阈值为业界参考值</b>（CPU ≤70%、%util ≤80%、错误率 ≤0.2% 等），"
        "<b>非业务验收标准</b>，<b>需各项目组结合自身业务具体讨论定夺</b>。"
        "本报告判定用<b>达标线</b>口径；源材料另有<b>警戒值</b>口径（CPU 75%~80%、磁盘繁忙率 &lt;70%），"
        "两者含义不同，<b>勿混用</b>。",
    ]:
        b.append("<li>%s</li>" % t)
    if kind == "summary":
        b.append("<li><b>跨应用对比的适用边界</b>：不同应用若采样窗口不同、素材不同，"
                 "均值不可直接精确比较。</li>")
    b.append("</ul>")

    # 已撤回
    wd = (ctx.get("analysis") or {}).get("withdrawn") or []
    if wd:
        b.append("<h2>九、已撤回的结论</h2>")
        b.append('<div class="note">保留纠错记录是报告质量的一部分。</div><ul>')
        for w in wd:
            b.append("<li>%s</li>" % ec(w))
        b.append("</ul>")

    an = ctx.get("analysis") or {}
    if an.get("bottleneck") or an.get("suggestions"):
        b.append("<h2>瓶颈分析与建议</h2>")
        if an.get("bottleneck"):
            b.append('<div class="note bad"><b>瓶颈定位</b>：%s</div>' % ec(an["bottleneck"]))
        if an.get("evidence"):
            b.append("<ul>" + "".join("<li>%s</li>" % ec(x) for x in an["evidence"]) + "</ul>")
        if an.get("suggestions"):
            b.append("<ol>" + "".join("<li>%s</li>" % ec(x) for x in an["suggestions"]) + "</ol>")

    body = "\n".join(b)
    page = PAGE
    # token 替换（一次性、不递归；CSS 里的裸 % 不会进来）
    for token, val in (("__TITLE__", ec(m.get("title") or KIND_TITLE[kind])),
                       ("__BODY__", body),
                       ("__TS__", ec(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))):
        page = page.replace(token, val)
    return page


# ---------------------------------------------------------------- 输入适配器

def load_k6(path):
    """k6 --summary-export 的 JSON → 统一 ctx（接口压测）。"""
    d = json.load(open(path, encoding="utf-8-sig"))
    m = d.get("metrics") or {}
    g = lambda k, f="avg": dig(m, "%s.%s" % (k, f))

    def val(k, f):
        v = dig(m, "%s.%s" % (k, f))
        return num(v)

    total = val("http_reqs", "count") or 0
    failed = val("http_req_failed", "rate")
    err_rate = round((failed or 0) * 100, 4) if failed is not None else None
    dur = val("http_req_duration", "avg")
    p95 = val("http_req_duration", "p(95)")
    if p95 is None:
        p95 = dig(m, "http_req_duration.thresholds")
    p99 = val("http_req_duration", "p(99)")
    maxrt = val("http_req_duration", "max")
    minrt = val("http_req_duration", "min")
    tps = val("http_reqs", "rate")
    data = {
        "kind": "perf",
        "app": "k6 压测",
        "meta": {"title": "接口性能测试报告", "tool": "k6",
                 "interval_s": None, "method": "k6 汇总导出",
                 "cpu_scope": "单核口径（100% = 1 个核）"},
        "quality": {"samples": int(total) if total else "—", "files": 1, "bad_rows": 0},
        "metrics": {
            "avg_rt": {"本次": {"avg": dur, "peak": maxrt, "p95": p95, "p99": p99, "min": minrt}},
            "p95_rt": {"本次": {"avg": p95, "peak": p95, "p95": p95, "p99": p95}},
            "p99_rt": {"本次": {"avg": p99, "peak": p99, "p95": p99, "p99": p99}},
            "max_rt": {"本次": {"avg": maxrt, "peak": maxrt}},
            "min_rt": {"本次": {"avg": minrt, "peak": minrt}},
            "tps": {"本次": {"avg": tps, "peak": tps}},
            "error_rate": {"本次": {"avg": err_rate, "peak": err_rate}},
            "success_rate": {"本次": {"avg": (round(100 - err_rate, 4)
                                              if err_rate is not None else None)}},
        },
        "coverage": [{"item": "服务端资源指标（CPU/内存/磁盘）", "status": "NA",
                      "reason": "k6 不采集服务端资源，请用 perf_collect.py 另采后合并"}],
    }
    d2 = data
    d2["_is_api"] = True
    return d2


def load_jmeter(path):
    """JMeter .jtl / .csv → 统一 ctx（接口压测）。"""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    if not rows:
        sys.exit("JMeter 结果为空：%s" % path)

    def g(r, *keys):
        for k in keys:
            if k in r and r[k] not in (None, ""):
                return r[k]
        return None

    times, ok = [], 0
    for r in rows:
        t = num(g(r, "elapsed", "timeStamp"))
        if t is not None:
            times.append(t)
        if str(g(r, "success", "responseCode") or "").lower() in ("true", "1"):
            ok += 1
        elif str(g(r, "responseCode") or "").startswith("2"):
            ok += 1
    times.sort()

    def pct(p):
        if not times:
            return None
        k = (len(times) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(times) - 1)
        return times[lo] + (times[hi] - times[lo]) * (k - lo)

    n = len(rows)
    err = round((n - ok) / n * 100, 4) if n else None
    avg = round(sum(times) / len(times), 2) if times else None
    t0 = num(g(rows[0], "timeStamp"))
    t1 = num(g(rows[-1], "timeStamp"))
    dur_s = ((t1 - t0) / 1000.0) if (t0 and t1 and t1 > t0) else None
    data = {
        "kind": "perf",
        "app": "JMeter 压测",
        "meta": {"title": "接口性能测试报告", "tool": "JMeter",
                 "method": "JMeter .jtl 汇总", "cpu_scope": "单核口径（100% = 1 个核）"},
        "quality": {"samples": n, "files": 1, "bad_rows": 0},
        "metrics": {
            "avg_rt": {"本次": {"avg": avg, "peak": (times[-1] if times else None),
                                "p95": pct(0.95), "p99": pct(0.99),
                                "min": (times[0] if times else None)}},
            "p95_rt": {"本次": {"avg": pct(0.95)}},
            "p99_rt": {"本次": {"avg": pct(0.99)}},
            "max_rt": {"本次": {"avg": (times[-1] if times else None)}},
            "min_rt": {"本次": {"avg": (times[0] if times else None)}},
            "tps": {"本次": {"avg": (round(n / dur_s, 2) if dur_s else None)}},
            "error_rate": {"本次": {"avg": err}},
            "success_rate": {"本次": {"avg": (round(100 - err, 4) if err is not None else None)}},
        },
        "coverage": [{"item": "服务端资源指标（CPU/内存/磁盘）", "status": "NA",
                      "reason": "JMeter 不采集服务端资源，请用 perf_collect.py 另采后合并"}],
    }
    data["_is_api"] = True
    return data


# ---------------------------------------------------------------- main

def main():
    _setup_io()
    ap = argparse.ArgumentParser(description="性能测试 · 报告生成（Markdown + 自包含 HTML）")
    ap.add_argument("--kind", choices=["monitor", "perf", "summary"],
                    help="报告体裁；不给则按输入自动判断")
    ap.add_argument("-i", "--input", action="append", default=[],
                    help="stats.json / results.json，可多次给（性能报告给空闲+负载两份）")
    ap.add_argument("--labels", default=None,
                    help="多输入时的场景名，逗号分隔，如：空闲,4路转码")
    ap.add_argument("--from-k6", default=None, help="k6 --summary-export 的 JSON")
    ap.add_argument("--from-jmeter", default=None, help="JMeter .jtl / .csv")
    ap.add_argument("--md", default=None, help="Markdown 输出路径")
    ap.add_argument("--html", default=None, help="HTML 输出路径（自包含）")
    ap.add_argument("--thresholds", default=None, help="阈值覆盖 JSON 文件")
    ap.add_argument("--fail-on", choices=["FAIL", "WARN"], default=None,
                    help="达到该等级则退出码 1（挂 CI 用）")
    args = ap.parse_args()

    labels = [x.strip() for x in args.labels.split(",")] if args.labels else None

    if args.from_k6:
        data = load_k6(args.from_k6)
        ctx = normalize(data, label="k6 压测", kind_hint="perf")
        ctx["is_api"] = True
    elif args.from_jmeter:
        data = load_jmeter(args.from_jmeter)
        ctx = normalize(data, label="JMeter 压测", kind_hint="perf")
        ctx["is_api"] = True
    elif args.input:
        ctxs = []
        for p in args.input:
            if not os.path.exists(p):
                sys.exit("输入文件不存在：%s" % p)
            d = json.load(open(p, encoding="utf-8-sig"))
            c = normalize(d, label=None, kind_hint=None)
            c["is_api"] = bool(d.get("_is_api"))
            ctxs.append(c)
        if len(ctxs) == 1:
            ctx = ctxs[0]
        else:
            ctx = merge_scenarios(ctxs, labels)
            ctx["is_api"] = any(c.get("is_api") for c in ctxs)
            # 多输入默认按性能报告（多场景对比）
        if args.kind:
            ctx["kind"] = args.kind
        elif len(ctxs) > 1:
            ctx["kind"] = "perf"
    else:
        ap.error("需要 -i/--input，或 --from-k6 / --from-jmeter")

    if args.kind:
        ctx["kind"] = args.kind

    if args.thresholds and os.path.exists(args.thresholds):
        ov_t = json.load(open(args.thresholds, encoding="utf-8-sig"))
        ctx["thresholds"].update({k: v for k, v in ov_t.items() if num(v) is not None})

    # 补充 meta（从输入推）
    m = ctx["meta"]
    m.setdefault("cpu_scope", "单核口径（100% = 1 个核；4 核跑满 = 400%）")
    m.setdefault("method", "进程树资源监控（父进程 + 全部子孙进程）")
    if not m.get("interval_s"):
        for sc in ctx["scenarios"]:
            for ps in (sc["procs"] or {}).values():
                w = ps.get("window") or []
                if len(w) == 2 and ps.get("samples"):
                    try:
                        t0 = datetime.datetime.strptime(w[0], "%Y-%m-%d %H:%M:%S")
                        t1 = datetime.datetime.strptime(w[1], "%Y-%m-%d %H:%M:%S")
                        m["interval_s"] = round((t1 - t0).total_seconds() / max(ps["samples"] - 1, 1), 1)
                    except Exception:
                        pass
                break
            break
    if not m.get("window"):
        wins = [ps.get("window") for sc in ctx["scenarios"] for ps in (sc["procs"] or {}).values()
                if ps.get("window")]
        if wins:
            m["window"] = "%s → %s" % (min(w[0] for w in wins), max(w[1] for w in wins))

    ctx["checks"] = build_checks(ctx)
    ctx["overall"] = overall(ctx["checks"])
    ctx["concerns"] = build_concerns(ctx)
    if not ctx.get("amplification"):
        ctx["amplification"] = amplification_of(ctx)

    md = render_markdown(ctx)
    ht = render_html(ctx)

    def _write(path, text, nl="\n"):
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline=nl) as f:
            f.write(text)
        print("OK  %s  (%d 字节)" % (path, len(text.encode("utf-8"))))

    if args.md:
        _write(args.md, md)
    if args.html:
        _write(args.html, ht)
    if not args.md and not args.html:
        # 都没给：默认落到当前目录
        _write("性能测试报告.md", md)
        _write("性能测试报告.html", ht)

    print("总判定：%s（通过 %d / 待确认 %d / 不通过 %d / 未采集 %d）"
          % (STATUS_LABEL[ctx["overall"]],
             sum(1 for c in ctx["checks"] if c["status"] == "PASS"),
             sum(1 for c in ctx["checks"] if c["status"] == "WARN"),
             sum(1 for c in ctx["checks"] if c["status"] == "FAIL"),
             sum(1 for c in ctx["checks"] if c["status"] == "NA")))

    if args.fail_on:
        want = STATUS_ORDER[args.fail_on]
        if STATUS_ORDER[ctx["overall"]] <= want and ctx["overall"] != "NA":
            print("--fail-on %s 触发，退出码 1" % args.fail_on)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
