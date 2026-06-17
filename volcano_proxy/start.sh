#!/bin/bash
# ============================================================
# 火山引擎 Coding Plan 代理 - 一键启动脚本
# ============================================================
# 用法:
#   sudo bash start.sh          # 启动代理
#   sudo bash start.sh --check  # 仅检查配置不启动
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/proxy.pid"
LOG_FILE="$SCRIPT_DIR/proxy.log"
HOSTS_FILE="/etc/hosts"
TARGET_DOMAIN="api.moonshot.cn"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║  🔥 火山引擎 Coding Plan 代理启动器     ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[✗] 需要 sudo 权限来监听 443 端口和修改 hosts${NC}"
    echo -e "    请使用: ${YELLOW}sudo bash $0${NC}"
    exit 1
fi

# Step 1: 检查证书
echo -e "${YELLOW}[1/4] 检查 SSL 证书...${NC}"
if [ ! -f "$SCRIPT_DIR/certs/kimi_cert.pem" ]; then
    echo -e "  证书不存在，正在生成..."
    python3 "$SCRIPT_DIR/gen_cert.py" gen
    echo -e "  ${YELLOW}正在安装证书到系统信任链（需要确认密码）...${NC}"
    python3 "$SCRIPT_DIR/gen_cert.py" install
fi
echo -e "  ${GREEN}[✓] SSL 证书已就绪${NC}"

# Step 2: 检查 hosts 文件
echo -e "${YELLOW}[2/4] 检查 hosts 劫持...${NC}"
if grep -q "127.0.0.1.*$TARGET_DOMAIN" "$HOSTS_FILE"; then
    echo -e "  ${GREEN}[✓] hosts 已配置: 127.0.0.1 → $TARGET_DOMAIN${NC}"
else
    echo -e "  ${YELLOW}正在添加 hosts 劫持...${NC}"
    echo "" >> "$HOSTS_FILE"
    echo "# === 火山引擎 Coding Plan 代理 (VolcanoProxy) ===" >> "$HOSTS_FILE"
    echo "127.0.0.1  $TARGET_DOMAIN" >> "$HOSTS_FILE"
    echo "# === End VolcanoProxy ===" >> "$HOSTS_FILE"
    echo -e "  ${GREEN}[✓] hosts 已添加: 127.0.0.1 → $TARGET_DOMAIN${NC}"
fi

# Step 3: 检查 API Key
echo -e "${YELLOW}[3/4] 检查 API Key 配置...${NC}"
API_KEY=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json'))['volcano_engine']['api_key'])")
if [ "$API_KEY" = "YOUR_VOLCANO_ENGINE_API_KEY_HERE" ]; then
    echo -e "  ${RED}[✗] 请先在 config.json 中填写你的火山引擎 API Key!${NC}"
    echo -e "    编辑: ${CYAN}$SCRIPT_DIR/config.json${NC}"
    echo -e '    修改 "api_key": "YOUR_VOLCANO_ENGINE_API_KEY_HERE"'
    echo -e '    改为 "api_key": "你的实际API Key"'
    exit 1
fi
echo -e "  ${GREEN}[✓] API Key 已配置 (${API_KEY:0:8}...)${NC}"

# Step 4: 检查是否已在运行
echo -e "${YELLOW}[4/4] 检查代理状态...${NC}"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "  ${YELLOW}[!] 代理已在运行 (PID: $OLD_PID)${NC}"
        echo -e "    如需重启，请先运行: ${CYAN}sudo bash stop.sh${NC}"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# 仅检查模式
if [ "$1" = "--check" ]; then
    echo -e "${GREEN}"
    echo "  ═══════════════════════════════════════════"
    echo "  [✓] 所有检查通过！可以启动代理"
    echo "  ═══════════════════════════════════════════"
    echo -e "${NC}"
    exit 0
fi

# 启动代理（后台运行）
echo -e "${GREEN}[✓] 正在启动代理...${NC}"
nohup python3 "$SCRIPT_DIR/proxy.py" >> "$LOG_FILE" 2>&1 &
PROXY_PID=$!
sleep 1

# 验证启动
if kill -0 "$PROXY_PID" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}"
    echo "  ═══════════════════════════════════════════"
    echo "  [✓] 代理已启动!"
    echo "  ═══════════════════════════════════════════"
    echo -e "${NC}"
    echo -e "  PID:       ${CYAN}$PROXY_PID${NC}"
    echo -e "  监听:      ${CYAN}https://0.0.0.0:443${NC}"
    echo -e "  拦截:      ${CYAN}$TARGET_DOMAIN → 火山引擎${NC}"
    echo -e "  健康检查:  ${CYAN}http://127.0.0.1:8443/health${NC}"
    echo -e "  日志:      ${CYAN}$LOG_FILE${NC}"
    echo ""
    echo -e "  ${YELLOW}停止代理: sudo bash $SCRIPT_DIR/stop.sh${NC}"
    echo -e "  ${YELLOW}查看日志: tail -f $LOG_FILE${NC}"
    echo ""
else
    echo -e "${RED}[✗] 代理启动失败！${NC}"
    echo -e "    查看日志: ${CYAN}tail -20 $LOG_FILE${NC}"
    tail -20 "$LOG_FILE"
    exit 1
fi
