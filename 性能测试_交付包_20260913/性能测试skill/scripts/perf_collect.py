#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perf_collect.py — 性能测试 · 进程树 / 整机资源采集器

按秒采集，实时逐行落盘 CSV（中断也不丢）。两种口径：

  tree  —— 进程树口径（默认）：匹配根进程 + **全部子孙进程**，逐项求和
  host  —— 整机口径：CPU 分解 / 内存 / swap / load / 磁盘 / 网络

口径要点（详见 references/memory-accounting.md、methodology-pitfalls.md）：

  * CPU 为**单核口径**（100% = 1 个核，4 核跑满 = 400%），用两次采样差值算
  * PSS / private_Dirty 取自 /proc/<pid>/smaps_rollup（缺则回退逐段读 /proc/<pid>/smaps）
  * **必须按进程树统计**：转码在 ffmpeg 子进程里，fork-per-connection 服务的内存
    长在子进程上，只盯父进程会漏掉大部分开销
  * 网络是**整机口径**（Linux 无逐进程网络计数），不可归因给单个应用
  * 磁盘写扣除 cancelled_write_bytes，否则虚高

用法：

  # 1) 在被测机上直接跑（脚本自包含，只用标准库）
  python3 perf_collect.py --app Emby --duration 300 --out Emby_idle.csv

  # 2) 在本机跑，经 SSH 推到被测机执行并取回 CSV
  python perf_collect.py --remote --app Emby --duration 300 --out Emby_idle.csv
  #    凭据走 TOS_HOST / TOS_USER / TOS_PASS / TOS_PORT 或同目录 .env.local

  # 3) 整机口径
  python perf_collect.py --scope host --duration 300 --out host_baseline.csv

  # 4) 只看要跑什么，不真跑
  python perf_collect.py --remote --app Emby --dry-run
"""
import argparse
import csv
import datetime
import os
import signal
import sys
import time

MB = 1024.0 * 1024.0


def _clk_tck():
    """每秒时钟 tick 数（通常 100）。Windows 没有 os.sysconf —— 只在真正采集时取。"""
    try:
        return float(os.sysconf("SC_CLK_TCK"))
    except (AttributeError, ValueError, OSError):
        return 100.0


TREE_HEADERS = [
    "时间", "CPU占用(%)", "PSS占用(MB)", "RSS占用(MB)", "private_Dirty占用(MB)",
    "swap占用(MB)", "磁盘读速度(MB/s)", "磁盘写速度(MB/s)",
    "网络发送速度(MB/s)", "网络接收速度(MB/s)",
    "RssAnon(MB)", "RssFile(MB)", "进程数",
]
#  前 10 列与既有采集器 CSV 保持一致，便于复用既有分析产物

HOST_HEADERS = [
    "时间", "CPU占用(%)", "用户态(%)", "系统态(%)", "iowait(%)", "软中断(%)",
    "内存使用(%)", "内存可用(MB)", "swap使用(MB)",
    "load1", "load5", "load15",
    "磁盘读(MB/s)", "磁盘写(MB/s)",
    "网络发送(MB/s)", "网络接收(MB/s)",
]


def _setup_io():
    """Windows 控制台 cp936 下打印非 ASCII 会 UnicodeEncodeError —— 先把 stdout 掰成 utf-8。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ---------------------------------------------------------------- 进程树发现

def read_all_stats():
    """一次扫 /proc，返回 {pid: (ppid, comm, utime, stime)}。"""
    out = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            with open("/proc/%d/stat" % pid, "rb") as f:
                line = f.read().decode("utf-8", "replace")
            i = line.rfind(")")
            comm = line[line.find("(") + 1:i]
            f_ = line[i + 2:].split()
            out[pid] = (int(f_[1]), comm, int(f_[11]), int(f_[12]))
        except (IOError, OSError, IndexError, ValueError):
            continue
    return out


def _is_self_or_helper(pid, cmd):
    """判断这个进程是不是采集器自己 / 同类辅助进程。

    ⚠️ **必须排除**：`--app` 是正则，而采集器自己的命令行里就含这个正则
    （`python3 perf_collect.py --app MultimediaServer`），不排除会**匹配到自身**，
    把采集器的 CPU/内存算进被测进程树 —— 实测会凭空多出 1 个进程、约 12 MB PSS。
    """
    if pid == os.getpid():
        return True
    low = (cmd or "").lower()
    for marker in ("perf_collect.py", "perf_collect ", "monitor_terrasync.py", "proc_monitor.py"):
        if marker in low:
            return True
    return False


def discover_tree(app=None, root_pid=None):
    """返回进程树内全部 PID。--app 走命令行/进程名正则匹配根进程，再递归收子孙。"""
    import re
    stats = read_all_stats()

    if root_pid is not None:
        roots = [root_pid] if root_pid in stats else []
    else:
        pat = re.compile(app)
        roots = []
        for pid, (_, comm, _, _) in stats.items():
            # 先取完整命令行：comm 被截断到 15 字符，且要用来判自身
            cmd = ""
            try:
                with open("/proc/%d/cmdline" % pid, "rb") as f:
                    cmd = f.read().decode("utf-8", "replace").replace("\x00", " ").strip()
            except (IOError, OSError):
                cmd = comm
            if _is_self_or_helper(pid, cmd):
                continue
            if pat.search(comm) or (cmd and pat.search(cmd)):
                roots.append(pid)

    if not roots:
        return []

    # 递归收子孙
    children = {}
    for pid, (ppid, _, _, _) in stats.items():
        children.setdefault(ppid, []).append(pid)

    tree, stack = set(), list(roots)
    while stack:
        p = stack.pop()
        if p in tree or p not in stats:
            continue
        # 子孙里也要剔掉采集器自己（它可能是被测进程 fork 出来的？不会，但防御性处理）
        if p != root_pid and _is_self_or_helper(p, ""):
            try:
                with open("/proc/%d/cmdline" % p, "rb") as f:
                    c = f.read().decode("utf-8", "replace").replace("\x00", " ").strip()
                if _is_self_or_helper(p, c):
                    continue
            except (IOError, OSError):
                pass
        tree.add(p)
        stack.extend(children.get(p, []))
    return sorted(tree)


# ---------------------------------------------------------------- 进程级读数

def read_proc_cpu(pid):
    """返回 (utime, stime)，单位时钟 tick。"""
    with open("/proc/%d/stat" % pid, "rb") as f:
        line = f.read().decode("utf-8", "replace")
    fields = line[line.rfind(")") + 2:].split()
    return int(fields[11]), int(fields[12])


def read_mem(pid):
    """返回 dict(MB)：pss/rss/private_dirty/rss_anon/rss_file/swap。

    ⚠️ 字段分布在两个文件里，别搞混（本机内核 6.12 实测）：
        /proc/<pid>/status        → VmRSS、VmSwap、**RssAnon、RssFile**、RssShmem
        /proc/<pid>/smaps_rollup  → Pss、Private_Dirty、Private_Clean、**Anonymous**
        （smaps_rollup 里**没有** Rss_Anon / Rss_File 这两个名字，只有 Anonymous）
    Pss/Private_Dirty 优先读 smaps_rollup（一次读完，快一个数量级）；
    老内核缺该文件时回退逐段读 /proc/<pid>/smaps 求和。
    """
    rss = swap = anon = filep = 0.0
    try:
        with open("/proc/%d/status" % pid, "rb") as f:
            for line in f.read().decode("utf-8", "replace").splitlines():
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1]) / 1024.0
                elif line.startswith("VmSwap:"):
                    swap = int(line.split()[1]) / 1024.0
                elif line.startswith("RssAnon:"):
                    anon = int(line.split()[1]) / 1024.0
                elif line.startswith("RssFile:"):
                    filep = int(line.split()[1]) / 1024.0
    except (IOError, OSError, ValueError, IndexError):
        pass

    pss = pvt = 0.0
    try:
        with open("/proc/%d/smaps_rollup" % pid, "rb") as f:
            for line in f.read().decode("utf-8", "replace").splitlines():
                if line.startswith("Pss:"):
                    pss = int(line.split()[1]) / 1024.0
                elif line.startswith("Private_Dirty:"):
                    pvt = int(line.split()[1]) / 1024.0
                elif line.startswith("Anonymous:") and not anon:
                    anon = int(line.split()[1]) / 1024.0
    except (IOError, OSError, ValueError, IndexError):
        # 回退：逐段读 smaps 求和（工作区已验证算法）
        try:
            with open("/proc/%d/smaps" % pid, "rb") as f:
                for line in f.read().decode("utf-8", "replace").splitlines():
                    p = line.split()
                    if len(p) < 2 or not p[1].isdigit():
                        continue
                    if line.startswith("Pss:"):
                        pss += int(p[1]) / 1024.0
                    elif line.startswith("Private_Dirty:"):
                        pvt += int(p[1]) / 1024.0
                    elif line.startswith("Rss:") and not anon:
                        anon += int(p[1]) / 1024.0
        except (IOError, OSError):
            pass

    if not filep and rss:
        filep = max(rss - anon, 0.0)      # RssFile 拿不到时按 Rss - RssAnon 推

    return {"pss": pss, "rss": rss, "private_dirty": pvt,
            "rss_anon": anon, "rss_file": filep, "swap": swap}


def read_io(pid):
    r = w = c = 0
    try:
        with open("/proc/%d/io" % pid, "rb") as f:
            for line in f.read().decode("utf-8", "replace").splitlines():
                if line.startswith("read_bytes:"):
                    r = int(line.split()[1])
                elif line.startswith("write_bytes:"):
                    w = int(line.split()[1])
                elif line.startswith("cancelled_write_bytes:"):
                    c = int(line.split()[1])
    except (IOError, OSError, ValueError, IndexError):
        pass
    return r, w, c


# ---------------------------------------------------------------- 整机口径读数

def get_default_iface():
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                p = line.split()
                if len(p) >= 2 and p[1] == "00000000":
                    return p[0]
    except (IOError, OSError):
        pass
    return None


def read_net(iface=None):
    """整机网络累计字节。Linux 无逐进程网络计数 —— 这是**整机口径**。"""
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                name = p[0].rstrip(":")
                if name == "lo":
                    continue
                if iface and name != iface:
                    continue
                rx += int(p[1])
                tx += int(p[9])
    except (IOError, OSError, ValueError, IndexError):
        pass
    return rx, tx


def read_cpu_stat():
    """返回 (busy, total, 明细 dict) —— 整机 CPU 累计 jiffies。"""
    with open("/proc/stat") as f:
        p = f.readline().split()
    v = [int(x) for x in p[1:11]]
    user, nice, system, idle, iowait, irq, softirq, steal = v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7]
    total = sum(v)
    busy = total - idle - iowait
    return busy, total, {"user": user + nice, "system": system, "iowait": iowait,
                         "softirq": softirq + irq, "steal": steal}


def read_meminfo():
    d = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, rest = line.partition(":")
                d[k] = int(rest.split()[0])      # kB
    except (IOError, OSError, ValueError, IndexError):
        pass
    return d


def read_diskstats():
    """返回 (读扇区, 写扇区) 合计，单位 512B 扇区。"""
    r = w = 0
    try:
        with open("/proc/diskstats") as f:
            for line in f:
                p = line.split()
                if len(p) < 10:
                    continue
                name = p[2]
                if name.startswith(("loop", "ram", "dm-", "sr")):
                    continue
                # 只统计整盘（分区名以数字结尾的跳过，避免双计）
                if name[-1].isdigit() and not name.startswith(("nvme", "mmcblk")):
                    continue
                if name.startswith(("nvme", "mmcblk")) and "p" in name:
                    continue
                r += int(p[5])
                w += int(p[9])
    except (IOError, OSError, ValueError, IndexError):
        pass
    return r, w


def read_loadavg():
    try:
        with open("/proc/loadavg") as f:
            p = f.read().split()
        return float(p[0]), float(p[1]), float(p[2])
    except (IOError, OSError, ValueError, IndexError):
        return 0.0, 0.0, 0.0


# ---------------------------------------------------------------- 采样循环

def _on_sigterm(signum, frame):
    """kill 时优雅退出，同 Ctrl+C，走 finally 收尾落盘。"""
    raise KeyboardInterrupt


def sample_tree(pids, prev):
    """采一次进程树；返回 (行, 新 prev)。pids 为空时返回 None。"""
    cpu_ticks = io_now = 0
    mem = {"pss": 0.0, "rss": 0.0, "private_dirty": 0.0,
           "rss_anon": 0.0, "rss_file": 0.0, "swap": 0.0}
    cur_cpu = {}
    for pid in pids:
        try:
            cur_cpu[pid] = read_proc_cpu(pid)
        except (IOError, OSError, ValueError, IndexError):
            continue
        m = read_mem(pid)
        for k in mem:
            mem[k] += m[k]
        try:
            io_now += sum(read_io(pid)[:2])
        except Exception:
            pass

    if not cur_cpu:
        return None, prev

    # CPU：两次差值的和 —— 单核口径
    cpu_pct = 0.0
    if prev.get("cpu"):
        for pid, (u, s) in cur_cpu.items():
            pu, ps = prev["cpu"].get(pid, (u, s))
            cpu_pct += (u - pu) + (s - ps)
        cpu_pct = cpu_pct / _clk_tck() * 100.0

    rd = wr = 0.0
    if prev.get("io") is not None:
        rd = (io_now - prev["io"]) / MB
    net_tx = net_rx = 0.0
    cur_net = read_net(prev.get("iface"))
    if prev.get("net") is not None:
        net_tx = (cur_net[1] - prev["net"][1]) / MB
        net_rx = (cur_net[0] - prev["net"][0]) / MB

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [ts, round(cpu_pct, 2), round(mem["pss"], 2), round(mem["rss"], 2),
           round(mem["private_dirty"], 2), round(mem["swap"], 2),
           round(rd, 2), round(wr, 2), round(net_tx, 2), round(net_rx, 2),
           round(mem["rss_anon"], 2), round(mem["rss_file"], 2), len(cur_cpu)]
    return row, {"cpu": cur_cpu, "io": io_now, "net": cur_net,
                 "iface": prev.get("iface")}


def sample_host(prev):
    busy, total, parts = read_cpu_stat()
    mi = read_meminfo()
    ds = read_diskstats()
    net = read_net(prev.get("iface"))

    d_total = d_busy = 0
    d_parts = {k: 0 for k in parts}
    if prev.get("cpu"):
        pb, pt, pp = prev["cpu"]
        d_total, d_busy = total - pt, busy - pb
        d_parts = {k: parts[k] - pp[k] for k in parts}

    def pct(x):
        return round(x / d_total * 100.0, 2) if d_total > 0 else 0.0

    cpu_pct = pct(d_busy)
    rd = wr = 0.0
    if prev.get("disk") is not None:
        rd = (ds[0] - prev["disk"][0]) * 512 / MB
        wr = (ds[1] - prev["disk"][1]) * 512 / MB
    tx = rx = 0.0
    if prev.get("net") is not None:
        tx = (net[1] - prev["net"][1]) / MB
        rx = (net[0] - prev["net"][0]) / MB

    mt = mi.get("MemTotal", 0)
    ma = mi.get("MemAvailable", 0)
    st = mi.get("SwapTotal", 0)
    sf = mi.get("SwapFree", 0)
    l1, l5, l15 = read_loadavg()

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [ts, cpu_pct, pct(d_parts["user"]), pct(d_parts["system"]),
           pct(d_parts["iowait"]), pct(d_parts["softirq"]),
           round((mt - ma) / mt * 100.0, 2) if mt else 0.0,
           round(ma / 1024.0, 1), round((st - sf) / 1024.0, 1),
           l1, l5, l15, round(rd, 2), round(wr, 2), round(tx, 2), round(rx, 2)]
    return row, {"cpu": (busy, total, parts), "disk": ds, "net": net,
                 "iface": prev.get("iface")}


def collect(scope, app, root_pid, interval, duration, out_path):
    headers = HOST_HEADERS if scope == "host" else TREE_HEADERS
    iface = get_default_iface()

    print("采集口径: %s" % ("整机" if scope == "host" else "进程树"))
    if scope == "tree":
        print("匹配目标: %s" % (("PID=%d" % root_pid) if root_pid else app))
    print("默认网卡: %s（网络为整机口径，不可归因单应用）" % (iface or "全部非 lo 网卡合计"))
    print("输出文件: %s" % out_path)
    print("-" * 60)

    f = open(out_path, "w", newline="", encoding="utf-8-sig")
    w = csv.writer(f)
    w.writerow(headers)
    f.flush()

    prev = {"iface": iface}
    # 首次读取作基线（CPU / io / net 都需要两次采样求差）
    if scope == "host":
        prev["cpu"] = read_cpu_stat()
        prev["disk"] = read_diskstats()
        prev["net"] = read_net(iface)
    else:
        pids = discover_tree(app, root_pid)
        prev["cpu"] = {}
        for pid in pids:
            try:
                prev["cpu"][pid] = read_proc_cpu(pid)
            except Exception:
                pass
        prev["io"] = sum((read_io(p)[0] + read_io(p)[1]) for p in pids) if pids else 0
        prev["net"] = read_net(iface)

    start, count, alive_warned = time.time(), 0, False
    try:
        while True:
            time.sleep(interval)
            if scope == "host":
                row, prev = sample_host(prev)
            else:
                pids = discover_tree(app, root_pid)
                if not pids:
                    if not alive_warned:
                        print("[警告] 未匹配到进程树，仍继续采样（等进程出现）", file=sys.stderr)
                        alive_warned = True
                    prev = {"cpu": {}, "io": None, "net": read_net(iface), "iface": iface}
                    continue
                alive_warned = False
                # 新增子进程：其 CPU 基线取当前值，避免把历史累计算进来
                for pid in pids:
                    if pid not in (prev.get("cpu") or {}):
                        try:
                            prev.setdefault("cpu", {})[pid] = read_proc_cpu(pid)
                        except Exception:
                            pass
                row, prev = sample_tree(pids, prev)
                if row is None:
                    continue

            w.writerow(row)
            f.flush()
            count += 1
            if count % 30 == 0 or count <= 3:
                print("  [%d] %s" % (count, " | ".join(str(x) for x in row[:6])), flush=True)

            if duration and (time.time() - start) >= duration:
                break
    except KeyboardInterrupt:
        print("\n用户中断，正在保存…")
    finally:
        f.close()
        print("完成：共采集 %d 个采样点，已保存到 %s" % (count, out_path))
    return count


# ---------------------------------------------------------------- SSH 远程模式

def run_remote(args):
    """把自身推到被测机执行，再把 CSV 取回本地。

    传输走 sshcommon.put_file/get_file —— **SFTP 优先、不可用自动回退 base64**，
    因为有些 TOS 机器把 sftp 子系统关了（实测 10.18.15.179 就是），
    同一批机器配置并不一致。
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sshcommon

    c = sshcommon.connect()
    remote_py = "/tmp/perf_collect.py"
    remote_csv = "/tmp/perf_collect_out.csv"
    local = os.path.abspath(__file__)
    print("[远程] 上传 %s -> %s" % (os.path.basename(local), remote_py))
    sshcommon.put_file(c, local, remote_py)

    cmd = ("python3 %s --scope %s --interval %s" % (remote_py, args.scope, args.interval))
    if args.duration:
        cmd += " --duration %s" % args.duration
    if args.scope == "tree":
        cmd += (" --pid %s" % args.pid) if args.pid else (" --app %s" % _shq(args.app))
    cmd += " --out %s" % remote_csv

    if args.dry_run:
        print("[dry-run] 将在被测机执行:\n  %s" % cmd)
        c.close()
        return 0

    print("[远程] 执行: %s" % cmd)
    out, err, _ = sshcommon.run(c, cmd, timeout=(args.duration or 3600) + 180)
    sys.stdout.write(out)
    if err.strip():
        sys.stderr.write(err)

    print("[远程] 取回 %s -> %s" % (remote_csv, args.out))
    try:
        sshcommon.get_file(c, remote_csv, args.out)
        print("OK 已保存: %s" % args.out)
    except Exception as e:
        sys.exit("取回 CSV 失败：%s\n（脚本在机上仍留着 %s，可手工取）" % (e, remote_csv))
    finally:
        for p in (remote_py, remote_csv):
            sshcommon.remove_remote(c, p)
    c.close()
    return 0


def _shq(s):
    return "'" + str(s).replace("'", "'\\''") + "'"


def main():
    _setup_io()
    signal.signal(signal.SIGTERM, _on_sigterm)

    ap = argparse.ArgumentParser(
        description="性能测试 · 进程树 / 整机资源采集器（每秒采样 → CSV）")
    ap.add_argument("--scope", choices=["tree", "host"], default="tree",
                    help="tree=进程树口径（默认）；host=整机口径")
    ap.add_argument("--app", default=None, help="进程名/命令行正则（tree 模式，与 --pid 二选一）")
    ap.add_argument("--pid", type=int, default=None, help="直接指定根进程 PID")
    ap.add_argument("--interval", type=float, default=1.0, help="采样间隔秒（默认 1）")
    ap.add_argument("--duration", type=int, default=0, help="采集秒数，0=一直采直到 Ctrl+C")
    ap.add_argument("--out", default=None, help="CSV 输出路径")
    ap.add_argument("--remote", action="store_true",
                    help="经 SSH 推到被测机执行并取回（凭据走 TOS_HOST/TOS_USER/TOS_PASS/TOS_PORT）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的命令，不真跑")
    args = ap.parse_args()

    if args.scope == "tree" and not args.app and not args.pid:
        sys.exit("tree 模式需要 --app <进程名/正则> 或 --pid <PID>")

    if not args.out:
        tag = "host" if args.scope == "host" else (args.app or ("pid%d" % args.pid))
        tag = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(tag))
        args.out = "%s_%s.csv" % (tag, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

    if args.remote:
        return run_remote(args)

    return 0 if collect(args.scope, args.app, args.pid, args.interval,
                        args.duration, args.out) is not None else 1


if __name__ == "__main__":
    sys.exit(main())
