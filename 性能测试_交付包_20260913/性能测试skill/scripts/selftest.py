#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py — 性能测试 skill 离线自检

**不连被测机、不需要 k6 / JMeter**，把本 skill 最容易悄悄坏掉的两件事在本地验一遍：

  A. **SSH 底座**：sshcommon 的函数契约还在不在（跨技能拷贝后最易漂移）
  B. **报告能力**：三种体裁能不能出 `.md` + 自包含 `.html`，且不违反几条硬约定

断言清单（每条打印 `PASS` / `FAIL`）：

  1. 环境摘要（Python + paramiko，走 `sshcommon.env_summary()`）
  2. `sshcommon` 八个核心函数 + 传输三件套都在
  3. 三种体裁（`monitor` / `perf` / `summary`）跑通，`.md` 与 `.html` 都生成且非空
  4. HTML **自包含**：无外链 `src`/`href`、无 `<script`、无 `@import`、无外链样式表
  5. HTML **无未替换的 `__TOKEN__` 占位符**（CSS 里含 `%`，只能走 token 替换）
  6. **缺失指标判 `NA` 不判 `FAIL`** —— 采不到 Full GC ≠ Full GC 超标
  7. `ec(None)` 兜底返回「（无）」而不是抛异常
  8. `judge(None, 70, "max") == "NA"` 且 `judge(999, 70, "max") == "FAIL"`

用法：

    python scripts/selftest.py
    python scripts/selftest.py --keep          # 保留临时产物,便于人工翻看

退出码 0 = 全部通过；1 = 有失败项。

> 样例来源：优先用 `references/examples/` 下的样例 JSON；**该目录为空时自动生成最小样例**
> 再跑（只是提示一句，不因此失败）。产物一律落 `tempfile.mkdtemp()` —— 本机 TEMP 路径含中文，
> 自己拼路径容易在编码上翻车，交给标准库。
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
PERF_REPORT = os.path.join(HERE, "perf_report.py")
EXAMPLES = os.path.join(SKILL_ROOT, "references", "examples")

sys.path.insert(0, HERE)
import perf_report as R      # noqa: E402  待测：报告引擎
import sshcommon as S        # noqa: E402  待测：SSH 底座

# ---------------------------------------------------------------- 断言框架

_N_PASS = 0
_N_FAIL = 0
_FAILED = []


def _setup_io():
    """Windows 控制台 cp936 下打印非 ASCII 会 UnicodeEncodeError —— 先掰成 utf-8。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def check(name, cond, detail=""):
    """一条断言。打印 PASS / FAIL + 说明。"""
    global _N_PASS, _N_FAIL
    if cond:
        _N_PASS += 1
        print("  PASS  %s%s" % (name, ("  —— %s" % detail) if detail else ""))
    else:
        _N_FAIL += 1
        _FAILED.append(name)
        print("  FAIL  %s%s" % (name, ("  —— %s" % detail) if detail else ""))
    return bool(cond)


def section(title):
    print("\n== %s ==" % title)


# ---------------------------------------------------------------- 自包含性正则
#
# 注意：SVG 的 xmlns="http://www.w3.org/2000/svg" 是**命名空间不是外链**，
# 下面这个正则只认 src / href 两个属性，所以天然不会命中它。

RE_EXT = re.compile(r"""\b(?:src|href)\s*=\s*["'](?:https?:)?//""")
RE_SCRIPT = re.compile(r"<\s*script", re.I)
RE_IMPORT = re.compile(r"@import", re.I)
RE_LINK_CSS = re.compile(r"<\s*link[^>]*stylesheet", re.I)
RE_TOKEN = re.compile(r"__[A-Z][A-Z0-9_]{2,}__")


# ---------------------------------------------------------------- 样例 JSON 生成
#
# 形状与 `perf_analyze.py` 的 stats.json 一致（见 references/results-schema.md），
# 量级取自真实采集结果：MultimediaServer 空载，进程树 4 个进程，CPU 0~1%，
# PSS 23.5 MB，private_Dirty 8.72 MB，RSS 34.4 MB，RssFile 25.7 MB。

def _ts(n):
    base = datetime.datetime(2026, 9, 13, 10, 0, 0)
    return [(base + datetime.timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S")
            for i in range(n)]


def _wave(n, lo, hi):
    """0~1 起伏的确定性序列（不用随机数，保证每次 selftest 产物一样）。"""
    return [round(lo + (hi - lo) * ((i * 3) % 7) / 7.0, 2) for i in range(n)]


def _four(peak, avg, p95, p99):
    return {"peak": peak, "avg": avg, "p95": p95, "p99": p99}


def _proc(cpu=0.4, pss=23.5, pvt=8.72, rss=34.4, filep=25.7, tree=4, n=60):
    ts = _ts(n)
    return {
        "segments": [{"file": "sample.csv", "n": n, "window": [ts[0], ts[-1]]}],
        "samples": n,
        "window": [ts[0], ts[-1]],
        "series": {
            "t": [t[11:] for t in ts],
            "cpu": _wave(n, max(cpu - 0.3, 0.0), cpu + 0.6),
            "pss": _wave(n, pss - 1.0, pss + 1.0),
            "pvt": _wave(n, pvt - 0.2, pvt + 0.3),
            "rss": _wave(n, rss - 1.0, rss + 1.0),
            "disk_r": _wave(n, 0.0, 0.4),
            "disk_w": _wave(n, 0.0, 0.3),
            "tx": _wave(n, 0.0, 0.02),
            "rx": _wave(n, 0.0, 0.05),
        },
        "usage": {"seconds": n // 2, "ratio_pct": 50.0, "cpu_avg": cpu,
                  "pss_avg": pss, "pvt_avg": pvt, "disk_w_avg": 0.15},
        "idle": {"seconds": n - n // 2, "ratio_pct": 50.0, "cpu_avg": 0.1,
                 "pss_avg": round(pss - 1.2, 2), "pvt_avg": round(pvt - 0.4, 2),
                 "disk_w_avg": 0.0},
        "peak_time": dict((k, ts[30]) for k in
                          ("cpu", "pss", "rss", "pvt", "anon", "file", "swap",
                           "disk_r", "disk_w", "tx", "rx", "tree")),
        "growth": {"first_mb": round(pvt - 0.3, 2), "last_mb": round(pvt + 0.3, 2),
                   "delta_mb": 0.6, "monotonic": 0.48, "verdict": "无增长"},
        "cpu": _four(round(cpu + 1.0, 2), cpu, round(cpu + 0.8, 2), round(cpu + 0.9, 2)),
        "pss": _four(round(pss + 1.0, 2), pss, round(pss + 0.8, 2), round(pss + 0.9, 2)),
        "rss": _four(round(rss + 1.2, 2), rss, round(rss + 1.0, 2), round(rss + 1.1, 2)),
        "pvt": _four(round(pvt + 0.4, 2), pvt, round(pvt + 0.3, 2), round(pvt + 0.35, 2)),
        "anon": _four(round(pvt + 0.5, 2), pvt, round(pvt + 0.4, 2), round(pvt + 0.45, 2)),
        "file": _four(round(filep + 0.5, 2), filep, round(filep + 0.4, 2), round(filep + 0.45, 2)),
        "swap": _four(0.0, 0.0, 0.0, 0.0),
        "disk_r": _four(0.8, 0.35, 0.7, 0.78),
        "disk_w": _four(0.6, 0.2, 0.5, 0.58),
        "tx": _four(0.04, 0.01, 0.03, 0.035),
        "rx": _four(0.09, 0.03, 0.07, 0.08),
        "tree": _four(tree, tree, tree, tree),
        "tx_total_MB": 1.8,
        "rx_total_MB": 5.4,
    }


def _stats(app, tag, procs):
    return {
        "app": app,
        "tag": tag,
        "generated": "2026-09-13 10:01:00",
        "quality": {"files": len(procs), "bad_rows": 0, "samples": 60 * len(procs),
                    "notes": "网络列为整机口径，不可归因单应用；"
                             "内存判压力请用 pvt(private_Dirty)/pss，不要用 rss"},
        "procs": procs,
    }


def build_samples():
    """构造三种体裁需要的最小样例。返回 {key: 数据}。"""
    return {
        "monitor": _stats("MultimediaServer", "P2",
                          {"mediaindex": _proc(cpu=0.4, pss=23.5, pvt=8.72)}),
        "idle": _stats("MultimediaServer", "P2",
                       {"mediaindex": _proc(cpu=0.4, pss=23.5, pvt=8.72)}),
        "load": _stats("MultimediaServer", "P3",
                       {"mediaindex": _proc(cpu=119.1, pss=97.4, pvt=41.2,
                                            rss=128.6, filep=58.1, tree=11)}),
        "summary": _stats("横向汇总", "20260913",
                          {"Emby": _proc(cpu=12.4, pss=210.5, pvt=88.2, tree=17),
                           "Jellyfin": _proc(cpu=8.7, pss=186.3, pvt=71.5, tree=13),
                           "qBittorrent": _proc(cpu=3.2, pss=96.1, pvt=140.2, tree=6)}),
        "minimal": {          # 只有 meta + 一个 CPU 值（验「缺指标判 NA 不判 FAIL」）
            "kind": "monitor",
            "app": "最小样例",
            "meta": {"title": "最小样例 · 缺指标不崩", "device": "离线自检"},
            "quality": {"files": 1, "bad_rows": 0, "samples": 3},
            "procs": {"p": {"samples": 3,
                            "window": ["2026-09-13 10:00:00", "2026-09-13 10:00:02"],
                            "cpu": {"avg": 0.4, "peak": 0.5}}},
        },
    }


def materialize(tmp, samples):
    """优先用 references/examples/ 里的样例；缺的写进临时目录。返回 ({key: path}, 是否自造)。"""
    names = {
        "monitor": ("monitor_stats.json", "example_monitor_stats.json"),
        "idle": ("idle_stats.json", "example_idle_stats.json"),
        "load": ("load_stats.json", "example_load_stats.json"),
        "summary": ("summary_stats.json", "example_summary_stats.json"),
        "minimal": (),
    }
    paths, selfmade = {}, False
    for key, data in samples.items():
        hit = None
        for nm in names.get(key, ()):
            p = os.path.join(EXAMPLES, nm)
            if os.path.isfile(p):
                hit = p
                break
        if key == "minimal":
            hit = None                     # 极简样例永远自己造（要精确控制缺字段）
        if hit:
            paths[key] = hit
            continue
        p = os.path.join(tmp, "sample_%s.json" % key)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        paths[key] = p
        selfmade = True
    return paths, selfmade


# ---------------------------------------------------------------- 跑报告

def run_report(args_list):
    """子进程跑 perf_report.py，返回 (rc, 合并输出)。列表参数，不经过 shell。"""
    cmd = [sys.executable, PERF_REPORT] + args_list
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def assert_outputs(tag, outdir, rc, log):
    """三种体裁共用的产物断言：`.md` 非空、`.html` 非空 + 自包含 + 无残留 token。"""
    md = os.path.join(outdir, "%s.md" % tag)
    ht = os.path.join(outdir, "%s.html" % tag)
    check("%s：退出码为 0" % tag, rc == 0, "rc=%d" % rc)
    check("%s：.md 生成且非空" % tag, os.path.isfile(md) and os.path.getsize(md) > 0,
          "%d 字节" % (os.path.getsize(md) if os.path.isfile(md) else 0))
    if not (os.path.isfile(ht) and os.path.getsize(ht) > 0):
        check("%s：.html 生成且非空" % tag, False, "未生成或为空")
        return
    check("%s：.html 生成且非空" % tag, True, "%d 字节" % os.path.getsize(ht))
    h = read(ht)

    ext = RE_EXT.findall(h)
    check("%s：HTML 无外链 src/href（自包含）" % tag, not ext, ", ".join(sorted(set(ext))[:3]))
    check("%s：HTML 无 <script>" % tag, not RE_SCRIPT.search(h))
    check("%s：HTML 无 @import" % tag, not RE_IMPORT.search(h))
    check("%s：HTML 无外链样式表 <link … stylesheet>" % tag, not RE_LINK_CSS.search(h))

    tok = sorted(set(RE_TOKEN.findall(h)))
    check("%s：HTML 无未替换的 __TOKEN__ 占位符" % tag, not tok, ", ".join(tok[:5]))
    # CSS 里含 width:100%，若走 % 格式化会被炸掉 —— 顺带验 CSS 没被吃掉
    check("%s：HTML 的 CSS 保留完好（含 width:100%%）" % tag, "width:100%" in h)


# ---------------------------------------------------------------- 环境自检（Step 0）
#
# 这是给「AI / 人」用的**快速入口**：只查环境，不跑报告。
# 输出要让读者一眼判断：缺什么、是不是必须、能不能自动补、补不了该复制哪条命令。

ENV_ROWS = []          # (依赖, 状态, 是否必须, 缺失时怎么办)


def _probe(cmd):
    """命令在不在。返回 (bool, 版本串)。"""
    import shutil
    exe = shutil.which(cmd)
    if not exe:
        return False, ""
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
        v = (out.stdout or out.stderr or "").strip().splitlines()
        return True, (v[0][:60] if v else exe)
    except Exception:
        return True, exe


def check_env_only():
    """只做环境自检（不跑报告），退出码 0 = 必需依赖齐备。"""
    _setup_io()
    print("=" * 74)
    print("性能测试 skill · 环境自检（Step 0）")
    print("=" * 74)
    print("本机 Python：%s" % sys.executable)
    print("工作目录：%s" % os.getcwd())
    print()

    rows = []
    ok_all = True

    # 1) Python 版本
    pv = sys.version_info
    py_ok = pv[:2] >= (3, 8)
    rows.append(("Python ≥ 3.8", "✅ %d.%d.%d" % (pv[0], pv[1], pv[2]) if py_ok
                 else "❌ %d.%d" % (pv[0], pv[1]),
                 "**必须**", "升级 Python；脚本无法自举解释器"))
    ok_all &= py_ok

    # 2) paramiko（远程采集用；缺了自动装）
    pk = None
    try:
        import importlib
        pk = importlib.import_module("paramiko")
    except ImportError:
        if os.environ.get("SKILL_NO_AUTO_INSTALL") == "1":
            rows.append(("paramiko", "❌ 未安装（自举已禁用）", "**必须**（远程采集）",
                         "`python -m pip install paramiko`"))
            ok_all = False
        else:
            print("[自举] 缺少 paramiko，正在自动安装 …")
            try:
                import subprocess as _sp
                _sp.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
                import importlib
                pk = importlib.import_module("paramiko")
            except Exception as e:
                rows.append(("paramiko", "❌ 自动安装失败", "**必须**（远程采集）",
                             "三选一：`pip install --user paramiko` ｜ "
                             "`pip install --break-system-packages paramiko` ｜ `apt install python3-paramiko`"))
                ok_all = False
    if pk is not None:
        rows.append(("paramiko", "✅ %s" % getattr(pk, "__version__", "?"),
                     "**必须**（远程采集）", "已就绪"))
    elif not any(r[0] == "paramiko" for r in rows):
        rows.append(("paramiko", "❌ 未安装", "**必须**（远程采集）", "`python -m pip install paramiko`"))
        ok_all = False

    # 3) 可选：压测工具（只有「接口压测」那条线需要）
    for name, cmd, hint in (
        ("k6", "k6", "`winget install --id GrafanaLabs.k6` 或从 grafana.com 下载 zip 解压到 PATH"),
        ("JMeter", "jmeter", "从 archive.apache.org 下载 apache-jmeter-5.x.zip 解压，或用 `perf_run.py --check-env` 看指引"),
        ("Locust", "locust", "`python -m pip install locust`"),
    ):
        got, ver = _probe(cmd if cmd != "Locust" else "locust")
        if got:
            rows.append((name, "✅ %s" % ver, "可选（仅接口压测）", "已就绪"))
        else:
            rows.append((name, "— 未安装", "可选（仅接口压测）", hint))

    # 4) 明确「不需要」的
    rows.append(("sshpass", "— 不需要", "**禁用**",
                 "Windows 下禁用 sshpass（对 TOS sshd 送不进密码，还会触发 PAM 锁账号）；一律走 paramiko"))

    # 输出表
    w = (26, 26, 18)
    print("%-*s %-*s %-*s %s" % (w[0], "依赖", w[1], "状态", w[2], "是否必须", "缺失时怎么办"))
    print("-" * 74)
    for name, st, must, hint in rows:
        print("%-*s %-*s %-*s %s" % (w[0], name, w[1], st, w[2], must, hint))
    print()
    print("被测机侧要求（脚本会在机上跑）：")
    print("  - Linux + python3（TOS 自带）；能读 /proc/<pid>/stat、smaps_rollup、/proc/net/dev")
    print("  - SSH 可达（TOS 默认端口 9222）；凭据走环境变量或 .env.local")
    print("  - 采集是**只读**的：不装包、不改配置、不启停服务")
    print()
    if ok_all:
        print(">>> 结论：必需依赖齐备，可以开始测试。")
        print("    下一步：python scripts/selftest.py        # 跑完整自检（含三体裁报告）")
        return 0
    print(">>> 结论：**必需依赖不齐**，请按上表「缺失时怎么办」处理后再跑。")
    print("    自举已尽量自动完成；装不上的按上面给的命令手动装。")
    print("    想关掉自动安装（只提示不装）：设 SKILL_NO_AUTO_INSTALL=1")
    return 1


def main():
    _setup_io()
    ap = argparse.ArgumentParser(description="性能测试 skill 离线自检")
    ap.add_argument("--keep", action="store_true", help="保留临时产物，便于人工查看")
    ap.add_argument("--check-env", action="store_true",
                    help="只做环境自检（快），不跑报告；退出码 0 = 必需依赖齐备")
    args = ap.parse_args()

    if args.check_env:
        return check_env_only()

    tmp = tempfile.mkdtemp(prefix="perf_selftest_")
    print("性能测试 skill 自检　临时目录：%s" % tmp)

    try:
        # ---------- 1. 环境摘要
        section("一、环境")
        try:
            summary = S.env_summary()
            check("环境摘要可打印（Python + paramiko）", True, summary)
            check("Python 版本 ≥ 3.8", sys.version_info[:2] >= (3, 8),
                  "当前 %d.%d" % sys.version_info[:2])
        except SystemExit as e:
            check("环境摘要可打印（Python + paramiko）", False,
                  "依赖自举失败：%s" % str(e).splitlines()[0])
        except Exception as e:
            check("环境摘要可打印（Python + paramiko）", False, repr(e))

        # ---------- 2. sshcommon 契约
        section("二、sshcommon 函数契约（防跨技能拷贝后漂移）")
        core = ["ensure_paramiko", "preflight", "env_summary", "load_env",
                "creds", "connect", "run", "banner"]
        miss = [n for n in core if not callable(getattr(S, n, None))]
        check("八个核心函数都在", not miss, "缺：" + ", ".join(miss) if miss else "8/8")
        trio = ["put_file", "get_file", "remove_remote"]
        miss3 = [n for n in trio if not callable(getattr(S, n, None))]
        check("传输三件套都在", not miss3, "缺：" + ", ".join(miss3) if miss3 else "3/3")

        # ---------- 3~5. 三种体裁跑通 + 自包含 + token
        section("三、三种体裁（md + 自包含 html）")
        paths, selfmade = materialize(tmp, build_samples())
        if selfmade:
            print("  [提示] references/examples/ 下缺少样例 JSON，"
                  "本次用**自动生成的最小样例**跑（不因此失败）")
        print("  [样例] %s" % "、".join("%s=%s" % (k, os.path.basename(v))
                                      for k, v in sorted(paths.items())))

        rc, log = run_report(["--kind", "monitor", "-i", paths["monitor"],
                              "--md", os.path.join(tmp, "monitor.md"),
                              "--html", os.path.join(tmp, "monitor.html")])
        if rc != 0:
            print(log)
        assert_outputs("monitor", tmp, rc, log)

        rc, log = run_report(["--kind", "perf",
                              "-i", paths["idle"], "-i", paths["load"],
                              "--labels", "空闲,负载",
                              "--md", os.path.join(tmp, "perf.md"),
                              "--html", os.path.join(tmp, "perf.html")])
        if rc != 0:
            print(log)
        assert_outputs("perf", tmp, rc, log)

        rc, log = run_report(["--kind", "summary", "-i", paths["summary"],
                              "--md", os.path.join(tmp, "summary.md"),
                              "--html", os.path.join(tmp, "summary.html")])
        if rc != 0:
            print(log)
        assert_outputs("summary", tmp, rc, log)

        # ---------- 6. 缺失指标判 NA 不判 FAIL
        section("四、缺字段的健壮性（采不到 ≠ 达标）")
        mini_md = os.path.join(tmp, "minimal.md")
        mini_ht = os.path.join(tmp, "minimal.html")
        rc, log = run_report(["--kind", "monitor", "-i", paths["minimal"],
                              "--md", mini_md, "--html", mini_ht])
        check("极简输入（只有 meta + 一个 CPU 值）不抛异常", rc == 0, "rc=%d" % rc)
        verdict = ""
        for line in log.splitlines():
            if line.startswith("总判定"):
                verdict = line.strip()
        # ⚠️ 不能直接找「不通过」三个字 —— 计数列里也有「不通过 0」，会误判。
        #    只认判定标签本身（`✗ 不通过`）。
        check("极简输入的判定不是「不通过」",
              bool(verdict) and R.STATUS_LABEL["FAIL"] not in verdict,
              verdict or "未取到「总判定」行")
        # 同一条走模块级复核（子进程只看到打印，这里直接看内部状态）
        ctx = R.normalize(json.load(open(paths["minimal"], encoding="utf-8")),
                          label=None, kind_hint="monitor")
        ctx["checks"] = R.build_checks(ctx)
        got = R.overall(ctx["checks"])
        check("模块级总判定为 NA 或 PASS（不是 FAIL）", got in ("NA", "PASS"), "overall=%s" % got)
        na_cnt = sum(1 for c in ctx["checks"] if c["status"] == "NA")
        check("缺的指标确实被判成 NA（未填 0）", na_cnt > 0, "NA 项 %d 条" % na_cnt)

        # ---------- 7~8. 两个纯函数边界
        section("五、纯函数边界")
        check("ec(None) 返回「（无）」而非抛异常",
              R.ec(None) == "（无）", "ec(None)=%r" % R.ec(None))
        check("judge(None, 70, 'max') == 'NA'", R.judge(None, 70, "max") == "NA",
              R.judge(None, 70, "max"))
        check("judge(999, 70, 'max') == 'FAIL'", R.judge(999, 70, "max") == "FAIL",
              R.judge(999, 70, "max"))

    finally:
        if args.keep:
            print("\n[保留] 临时产物在：%s" % tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    section("汇总")
    print("  %d 通过 / %d 失败" % (_N_PASS, _N_FAIL))
    if _N_FAIL:
        print("  失败项：" + "、".join(_FAILED))
        return 1
    print("  性能测试 skill 自检全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
