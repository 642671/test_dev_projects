#!/bin/bash
# ============================================================
# 火山引擎 Coding Plan 代理 - 停止脚本
# ============================================================
# 用法:
#   sudo bash stop.sh            # 停止代理（保留 hosts 和证书）
#   sudo bash stop.sh --clean    # 停止并清理所有配置（hosts + 证书）
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/proxy.pid"
HOSTS_FILE="/etc/hosts"
TARGET_DOMAIN="api.minimax.chat"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${YELLOW}[*] 正在停止火山引擎代理...${NC}"

# 停止代理进程
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        sleep 1
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID"
        fi
        echo -e "  ${GREEN}[✓] 代理进程已停止 (PID: $PID)${NC}"
    else
        echo -e "  ${YELLOW}[!] 进程 $PID 已不存在${NC}"
    fi
    rm -f "$PID_FILE"
else
    echo -e "  ${YELLOW}[!] PID 文件不存在，尝试查找进程...${NC}"
    PIDS=$(pgrep -f "proxy.py" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        kill $PIDS 2>/dev/null || true
        echo -e "  ${GREEN}[✓] 已终止进程: $PIDS${NC}"
    else
        echo -e "  ${YELLOW}[!] 没有发现运行中的代理${NC}"
    fi
fi

# 清理模式
if [ "$1" = "--clean" ]; then
    echo ""
    echo -e "${YELLOW}[*] 清理模式: 移除 hosts 劫持和证书...${NC}"

    # 移除 hosts 劫持
    if grep -q "$TARGET_DOMAIN" "$HOSTS_FILE"; then
        sed -i '' "/# === 火山引擎 Coding Plan 代理 (VolcanoProxy) ===/,/# === End VolcanoProxy ===/d" "$HOSTS_FILE"
        # 也移除单独的行（兼容旧版本）
        sed -i '' "/127.0.0.1.*$TARGET_DOMAIN/d" "$HOSTS_FILE"
        echo -e "  ${GREEN}[✓] hosts 劫持已移除${NC}"
    else
        echo -e "  ${GREEN}[✓] hosts 无需修改${NC}"
    fi

    # 移除系统证书
    if [ -f "$SCRIPT_DIR/certs/minimax_cert.pem" ]; then
        echo -e "  ${YELLOW}[*] 正在移除系统信任证书...${NC}"
        python3 "$SCRIPT_DIR/gen_cert.py" uninstall 2>/dev/null || true
    fi

    echo ""
    echo -e "${GREEN}"
    echo "  ═══════════════════════════════════════════"
    echo "  [✓] 所有配置已清理完毕!"
    echo "  ═══════════════════════════════════════════"
    echo -e "${NC}"
    echo -e "  如需完全删除项目: ${CYAN}rm -rf $SCRIPT_DIR${NC}"
else
    echo ""
    echo -e "${GREEN}[✓] 代理已停止${NC}"
    echo -e "  ${YELLOW}hosts 劫持和证书已保留${NC}"
    echo -e "  如需完全清理: ${CYAN}sudo bash $0 --clean${NC}"
fi
