#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perf_run.py — 性能测试 · k6 / JMeter / Locust 执行与自举

⚠️ **本脚本只负责「把压测跑起来」。报告能力与本脚本无关。**

   没有 k6 / JMeter / Locust **也照样能出报告** —— 只要手上有
   `.jtl` / k6 summary JSON / 监控 CSV，走 `perf_report.py`（纯标准库，见
   `references/report-skeletons.md`）即可出 `.md` + 自包含 `.html`。
   装不上压测器只影响「能否现场灌压力」，不影响「能否把数据变成结论」。

为什么需要自举：本机（2026-09-13 实测）一个压测器都没有（`k6` / `jmeter` / `locust`
全部 `command not found`，只有 JDK 17 在位）。工具不该让人对着 `command not found`
自己猜 —— 找不到先**自动装**，装不上给**可直接复制**的三选一。

执行口径（踩过的坑，务必遵守）：

  * 一律**列表参数**、`shell=True` 绝不使用 —— 路径含中文 / 空格也不会被 shell 拆碎
  * JMeter 走 **`java -jar ApacheJMeter.jar`**，不走 `jmeter.bat`
    （`.bat` 在含中文 / 空格的路径下容易炸，且会拉起 GUI 相关逻辑）
  * k6 跑完自动调 `perf_report.py --from-k6` 出报告；`--no-report` 可跳过

用法：

  # 0. 环境自检（只检查 + 打印可复制的安装指引，不跑压测）
  python perf_run.py --check-env

  # 1. k6 固定并发压接口
  python perf_run.py --engine k6 --script api.js \
      --base-url http://10.18.15.179:8023 --vus 50 --duration 2m --out-dir out/

  # 2. k6 阶梯压测（30 秒涨到 300 并发，再用 5 分钟涨到 3000）
  python perf_run.py --engine k6 --script api.js --stages "30s:300,5m:3000" --out-dir out/

  # 3. JMeter 无 GUI 跑 .jmx（结果落 result.jtl，并生成 HTML 报告目录）
  python perf_run.py --engine jmeter --script plan.jmx \
      --base-url http://10.18.15.179:8023 --out-dir out/

  # 4. Locust（Python 栈，headless）
  python perf_run.py --engine locust --script locustfile.py \
      --base-url http://10.18.15.179:8023 --vus 100 --duration 5m --out-dir out/

  # 5. 只看要执行什么，不真跑
  python perf_run.py --engine k6 --script api.js --dry-run

产物（都在 `--out-dir` 下）：

  k6      k6_summary.json · k6_报告.md · k6_报告.html
  jmeter  result.jtl · jmeter.log · jmeter-report/（JMeter 自带 HTML）· jmeter_报告.md/.html
  locust  locust_stats.csv · locust-report.html（Locust 自带）
          —— Locust 的 CSV 目前没有直连适配器，报告口径见下方「已知边界」
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PERF_REPORT = os.path.join(HERE, "perf_report.py")

ENGINES = ("k6", "jmeter", "locust")

# 各引擎的脚本后缀（只做提示性校验，不强制 —— k6 也支持 .ts，JMeter 也能吃 .csv 计划）
SCRIPT_EXT = {"k6": (".js", ".ts"), "jmeter": (".jmx",), "locust": (".py",)}


def _setup_io():
    """Windows 控制台 cp936 下打印非 ASCII 会 UnicodeEncodeError —— 先掰成 utf-8。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _exe(name):
    """补平台可执行后缀（Windows 是 .exe）。"""
    return name + ".exe" if os.name == "nt" else name


def _on_path(name):
    """在 PATH 里找可执行文件；找不到返回 None。"""
    return shutil.which(name)


# ---------------------------------------------------------------- 工具落地目录

def tools_root():
    """压测工具的落地/查找目录。

    优先级：`PERF_TOOLS_ROOT` 环境变量 > `%USERPROFILE%\\.perf-tools`（POSIX 下 `~/.perf-tools`）。
    把工具放这里的好处是**不改 PATH、不污染系统**，且换机器时整个目录拷走即可。
    """
    r = (os.environ.get("PERF_TOOLS_ROOT") or "").strip()
    if not r:
        r = os.path.join(os.path.expanduser("~"), ".perf-tools")
    return os.path.abspath(r)


def _winget_links(name):
    """winget 安装后落地的 shim 目录（本进程 PATH 是启动时快照，刷不到新装的包）。"""
    la = os.environ.get("LOCALAPPDATA")
    if not la:
        return None
    return os.path.join(la, "Microsoft", "WinGet", "Links", _exe(name))


# ---------------------------------------------------------------- 查找

def _find_k6():
    """找 k6 可执行文件：落地目录 → PATH → winget 的 Links 目录。"""
    root = tools_root()
    for p in (os.path.join(root, "k6", _exe("k6")),
              os.path.join(root, "k6", "k6"),
              os.path.join(root, _exe("k6"))):
        if os.path.isfile(p):
            return p
    p = _on_path("k6")
    if p:
        return p
    w = _winget_links("k6")
    return w if w and os.path.isfile(w) else None


def _find_jmeter():
    """找 JMeter 的 `ApacheJMeter.jar`（**返回 jar 不返回 .bat**）。

    我们要的是「用 java -jar 跑 jar」，所以这里只认 jar 的路径：
    落地目录下的常见解压形态 → PATH 上的 jmeter（由它反推 JMETER_HOME）。
    """
    root = tools_root()
    for p in (os.path.join(root, "jmeter", "bin", "ApacheJMeter.jar"),
              os.path.join(root, "apache-jmeter", "bin", "ApacheJMeter.jar"),
              os.path.join(root, "apache-jmeter-5.6.3", "bin", "ApacheJMeter.jar")):
        if os.path.isfile(p):
            return p
    jm = _on_path("jmeter")
    if jm:
        home = os.path.dirname(os.path.dirname(os.path.abspath(jm)))
        jar = os.path.join(home, "bin", "ApacheJMeter.jar")
        if os.path.isfile(jar):
            return jar
    return None


def _find_java():
    """JMeter 是 Java 程序，得先有 java。"""
    return _on_path("java")


def _find_locust():
    """Locust 是个 Python 包 —— 看当前解释器里能不能 import 到。

    返回运行它的命令前缀（list），找不到返回 None。
    """
    if importlib.util.find_spec("locust") is None:
        return None
    return [sys.executable, "-m", "locust"]


# ---------------------------------------------------------------- 自举

def _no_auto():
    """设了 SKILL_NO_AUTO_INSTALL=1 就只提示不安装（给人选择权）。"""
    return os.environ.get("SKILL_NO_AUTO_INSTALL") == "1"


def _winget_install(pkg_id):
    """用 winget 装（Windows）。列表参数、不经过 shell。"""
    print("[自举] winget 安装 %s ..." % pkg_id, file=sys.stderr)
    try:
        subprocess.check_call(["winget", "install", "--id", pkg_id,
                               "--accept-package-agreements",
                               "--accept-source-agreements"])
        return True
    except Exception as e:
        print("[自举] winget 安装 %s 失败：%s" % (pkg_id, e), file=sys.stderr)
        return False


def _pip_install(pkg):
    """用当前解释器 pip 装。"""
    print("[自举] pip 安装 %s ..." % pkg, file=sys.stderr)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        return True
    except Exception as e:
        print("[自举] pip 安装 %s 失败：%s" % (pkg, e), file=sys.stderr)
        return False


def _guide_k6():
    """k6 装不上时的三选一（**可直接复制**，不是异常栈）。"""
    dest = os.path.join(tools_root(), "k6", _exe("k6"))
    print(
        "[自举] k6 未安装，且无法自动安装。\n"
        "手动三选一：\n"
        "  1) winget install --id GrafanaLabs.k6 --accept-package-agreements "
        "--accept-source-agreements\n"
        "  2) 下载 https://github.com/grafana/k6/releases 的 windows-amd64.zip，"
        "解压 k6.exe 到 %%USERPROFILE%%\\.perf-tools\\k6\\k6.exe"
        "（本机即 %s）\n"
        "  3) 设 PERF_TOOLS_ROOT 指向已有安装目录后重试" % dest)


def _guide_jmeter():
    """JMeter 装不上时的三选一（Apache 归档站的包名带版本号，只能给指引）。"""
    dest = os.path.join(tools_root(), "jmeter")
    print(
        "[自举] JMeter（ApacheJMeter.jar）未找到，且无法自动安装。\n"
        "手动三选一：\n"
        "  1) winget install --id Apache.JMeter --accept-package-agreements "
        "--accept-source-agreements\n"
        "  2) 到 https://archive.apache.org/dist/jmeter/binaries/ 下 "
        "apache-jmeter-5.6.3.zip，解压到 %s\n"
        "     （解压后应有 %s\\bin\\ApacheJMeter.jar）\n"
        "  3) 设 PERF_TOOLS_ROOT 指向已有安装目录后重试（JMeter 是 Java 程序，"
        "另需 java 在 PATH 上；本机 JDK 17 已在位）"
        % (dest, dest))


def _guide_locust():
    """Locust 装不上时的三选一。"""
    print(
        "[自举] Locust 未安装，且无法自动安装。\n"
        "手动三选一：\n"
        "  1) %s -m pip install locust\n"
        "  2) %s -m pip install --user locust        # 无写权限时\n"
        "  3) %s -m pip install --break-system-packages locust   # PEP 668 受管环境"
        % (sys.executable, sys.executable, sys.executable))


def ensure_k6(auto=True):
    """拿到 k6 可执行文件路径；找不到就自举。**返回 None 表示不可用（不抛异常）。**

    `auto=False` 时只查找、只提示，**绝不安装** —— `--dry-run` 走这条路，
    「只看要跑什么」不该顺手往系统里装东西。
    """
    p = _find_k6()
    if p:
        return p
    if not auto or _no_auto():
        _guide_k6()
        return None
    if os.name == "nt" and _on_path("winget"):
        _winget_install("GrafanaLabs.k6")
    else:
        print("[自举] 非 Windows 平台，请用系统包管理器安装 k6（如 "
              "`sudo apt install k6` 或 snap）。", file=sys.stderr)
    p = _find_k6()
    if not p:
        _guide_k6()
    return p


def ensure_jmeter(auto=True):
    """拿到 `ApacheJMeter.jar` 路径；找不到就自举。返回 None 表示不可用。"""
    jar = _find_jmeter()
    if jar:
        return jar
    if auto and not _no_auto() and os.name == "nt" and _on_path("winget"):
        # JMeter 的发行包名带版本号，自动装不一定可靠 —— 装完再查一次，查不到就给归档站指引
        if _winget_install("Apache.JMeter"):
            jar = _find_jmeter()
            if jar:
                return jar
    _guide_jmeter()
    return None


def ensure_locust(auto=True):
    """拿到运行 Locust 的命令前缀（list）；找不到就自举。返回 None 表示不可用。"""
    pre = _find_locust()
    if pre:
        return pre
    if auto and not _no_auto() and _pip_install("locust"):
        pre = _find_locust()
        if pre:
            return pre
    _guide_locust()
    return None


def placeholder(engine):
    """`--dry-run` 且工具尚未安装时，按约定路径给出占位路径，好把命令完整展示出来。"""
    root = tools_root()
    if engine == "k6":
        return os.path.join(root, "k6", _exe("k6"))
    if engine == "jmeter":
        return os.path.join(root, "jmeter", "bin", "ApacheJMeter.jar")
    return [sys.executable, "-m", "locust"]


# ---------------------------------------------------------------- 参数与命令构造

def parse_stages(spec):
    """`"30s:300,5m:3000"` → `["30s:300", "5m:3000"]`。

    格式不对**直接退出**而不是猜 —— 猜错会压出一个不是你要的负载，
    而报告上看不出来（只会看到一堆看不懂的数字）。
    """
    if not spec:
        return []
    out = []
    for part in str(spec).split(","):
        p = part.strip()
        if not p:
            continue
        dur, sep, vus = p.partition(":")
        dur, vus = dur.strip(), vus.strip()
        if not sep or not dur or not vus.isdigit():
            sys.exit("--stages 格式应为「时长:并发」，逗号分隔，如 30s:300,5m:3000；"
                     "收到：%r" % p)
        out.append("%s:%s" % (dur, vus))
    return out


def build_k6(k6, script, args, out_dir):
    """k6 命令 + summary 导出路径。"""
    summary = os.path.join(out_dir, "k6_summary.json")
    cmd = [k6, "run", script, "--summary-export", summary]
    if args.vus:
        cmd += ["--vus", str(args.vus)]
    if args.duration:
        cmd += ["--duration", str(args.duration)]
    for st in parse_stages(args.stages):
        cmd += ["--stage", st]
    if args.base_url:
        # 脚本里用 __ENV.BASE_URL 取，避免把地址硬编码进 .js
        cmd += ["-e", "BASE_URL=%s" % args.base_url]
    return cmd, summary


def build_jmeter(jar, script, args, out_dir, java=None):
    """JMeter 无 GUI 命令。**走 java -jar，不走 jmeter.bat。**"""
    java = java or _find_java()
    if not java:
        sys.exit("JMeter 是 Java 程序，当前 PATH 上没有 java。\n"
                 "请先装 JRE/JDK（本机实测已有 Temurin JDK 17），或把 java 加进 PATH。")
    jtl = os.path.join(out_dir, "result.jtl")
    rep = os.path.join(out_dir, "jmeter-report")
    log = os.path.join(out_dir, "jmeter.log")
    cmd = [java, "-jar", jar, "-n",              # -n = 无 GUI（headless）
           "-t", script, "-l", jtl, "-j", log,
           "-e", "-o", rep]                       # -e 出 HTML，-o 指定报告目录
    if args.base_url:
        # 计划里用 ${__P(BASE_URL)} / ${__P(baseUrl)} 取
        cmd += ["-JBASE_URL=%s" % args.base_url]
    if args.duration:
        cmd += ["-JDURATION=%s" % args.duration]
    if args.vus:
        cmd += ["-JVUS=%s" % args.vus]
    return cmd, jtl, rep


def build_locust(prefix, script, args, out_dir):
    """Locust headless 命令。"""
    if not args.vus:
        sys.exit("Locust headless 模式需要 --vus <并发数>（还要有 --duration 才会自己停）。")
    rate = args.spawn_rate or max(1, int(args.vus) // 10)
    csv_base = os.path.join(out_dir, "locust")
    html = os.path.join(out_dir, "locust-report.html")
    cmd = list(prefix) + ["-f", script, "--headless",
                          "--csv", csv_base, "--html", html,
                          "-u", str(args.vus), "-r", str(rate)]
    if args.duration:
        cmd += ["-t", str(args.duration)]
    if args.base_url:
        cmd += ["--host", args.base_url]
    return cmd, html


def _render(cmd):
    """把 argv 渲染成可直接复制的命令行（Windows 用 list2cmdline，其它用 shlex.join）。"""
    if os.name == "nt":
        return subprocess.list2cmdline([str(c) for c in cmd])
    import shlex
    return shlex.join([str(c) for c in cmd])


def _ensure_empty_dir(path):
    """JMeter 的 `-o` 要求目录不存在或为空，否则报错退出。"""
    if os.path.isdir(path) and os.listdir(path):
        sys.exit("JMeter 报告目录非空，`-e -o` 会拒绝执行：%s\n"
                 "请先清空该目录（或换一个 --out-dir）后重试。" % path)
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------- 执行

def execute(cmd, timeout=None):
    """执行压测命令。**列表参数、绝不 shell=True** —— 含中文/空格的路径也不会被拆碎。"""
    print("[执行] %s" % _render(cmd))
    print("-" * 68)
    t0 = time.time()
    try:
        rc = subprocess.call([str(c) for c in cmd])
    except FileNotFoundError as e:
        print("[失败] 命令不可执行：%s" % e, file=sys.stderr)
        return 127
    except KeyboardInterrupt:
        print("\n用户中断。", file=sys.stderr)
        return 130
    print("-" * 68)
    print("[完成] 退出码 %d，耗时 %.1f 秒" % (rc, time.time() - t0))
    return rc


def gen_report(engine, src, out_dir):
    """调 perf_report.py 出 `.md` + 自包含 `.html`。**纯标准库，不依赖压测器。**"""
    if not os.path.exists(PERF_REPORT):
        print("[跳过] 找不到 perf_report.py：%s" % PERF_REPORT, file=sys.stderr)
        return 1
    md = os.path.join(out_dir, "%s_报告.md" % engine)
    ht = os.path.join(out_dir, "%s_报告.html" % engine)
    cmd = [sys.executable, PERF_REPORT, "--kind", "perf"]
    cmd += ["--from-k6", src] if engine == "k6" else ["--from-jmeter", src]
    cmd += ["--md", md, "--html", ht]
    print("[报告] 由 perf_report.py 生成（纯标准库，与压测器无关）")
    return execute(cmd)


def check_env():
    """只做环境自检并打印可复制的安装指引，不跑任何压测。"""
    root = tools_root()
    print("== 性能测试 · 压测工具环境自检 ==")
    print("PERF_TOOLS_ROOT ：%s%s" % (root, "" if os.path.isdir(root) else "（目录不存在，尚未落地过工具）"))
    print("Python          ：%s" % sys.executable)
    print("平台            ：%s" % sys.platform)
    print("-" * 68)

    k6 = _find_k6()
    jm = _find_jmeter()
    java = _find_java()
    loc = _find_locust()

    rows = [
        ("k6", k6 or "未安装", bool(k6)),
        ("JMeter（ApacheJMeter.jar）", jm or "未安装", bool(jm)),
        ("java（JMeter 前置）", java or "未找到", bool(java)),
        ("Locust", (" ".join(loc) if loc else "未安装"), bool(loc)),
    ]
    for name, val, ok in rows:
        print("  %-28s %-8s %s" % (name, "✅ 有" if ok else "❌ 缺", val))

    missing = [name for name, _v, ok in rows if not ok]
    print("-" * 68)
    if not missing:
        print("全部就位，可直接压测。")
    else:
        print("缺 %d 项，逐个给可复制的安装指引：" % len(missing))
        if not k6:
            _guide_k6()
        if not jm or not java:
            _guide_jmeter()
        if not loc:
            _guide_locust()
        if os.environ.get("SKILL_NO_AUTO_INSTALL") == "1":
            print("[提示] 当前设了 SKILL_NO_AUTO_INSTALL=1 —— 执行时会**只提示不自动安装**。")
    print("-" * 68)
    print("⚠️ 本脚本只负责执行压测。**报告能力不依赖上面任何一项**：")
    print("   有 .jtl / k6 summary JSON / 监控 CSV 就能出报告（perf_report.py，纯标准库）。")
    return 0


def main():
    _setup_io()
    ap = argparse.ArgumentParser(
        description="性能测试 · k6 / JMeter / Locust 执行与自举（报告不依赖它们）")
    ap.add_argument("--check-env", action="store_true",
                    help="只做环境自检并打印可复制的安装指引")
    ap.add_argument("--engine", choices=list(ENGINES), default="k6", help="压测引擎（默认 k6）")
    ap.add_argument("--script", default=None, help="要执行的脚本（.js / .ts / .jmx / .py）")
    ap.add_argument("--base-url", default=None, help="被测服务地址（压哪）")
    ap.add_argument("--vus", type=int, default=0, help="并发用户数")
    ap.add_argument("--duration", default=None, help="持续时长，如 30s / 2m / 5m")
    ap.add_argument("--stages", default=None,
                    help="阶梯压测，如 30s:300,5m:3000（k6；与 --duration 互斥）")
    ap.add_argument("--spawn-rate", type=int, default=0,
                    help="Locust 每秒涨的并发数（默认取 vus/10，至少 1）")
    ap.add_argument("--out-dir", default="perf-out", help="产物目录（默认 perf-out）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的命令，不真跑")
    ap.add_argument("--no-report", action="store_true",
                    help="跳过自动出报告（默认跑完会调 perf_report.py --from-k6/--from-jmeter 出报告）")
    args = ap.parse_args()

    if args.check_env:
        return check_env()

    if not args.script:
        ap.error("需要 --script <压测脚本>；只做环境自检请用 --check-env")
    if not os.path.isfile(args.script):
        sys.exit("脚本不存在：%s" % args.script)

    ext = os.path.splitext(args.script)[1].lower()
    if ext not in SCRIPT_EXT[args.engine]:
        print("[警告] --engine %s 的脚本通常是 %s，收到的是 %s —— 若确属有意请忽略。"
              % (args.engine, "/".join(SCRIPT_EXT[args.engine]), ext), file=sys.stderr)

    if args.stages and args.duration:
        sys.exit("--stages 与 --duration 互斥（k6 不允许同时指定），请只给一个。")

    if not args.dry_run:
        # dry-run 不落任何东西 —— 连目录都不建（免得留下空目录让人以为跑过了）
        os.makedirs(args.out_dir, exist_ok=True)
    out_dir = os.path.abspath(args.out_dir)
    print("引擎：%s　脚本：%s　产物目录：%s" % (args.engine, args.script, out_dir))

    # ---- 找工具。`--dry-run` **只查找不安装**（连安装指引都不打），
    #      找不到就按约定路径占位，好把「将要执行什么」完整展示出来。
    if args.engine == "k6":
        k6 = _find_k6() if args.dry_run else ensure_k6()
        if not k6 and args.dry_run:
            k6 = placeholder("k6")
            print("[dry-run] k6 尚未安装 —— 下面按约定路径 %s 展示将执行的命令" % k6)
        if not k6:
            return 1
        cmd, summary = build_k6(k6, args.script, args, out_dir)
        src = summary
    elif args.engine == "jmeter":
        jar = _find_jmeter() if args.dry_run else ensure_jmeter()
        if not jar and args.dry_run:
            jar = placeholder("jmeter")
            print("[dry-run] JMeter 尚未安装 —— 下面按约定路径 %s 展示将执行的命令" % jar)
        if not jar:
            return 1
        cmd, jtl, rep = build_jmeter(jar, args.script, args, out_dir,
                                     java=(_find_java() or "java"))
        if not args.dry_run:
            _ensure_empty_dir(rep)
        src = jtl
    else:
        prefix = _find_locust() if args.dry_run else ensure_locust()
        if not prefix and args.dry_run:
            prefix = placeholder("locust")
            print("[dry-run] Locust 尚未安装 —— 下面按约定命令展示将执行什么")
        if not prefix:
            return 1
        cmd, _html = build_locust(prefix, args.script, args, out_dir)
        src = None

    if args.dry_run:
        print("[dry-run] 将执行：\n  %s" % _render(cmd))
        return 0

    rc = execute(cmd)

    # ---- 出报告（k6 / JMeter 有直连适配器；Locust 见下方说明）
    if args.engine == "locust":
        print("[提示] Locust 的 `*_stats.csv` 目前没有直连适配器 —— "
              "报告可先用 Locust 自带 --html（已生成），或用 perf_report.py 走 .jtl / stats.json 口径。")
    elif not args.no_report:
        if rc != 0:
            print("[提示] 压测退出码非 0，仍尝试出报告（有结果才有得判）。", file=sys.stderr)
        if not os.path.exists(src):
            print("[跳过] 结果文件未生成，无法出报告：%s" % src, file=sys.stderr)
        else:
            gen_report(args.engine, src, out_dir)
    return rc


if __name__ == "__main__":
    sys.exit(main())
