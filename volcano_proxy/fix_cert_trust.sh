#!/bin/bash
# ============================================================
# 修复 SSL 证书信任设置
# 解决 Qoder 不信任自签名证书的问题
# 用法: sudo bash fix_cert_trust.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_FILE="$SCRIPT_DIR/certs/minimax_cert.pem"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║  🔧 修复 SSL 证书信任设置               ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[✗] 需要 sudo 权限${NC}"
    echo -e "    请使用: ${YELLOW}sudo bash $0${NC}"
    exit 1
fi

# Step 1: 重新安装证书，显式指定 SSL 和基本信任
echo -e "${YELLOW}[1/3] 重新安装证书到系统钥匙串 (指定 SSL 信任)...${NC}"

# 先删除旧证书（如果存在）
security delete-certificate -c "api.minimax.chat" /Library/Keychains/System.keychain 2>/dev/null || true

# 重新添加，显式指定 SSL 和基本策略
security add-trusted-cert -d -r trustRoot -p ssl -p basic \
    -k /Library/Keychains/System.keychain "$CERT_FILE"
echo -e "  ${GREEN}[✓] 证书已重新安装${NC}"

# Step 2: 验证信任设置
echo -e "${YELLOW}[2/3] 验证证书信任设置...${NC}"
echo "  系统信任设置:"
security dump-trust-settings -d 2>&1 | grep -A2 "minimax" || echo "  (未找到)"
echo ""

# Step 3: 测试 HTTPS 连接
echo -e "${YELLOW}[3/3] 测试 HTTPS 连接...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.minimax.chat/ 2>&1 || echo "000")
echo -e "  HTTPS 响应码: ${CYAN}$HTTP_CODE${NC}"

echo ""
echo -e "${GREEN}"
echo "  ═══════════════════════════════════════════"
echo "  [✓] 证书信任设置已修复!"
echo "  ═══════════════════════════════════════════"
echo -e "${NC}"
echo -e "  ${YELLOW}重要: 请重启 Qoder 后重试添加模型${NC}"
echo -e "  (关闭 Qoder 窗口，重新打开)"
echo ""
