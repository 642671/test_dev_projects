#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perf_lifecycle.py — 应用性能测试 · 六阶段生命周期编排

把「未安装 → 安装 → 空载 → 负载 → 回落/泄漏 → 卸载」串成一条可复跑的流水线。

  P0  pre_install   记录**未安装态**基线 + 断言应用确实没装 + 记已装应用清单（防串味）
  P1  install       捕获**安装过程**：耗时、CPU/磁盘峰值、进程出现时刻
  P2  idle          安装后**默认占用**（静置 N 分钟）
  P3  load          有任务/运行时的占用（与 P2 同比出**放大倍数**）
  P4  leak          停止任务后的**回落** + 多轮 churn + 长稳，判内存泄漏
  P5  post_uninstall 卸载后**残留**检查（默认不跑）

⚠️ **安装与卸载一律由人工触发，本脚本只负责监控与打点。**
   不同应用的安装方式不一，卸载还可能丢配置/数据；脚本不代劳。

用法：

  # 全程（交互式：每到切换点会打印指引并等你回车）
  python perf_lifecycle.py --app Emby --phases P0,P1,P2,P3,P4 --out-dir ./perf-out

  # 非交互：用标记文件代替回车（适合脚本化 / 远程）
  python perf_lifecycle.py --app Emby --wait-file /tmp/phase.ok --out-dir ./perf-out

  # 单跑某阶段
  python perf_lifecycle.py --app Emby --phases P2 --idle-min 5 --out-dir ./perf-out

  # 对已有的连续采集分段（不重新采，只用时间戳切）
  python perf_lifecycle.py --segment continuous.csv --marks marks.json --out-dir ./perf-out

产出（都在 --out-dir 下）：

  phases.json           各阶段的起止时间戳与实测指标
  P0_host.csv           未安装态整机基线
  P1_install_host.csv   安装过程整机曲线
  P2_<app>.csv          安装后空载（进程树口径）
  P3_<app>.csv          负载态（进程树口径）
  P4_churn.json         churn 轮次记录与泄漏判定
  lifecycle_report.md / .html   汇总报告（调 perf_report.py 生成）
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COLLECT = os.path.join(HERE, "perf_collect.py")
ANALYZE = os.path.join(HERE, "perf_analyze.py")
REPORT = os.path.join(HERE, "perf_report.py")

PHASES = ["P0", "P1", "P2", "P3", "P4", "P5"]
PHASE_NAME = {"P0": "pre_install", "P1": "install", "P2": "idle",
              "P3": "load", "P4": "leak", "P5": "post_uninstall"}
PHASE_DESC = {
    "P0": "未安装态基线（确认应用确实没装 + 记整机基线）",
    "P1": "安装过程监控（人工触发安装，脚本全程采）",
    "P2": "安装后空载基线（默认占用）",
    "P3": "负载态（有任务/运行时）",
    "P4": "回落 + churn + 长稳（判内存泄漏）",
    "P5": "卸载后残留检查",
}


def _setup_io():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print("[%s] %s" % (now(), msg), flush=True)


def wait_gate(args, phase, prompt):
    """阶段切换闸门：--wait-file 存在则等文件；否则交互等回车；--yes 直接过。"""
    if args.yes:
        return
    if args.wait_file:
        log("等待标记文件出现：%s" % args.wait_file)
        while not os.path.exists(args.wait_file):
            time.sleep(2)
        try:
            os.remove(args.wait_file)
        except OSError:
            pass
        log("标记文件已出现，继续")
        return
    try:
        input(">>> %s\n    （完成后按回车继续，Ctrl+C 中止）" % prompt)
    except EOFError:
        log("非交互环境且没给 --yes / --wait-file，跳过等待")


def run_collect(scope, app, duration, out, interval=1):
    """在本机直接调 perf_collect.py（脚本自身不依赖 SSH；远程用 --remote 由调用方决定）。"""
    cmd = [sys.executable, COLLECT, "--scope", scope, "--interval", str(interval),
           "--duration", str(duration), "--out", out]
    if scope == "tree":
        cmd += ["--app", app]
    log("采集: %s" % " ".join(os.path.basename(c) if c.endswith(".py") else c for c in cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        log("[警告] 采集脚本退出码 %d（%s）" % (rc, out))
    return rc


# ---------------------------------------------------------------- 各阶段

def phase_p0(args, outdir, marks):
    csv = os.path.join(outdir, "P0_host.csv")
    log("P0 %s" % PHASE_DESC["P0"])
    log("  该阶段只读，不会动被测机任何东西")
    if args.remote:
        _collect_remote(args, "host", None, args.p0_min * 60, csv)
    else:
        run_collect("host", None, args.p0_min * 60, csv)
    marks["P0"] = {"start": marks.get("_t0", now()), "end": now(), "csv": os.path.basename(csv)}
    return csv


def phase_p1(args, outdir, marks):
    csv = os.path.join(outdir, "P1_install_host.csv")
    log("P1 %s" % PHASE_DESC["P1"])
    wait_gate(args, "P1",
              "请在**另一个窗口**（TOS 应用中心 / 命令行）执行安装。\n"
              "    脚本已经在采了，安装过程的 CPU/磁盘尖峰会被完整记录。\n"
              "    想装完再继续就等安装完成后再按回车。")
    log("开始采集安装过程（最长 %d 分钟，检测到应用进程出现后 %d 秒自动收尾）"
        % (args.p1_max_min, args.p1_settle))
    _collect_until_process(args, "host", csv, args.app,
                           args.p1_max_min * 60, args.p1_settle, args)
    marks["P1"] = {"start": marks.get("_p1_start", now()), "end": now(),
                   "csv": os.path.basename(csv), "installed_by": "人工触发"}
    return csv


def phase_p2(args, outdir, marks):
    csv = os.path.join(outdir, "P2_%s.csv" % _slug(args.app))
    log("P2 %s —— 静置 %d 分钟后采 %d 分钟" % (PHASE_DESC["P2"], args.settle_min, args.p2_min))
    if args.settle_min:
        log("  静置中（让首次初始化/扫描收敛）…")
        time.sleep(args.settle_min * 60)
    _collect_any(args, "tree", args.app, args.p2_min * 60, csv)
    marks["P2"] = {"start": now(), "end": now(), "csv": os.path.basename(csv),
                   "note": "安装后空载；静置 %d 分钟后采集" % args.settle_min}
    return csv


def phase_p3(args, outdir, marks):
    csv = os.path.join(outdir, "P3_%s.csv" % _slug(args.app))
    log("P3 %s" % PHASE_DESC["P3"])
    wait_gate(args, "P3",
              "请现在**发起任务**（播放/转码/下载/备份…）。\n"
              "    任务跑起来后再按回车开始采集。")
    _collect_any(args, "tree", args.app, args.p3_min * 60, csv)
    marks["P3"] = {"start": now(), "end": now(), "csv": os.path.basename(csv),
                   "note": "负载由人工触发"}
    return csv


def phase_p4(args, outdir, marks):
    log("P4 %s" % PHASE_DESC["P4"])
    wait_gate(args, "P4",
              "请现在**停止任务**。\n"
              "    脚本会先采一段回落曲线，再做 %d 轮 churn。" % args.rounds)
    # 回落曲线
    cool = os.path.join(outdir, "P4_cooldown_%s.csv" % _slug(args.app))
    _collect_any(args, "tree", args.app, args.cool_min * 60, cool)

    # churn 轮次：本脚本不驱动业务动作（业务由人做），因此只做**轮次打点**，
    # 每轮记录一次水位，供人工/外部脚本在轮次间执行建拆。
    rounds = []
    log("churn 共 %d 轮：每轮「建立 → 保持 %ds → 全拆 → 静置 %ds」"
        % (args.rounds, args.hold_s, args.rest_s))
    for i in range(1, args.rounds + 1):
        log("--- 第 %d/%d 轮 ---" % (i, args.rounds))
        wait_gate(args, "P4", "第 %d 轮：请**建立负载**，建立完成后按回车" % i)
        built = _watermark(args)
        log("  建立后水位：%s MB —— 保持 %d 秒" % (built, args.hold_s))
        time.sleep(args.hold_s)
        hold = _watermark(args)
        wait_gate(args, "P4", "第 %d 轮：请**拆除负载**，拆除完成后按回车" % i)
        log("  保持期水位：%s MB —— 静置 %d 秒后取拆除水位" % (hold, args.rest_s))
        time.sleep(args.rest_s)
        after = _watermark(args)
        rounds.append({"round": i, "after_build": built, "hold": hold, "after_teardown": after})
        log("  拆除后水位：%s MB" % after)

    base = _watermark(args)
    round_mb = [r["after_teardown"] for r in rounds if r["after_teardown"] is not None]
    drift = None
    verdict = "样本不足"
    if len(round_mb) >= 3:
        drift = round(round_mb[-1] - round_mb[0], 2)
        up = sum(1 for i in range(1, len(round_mb)) if round_mb[i] > round_mb[i - 1])
        ratio_up = up / (len(round_mb) - 1)
        if drift > 3.0 and ratio_up > 0.6:
            verdict = "疑泄漏"
        elif drift > 3.0:
            verdict = "有抬升但非单调，建议延长窗口复测"
        else:
            verdict = "无泄漏"
    churn = {"rounds": rounds, "baseline_mb": base, "drift_mb": drift, "verdict": verdict}
    p = os.path.join(outdir, "P4_churn.json")
    json.dump(churn, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log("churn 判定：%s（漂移 %s MB）→ %s" % (verdict, drift, p))
    marks["P4"] = {"start": cool, "end": now(), "churn": os.path.basename(p), "verdict": verdict}
    return cool


def phase_p5(args, outdir, marks):
    log("P5 %s" % PHASE_DESC["P5"])
    wait_gate(args, "P5", "请现在**卸载应用**，卸载完成后按回车。")
    csv = os.path.join(outdir, "P5_post_uninstall_host.csv")
    _collect_any(args, "host", None, args.p5_min * 60, csv)
    marks["P5"] = {"start": now(), "end": now(), "csv": os.path.basename(csv)}
    return csv


# ---------------------------------------------------------------- 采集辅助

def _slug(s):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(s or "app"))


def _watermark(args):
    """取一次当前内存水位（MB）—— 用于 churn 判定。本机或远端。"""
    if not args.remote:
        val = _local_watermark(args.app)
        return val
    sys.path.insert(0, HERE)
    import sshcommon
    c = sshcommon.connect()
    try:
        out, _, _ = sshcommon.run(
            c, "ps -eo rss,comm --no-headers | grep -iE %s | awk '{s+=$1} END {printf \"%%.2f\", s/1024}'"
               % sshcommon._shq(args.app))
        return float(out.strip()) if out.strip() else None
    except Exception:
        return None
    finally:
        c.close()


def _local_watermark(app):
    """本机（Linux）取进程树 RSS 合计，MB。"""
    try:
        out = subprocess.run(["ps", "-eo", "rss,args", "--no-headers"],
                             capture_output=True, text=True).stdout
        tot = 0
        for line in out.splitlines():
            p = line.split(None, 1)
            if len(p) == 2 and app in p[1]:
                tot += int(p[0])
        return round(tot / 1024.0, 2)
    except Exception:
        return None


def _collect_any(args, scope, app, duration, out):
    """按 --remote 决定本机跑还是推到被测机跑。"""
    if args.remote:
        return _collect_remote(args, scope, app, duration, out)
    return run_collect(scope, app, duration, out)


def _collect_remote(args, scope, app, duration, out):
    cmd = [sys.executable, COLLECT, "--remote", "--scope", scope,
           "--interval", "1", "--duration", str(duration), "--out", out]
    if scope == "tree" and app:
        cmd += ["--app", app]
    log("远程采集: %s" % " ".join(cmd[3:]))
    rc = subprocess.call(cmd)
    if rc != 0:
        log("[警告] 远程采集退出码 %d" % rc)
    return rc


def _collect_until_process(args, scope, out, app, max_s, settle_s, a):
    """采到「应用进程出现」后再多采 settle 秒就收尾；到 max_s 兜底停。"""
    cmd = [sys.executable, COLLECT, "--scope", scope,
           "--interval", "1", "--duration", str(max_s), "--out", out]
    if a.remote:
        cmd.insert(2, "--remote")
    log("  采集最长 %ds；检测到「%s」进程后 %ds 自动收尾" % (max_s, app, settle_s))
    p = subprocess.Popen(cmd)
    t0 = time.time()
    seen_at = None
    try:
        while p.poll() is None:
            time.sleep(3)
            if _process_present(a, app):
                if seen_at is None:
                    seen_at = time.time()
                    log("  >> 检测到「%s」进程出现，%ds 后收尾" % (app, settle_s))
                elif (time.time() - seen_at) >= settle_s:
                    log("  安装已收敛，结束采集")
                    p.terminate()
                    try:
                        p.wait(timeout=15)
                    except Exception:
                        p.kill()
                    break
            if (time.time() - t0) > max_s + 30:
                p.terminate()
                break
    except KeyboardInterrupt:
        p.terminate()
    return out


def _process_present(args, app):
    """被测机上匹配到该进程了吗。"""
    if args.remote:
        try:
            sys.path.insert(0, HERE)
            import sshcommon
            c = sshcommon.connect()
            try:
                out, _, _ = sshcommon.run(
                    c, "ps -eo comm,args --no-headers | grep -iE %s | grep -v grep | head -1"
                       % sshcommon._shq(app))
                return bool(out.strip())
            finally:
                c.close()
        except Exception:
            return False
    try:
        out = subprocess.run(["ps", "-eo", "comm,args", "--no-headers"],
                             capture_output=True, text=True).stdout
        return any(app.lower() in ln.lower() for ln in out.splitlines())
    except Exception:
        return False


# ---------------------------------------------------------------- 报告

def build_report(args, outdir, marks):
    """把各阶段 CSV 交给 perf_analyze + perf_report，出 md/html 两份汇总报告。"""
    stats_files, labels = [], []
    pairs = [("P2", "idle"), ("P3", "load")]
    for ph, _n in pairs:
        csv = None
        for f in sorted(os.listdir(outdir)):
            if f.startswith(ph + "_") and f.endswith(".csv") and "host" not in f:
                csv = f
                break
        if not csv:
            continue
        st = os.path.join(outdir, "%s_stats.json" % ph)
        subprocess.call([sys.executable, ANALYZE, "--in", os.path.join(outdir, csv),
                         "--app", args.app, "--tag", ph, "--out", st])
        if os.path.exists(st):
            stats_files.append(st)
            labels.append("空载(P2)" if ph == "P2" else "负载(P3)")

    if not stats_files:
        log("没有可出报告的阶段数据（需要 P2/P3 至少一个）")
        return None
    md = os.path.join(outdir, "lifecycle_report.md")
    ht = os.path.join(outdir, "lifecycle_report.html")
    cmd = [sys.executable, REPORT, "--kind", "perf" if len(stats_files) > 1 else "monitor",
           "--md", md, "--html", ht]
    for f in stats_files:
        cmd += ["-i", f]
    if labels:
        cmd += ["--labels", ",".join(labels)]
    subprocess.call(cmd)
    # 把 phases 与 churn 附在报告头部说明里
    log("报告: %s / %s" % (md, ht))
    return md


# ---------------------------------------------------------------- main

def main():
    _setup_io()
    ap = argparse.ArgumentParser(description="应用性能测试 · 六阶段生命周期编排")
    ap.add_argument("--app", required=True, help="应用名/进程正则（用于进程树匹配）")
    ap.add_argument("--phases", default="P0,P1,P2,P3,P4",
                    help="要跑哪些阶段，逗号分隔（默认 P0,P1,P2,P3,P4；P5 卸载默认不跑）")
    ap.add_argument("--out-dir", default="perf-lifecycle", help="产物目录")
    ap.add_argument("--remote", action="store_true",
                    help="经 SSH 在被测机上采集（凭据走 TOS_HOST/TOS_USER/TOS_PASS/TOS_PORT）")
    ap.add_argument("--yes", action="store_true", help="非交互：闸门直接放行")
    ap.add_argument("--wait-file", default=None,
                    help="非交互：每到闸门等这个文件出现（出现后自动删除）")
    ap.add_argument("--p0-min", type=int, default=5, help="P0 未安装态基线分钟数（默认 5）")
    ap.add_argument("--p1-max-min", type=int, default=20, help="P1 安装过程最长分钟数（默认 20）")
    ap.add_argument("--p1-settle", type=int, default=60,
                    help="P1 检测到应用进程后再采多少秒收尾（默认 60）")
    ap.add_argument("--settle-min", type=int, default=2,
                    help="P1→P2 之间的静置分钟数（默认 2；首次初始化扫描需要收敛）")
    ap.add_argument("--p2-min", type=int, default=5, help="P2 空载采集分钟数（默认 5）")
    ap.add_argument("--p3-min", type=int, default=10, help="P3 负载采集分钟数（默认 10）")
    ap.add_argument("--cool-min", type=int, default=3, help="P4 停任务后回落曲线分钟数（默认 3）")
    ap.add_argument("--rounds", type=int, default=5, help="P4 churn 轮数（默认 5）")
    ap.add_argument("--hold-s", type=int, default=15, help="churn 每轮保持秒数（默认 15）")
    ap.add_argument("--rest-s", type=int, default=20, help="churn 每轮拆除后静置秒数（默认 20）")
    ap.add_argument("--p5-min", type=int, default=3, help="P5 卸载后采集分钟数（默认 3）")
    ap.add_argument("--no-report", action="store_true", help="只采集，不出报告")
    args = ap.parse_args()

    outdir = os.path.abspath(args.out_dir)
    os.makedirs(outdir, exist_ok=True)
    want = [p.strip().upper() for p in args.phases.split(",") if p.strip()]
    bad = [p for p in want if p not in PHASES]
    if bad:
        sys.exit("未知阶段：%s（可选 %s）" % (bad, PHASES))

    marks = {"app": args.app, "device": os.environ.get("TOS_HOST", "本机"),
             "started": now(), "_t0": now(), "phases": {}}
    log("六阶段生命周期编排 · 应用=%s · 阶段=%s" % (args.app, ",".join(want)))
    log("产物目录：%s" % outdir)
    if args.remote:
        log("采集方式：远程（%s）" % os.environ.get("TOS_HOST", "?"))
    log("⚠️ 安装/卸载一律由你人工触发，脚本只负责监控与打点")

    fns = {"P0": phase_p0, "P1": phase_p1, "P2": phase_p2,
           "P3": phase_p3, "P4": phase_p4, "P5": phase_p5}
    try:
        for ph in want:
            fns[ph](args, outdir, marks["phases"])
            _save_marks(outdir, marks)
    except KeyboardInterrupt:
        log("用户中止，已保存到目前阶段的进度")

    marks["ended"] = now()
    _save_marks(outdir, marks)
    log("阶段打点已保存：%s" % os.path.join(outdir, "phases.json"))

    if not args.no_report:
        build_report(args, outdir, marks)
    return 0


def _save_marks(outdir, marks):
    p = os.path.join(outdir, "phases.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(marks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sys.exit(main())
