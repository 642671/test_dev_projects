#!/usr/bin/env python3
"""
为 api.minimax.chat 生成自签名 SSL 证书
用于本地 MITM 代理拦截 Qoder 发往 MiniMax 的 HTTPS 请求
"""

import os
import sys
import subprocess

CERTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
DOMAIN = "api.minimax.chat"
CERT_FILE = os.path.join(CERTS_DIR, "minimax_cert.pem")
KEY_FILE = os.path.join(CERTS_DIR, "minimax_key.pem")


def generate_cert():
    os.makedirs(CERTS_DIR, exist_ok=True)

    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        print(f"[!] 证书已存在: {CERT_FILE}")
        resp = input("    是否重新生成? (y/N): ").strip().lower()
        if resp != "y":
            print("[*] 跳过证书生成")
            return

    print(f"[*] 正在为 {DOMAIN} 生成自签名 SSL 证书...")

    # 使用 openssl 生成自签名证书
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", KEY_FILE,
        "-out", CERT_FILE,
        "-days", "365",
        "-nodes",
        "-subj", f"/CN={DOMAIN}/O=VolcanoProxy/C=CN",
        "-addext", f"subjectAltName=DNS:{DOMAIN},DNS:*.minimax.chat,IP:127.0.0.1"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[✗] 证书生成失败:")
        print(result.stderr)
        sys.exit(1)

    print(f"[✓] 证书已生成:")
    print(f"    证书: {CERT_FILE}")
    print(f"    私钥: {KEY_FILE}")
    print()
    print("=" * 60)
    print("[!] 下一步: 将证书安装到系统信任链")
    print()
    print("  macOS 命令 (需要密码):")
    print(f'  sudo security add-trusted-cert -d -r trustRoot '
          f'-k /Library/Keychains/System.keychain "{CERT_FILE}"')
    print()
    print("  或者手动操作:")
    print(f'  1. 双击打开 {CERT_FILE}')
    print(f'  2. 添加到 "系统" 钥匙串')
    print(f'  3. 找到证书 → 信任 → 始终信任')
    print("=" * 60)


def install_cert():
    """安装证书到 macOS 系统信任链"""
    if not os.path.exists(CERT_FILE):
        print("[✗] 证书文件不存在，请先运行 gen_cert.py")
        sys.exit(1)

    print(f"[*] 正在安装证书到系统信任链...")
    print(f"    (需要输入管理员密码)")
    print()

    cmd = [
        "sudo", "security", "add-trusted-cert",
        "-d", "-r", "trustRoot",
        "-k", "/Library/Keychains/System.keychain",
        CERT_FILE
    ]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        print()
        print("[✓] 证书已安装到系统信任链")
    else:
        print()
        print("[✗] 安装失败，请手动安装:")
        print(f'    sudo security add-trusted-cert -d -r trustRoot '
              f'-k /Library/Keychains/System.keychain "{CERT_FILE}"')


def uninstall_cert():
    """从系统信任链移除证书"""
    print("[*] 正在从系统信任链移除证书...")
    print(f"    (需要输入管理员密码)")

    # 获取证书指纹
    result = subprocess.run(
        ["openssl", "x509", "-in", CERT_FILE, "-fingerprint", "-noout"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("[✗] 无法读取证书指纹")
        return

    fingerprint = result.stdout.strip().split("=")[-1].replace(":", "")

    cmd = [
        "sudo", "security", "delete-certificate",
        "-Z", fingerprint,
        "/Library/Keychains/System.keychain"
    ]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("[✓] 证书已从系统信任链移除")
    else:
        print("[!] 移除失败或证书不存在于系统信任链中")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "install":
            install_cert()
        elif action == "uninstall":
            uninstall_cert()
        elif action == "gen":
            generate_cert()
        else:
            print(f"用法: python3 {sys.argv[0]} [gen|install|uninstall]")
    else:
        generate_cert()
