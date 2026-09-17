#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sshcommon.py — UID 迁移测试 skill 共用 SSH 连接与远程操作（账号密码 + paramiko）。

仅封装“连接 / 执行命令”，不内嵌任何密码。
凭据优先级：进程环境变量 > 本文件所在 skill 根目录的 .env.local > 当前目录的 .env.local

    TOS_HOST   目标 IP/主机名
    TOS_USER   登录用户名
    TOS_PASS   登录密码
    TOS_PORT   SSH 端口（默认 9222）
    TOS_LEGACY=1  兼容老 dropbear/老 sshd（只认 ssh-rsa）
    SSH_TIMEOUT   单条命令超时秒（默认 120）

Windows 下禁止 sshpass（对 TOS sshd 的 password+keyboard-interactive 无法正确送密码，
凭据正确也报 Permission denied）。一律走 paramiko（等价 PuTTY）。

本文件与其它 skill 内的同名文件保持一致，改动请同步（见 .claude/rules/skill-portability.md）。
"""
import logging
import os
import re
import sys
import time


# ---------------------------------------------------------------- 环境自检与自举
#
# 本 skill 的目标是「目录复制到任何一台机器上就能用」：缺依赖先自动补齐，而不是
# 让人对着 ImportError 猜。Python 解释器本身装不了，只能给出手动安装指引。
MIN_PY = (3, 8)
DEP_PIP = "paramiko"      # pip 包名
DEP_IMP = "paramiko"      # import 名


def ensure_paramiko():
    """拿到 paramiko 模块；没装就自动 pip install（设 SKILL_NO_AUTO_INSTALL=1 可关闭）。"""
    try:
        import paramiko
        return paramiko
    except ImportError:
        pass

    py = os.path.basename(sys.executable or "python")
    if os.environ.get("SKILL_NO_AUTO_INSTALL") == "1":
        sys.exit("缺少依赖 %(imp)s，且已设 SKILL_NO_AUTO_INSTALL=1（不自动安装）。\n"
                 "请手动执行：%(py)s -m pip install %(pip)s"
                 % {"imp": DEP_IMP, "pip": DEP_PIP, "py": py})

    print("[自举] 缺少依赖 %s，正在自动安装 ..." % DEP_IMP, file=sys.stderr)
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", DEP_PIP])
    except Exception as e:
        sys.exit("自动安装 %(imp)s 失败：%(e)s\n"
                 "手动三选一：\n"
                 "  1) %(py)s -m pip install --user %(pip)s\n"
                 "  2) %(py)s -m pip install --break-system-packages %(pip)s   # PEP 668 受管环境\n"
                 "  3) apt install python3-%(imp)s                             # 系统包管理器"
                 % {"imp": DEP_IMP, "pip": DEP_PIP, "py": py, "e": e})

    import paramiko
    print("[自举] %s %s 安装完成。" % (DEP_IMP, getattr(paramiko, "__version__", "?")),
          file=sys.stderr)
    return paramiko


def preflight():
    """环境自检：Python 版本够不够 + 依赖拿不拿得到。返回可用的 paramiko。"""
    if sys.version_info < MIN_PY:
        sys.exit("需要 Python %d.%d 及以上，当前 %d.%d —— 请先安装/升级 Python 后重试。"
                 % (MIN_PY + sys.version_info[:2]))
    return ensure_paramiko()


def env_summary():
    """一行环境摘要，供自检入口打印。"""
    pk = ensure_paramiko()
    return "Python %d.%d.%d (%s) · %s %s" % (
        sys.version_info[0], sys.version_info[1], sys.version_info[2],
        sys.executable, DEP_IMP, getattr(pk, "__version__", "?"))


def load_env():
    """读取 skill 根 / 当前目录的 .env.local（若存在），不覆盖已有环境变量。

    ⚠️ 行内注释要剥掉：`TOS_PORT=9222   # SSH 端口` 若不处理，值会变成
    `9222   # SSH 端口`，`creds()` 里的 `int()` 直接 ValueError。
    只把**前面有空白**的 `#` 当注释起始 —— 口令里含 `#` 时不至于被误伤。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(here)          # 本脚本 上一级 即 skill 根
    for path in (os.path.join(skill_root, ".env.local"),
                 os.path.join(os.getcwd(), ".env.local")):
        if os.path.exists(path):
            for raw in open(path, encoding="utf-8"):
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                # 剥掉行内注释：` #...` 或 `\t#...`
                v = re.split(r"\s+#", v, maxsplit=1)[0]
                os.environ.setdefault(k.strip(), v.strip())


def creds():
    load_env()
    return {
        "host": os.environ.get("TOS_HOST", "").strip(),
        "user": os.environ.get("TOS_USER", "").strip(),
        "pass": os.environ.get("TOS_PASS", ""),
        "port": int(os.environ.get("TOS_PORT", "9222")),
    }


# ---------------------------------------------------------------- 连接重试
#
# 机器刚重启 / sshd 瞬时无响应时，第一次连接常直接失败，典型报错：
#     paramiko.ssh_exception.SSHException: Error reading SSH protocol banner
# 特征是「端口能 accept，但收不到 banner」——sshd 还没准备好，等几秒再连通常就好。
#
# ⚠️ **认证失败不重试**：反复试密码会触发 PAM 锁账号（约 5 分钟），越试越登不上。
CONNECT_TRIES = int(os.environ.get("SSH_RETRIES", "3"))        # 总尝试次数
CONNECT_WAIT = float(os.environ.get("SSH_RETRY_WAIT", "5"))    # 每次重试前的等待秒数
BANNER_TIMEOUT = float(os.environ.get("SSH_BANNER_TIMEOUT", "20"))   # 单次等待 banner 秒数


def _with_retry(fn):
    """对瞬时连接失败等待重试；认证失败立即抛出；用尽次数给出排查指引。"""
    if os.environ.get("SSH_DEBUG") != "1":
        # paramiko 的 transport 线程会把连接异常连同完整调用栈打进 stderr
        # （logging 的 lastResort handler），而下面已经给出自己的诊断 ——
        # 默认静音，需要看原始栈时设 SSH_DEBUG=1。
        logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    paramiko = ensure_paramiko()
    last = None
    for i in range(1, CONNECT_TRIES + 1):
        try:
            return fn()
        except paramiko.AuthenticationException:
            raise                       # 密码/账号问题：重试只会触发 PAM 锁定
        except (paramiko.SSHException, EOFError, OSError) as e:
            last = e
            if i >= CONNECT_TRIES:
                break
            print("[重试] 第 %d/%d 次连接失败：%s" % (i, CONNECT_TRIES, e), file=sys.stderr)
            print("       %.0f 秒后再试（SSH_RETRIES / SSH_RETRY_WAIT 可调）..."
                  % CONNECT_WAIT, file=sys.stderr)
            time.sleep(CONNECT_WAIT)
    sys.exit("连续 %d 次连接失败，最后一次：%s\n"
             "排查顺序：① ping 通不通  ② 端口能否 accept  ③ 能否收到 SSH banner。\n"
             "端口通却收不到 banner（Error reading SSH protocol banner）多是 sshd 刚重启/正忙，\n"
             "稍等重试，或调大 SSH_RETRY_WAIT（当前 %.0f 秒）/ SSH_BANNER_TIMEOUT（当前 %.0f 秒）。"
             % (CONNECT_TRIES, last, CONNECT_WAIT, BANNER_TIMEOUT))


def connect():
    """连接测试机；对瞬时连接失败自动等待重试（认证失败不重试）。"""
    return _with_retry(_connect_once)


def _connect_once():
    paramiko = ensure_paramiko()
    c = creds()
    if not c["host"] or not c["user"]:
        sys.exit("缺少凭据：请设置 TOS_HOST / TOS_USER（可加 TOS_PASS / TOS_PORT）。\n"
                 "示例:  TOS_HOST=10.18.15.171 TOS_USER=yxw TOS_PASS=xxxx TOS_PORT=9222 \\\n"
                 "         python scripts/uid_snapshot.py --label before --out before.json\n"
                 "或参考本 skill 目录 .env.local.example 创建 .env.local。")
    if os.environ.get("TOS_LEGACY") == "1":
        # 老 dropbear/老 sshd：paramiko 默认禁用 ssh-rsa，显式放开
        pk = ensure_paramiko()
        tr = pk.Transport((c["host"], c["port"]))
        tr.banner_timeout = 30
        so = tr.get_security_options()
        so.key_types = ["ssh-rsa", "rsa-sha2-256", "rsa-sha2-512",
                        "ssh-ed25519", "ecdsa-sha2-nistp256"]
        tr.start_client()
        tr.auth_password(c["user"], c["pass"]) if c["pass"] else tr.auth_none(c["user"])
        client = pk.SSHClient()
        client._transport = tr
        return client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(c["host"], port=c["port"], username=c["user"], password=c["pass"] or None,
                   timeout=20, banner_timeout=BANNER_TIMEOUT,
                   look_for_keys=False, allow_agent=False,
                   disabled_algorithms={"pubkeys": ["ssh-rsa"]})
    return client


def run(client, cmd, timeout=None):
    """执行单条远程命令，返回 (stdout, stderr, exit_code)。"""
    timeout = timeout or int(os.environ.get("SSH_TIMEOUT", "120"))
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return out, err, stdout.channel.recv_exit_status()


def banner(client):
    """打印机器识别信息，便于对账是哪台测试机。"""
    c = creds()
    out, err, _ = run(client, "whoami; hostname; uname -a 2>/dev/null | head -1")
    print("== 连接 %s:%s (%s) ==" % (c["host"], c["port"], c["user"]))
    print(out.strip())
    if err.strip():
        print("[stderr]", err.strip(), file=sys.stderr)


# ---------------------------------------------------------------- 文件传输
#
# 有些 TOS 机器把 sftp 子系统关了（实测 10.18.15.179：open_sftp 抛
# "EOF during negotiation"），而 10.18.15.103 是开的 —— 同一批机器配置不一致。
# 所以这里 **SFTP 优先、失败自动回退 base64 over exec**，调用方无需关心。

def _sftp_or_none(client):
    try:
        return client.open_sftp()
    except Exception as e:
        print("[传输] sftp 不可用（%s），改用 base64 通道" % str(e)[:60], file=sys.stderr)
        return None


def put_file(client, local_path, remote_path):
    """上传一个文件。sftp 不可用时走 `base64 | base64 -d`（不依赖 sftp 子系统）。"""
    import base64
    import os as _os

    sftp = _sftp_or_none(client)
    if sftp is not None:
        try:
            sftp.put(local_path, remote_path)
            return "sftp"
        except Exception as e:
            print("[传输] sftp.put 失败（%s），回退 base64" % str(e)[:60], file=sys.stderr)
        finally:
            try:
                sftp.close()
            except Exception:
                pass

    with open(local_path, "rb") as f:
        blob = base64.b64encode(f.read())
    stdin, stdout, stderr = client.exec_command(
        "base64 -d > %s" % _shq(remote_path), timeout=300)
    # 分块写，避免一次性灌爆 channel 窗口
    for i in range(0, len(blob), 65536):
        stdin.write(blob[i:i + 65536])
    stdin.flush()
    stdin.channel.shutdown_write()
    rc = stdout.channel.recv_exit_status()
    err = stderr.read().decode("utf-8", "replace")
    if rc != 0:
        raise IOError("base64 上传失败 rc=%d %s" % (rc, err[:200]))
    return "base64"


def get_file(client, remote_path, local_path):
    """下载一个文件。sftp 不可用时走 `base64 < file` 再本地解码。"""
    import base64
    import os as _os

    d = _os.path.dirname(_os.path.abspath(local_path))
    if d:
        _os.makedirs(d, exist_ok=True)

    sftp = _sftp_or_none(client)
    if sftp is not None:
        try:
            sftp.get(remote_path, local_path)
            return "sftp"
        except Exception as e:
            print("[传输] sftp.get 失败（%s），回退 base64" % str(e)[:60], file=sys.stderr)
        finally:
            try:
                sftp.close()
            except Exception:
                pass

    out, err, rc = run(client, "base64 %s" % _shq(remote_path), timeout=300)
    if rc != 0:
        raise IOError("base64 下载失败 rc=%d %s" % (rc, err[:200]))
    with open(local_path, "wb") as f:
        f.write(base64.b64decode("".join(out.split())))
    return "base64"


def remove_remote(client, remote_path):
    """尽力删除远端文件，失败不抛。"""
    try:
        run(client, "rm -f %s" % _shq(remote_path), timeout=20)
    except Exception:
        pass


def _shq(s):
    """POSIX 单引号转义。"""
    return "'" + str(s).replace("'", "'\\''") + "'"
