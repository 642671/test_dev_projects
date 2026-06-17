#!/bin/bash
# ============================================================
# 通过 NODE_EXTRA_CA_CERTS 启动 Qoder
# 让 Qoder 的 Electron/Node.js 信任火山引擎代理的自签名证书
# 用法: bash launch_qoder.sh
# ============================================================

CERT_FILE="/Users/miaoqi/Desktop/test_dev_projects/volcano_proxy/certs/kimi_cert.pem"
QODER_BIN="/Applications/Qoder.app/Contents/MacOS/Electron"

if [ ! -f "$CERT_FILE" ]; then
    echo "[✗] 证书文件不存在: $CERT_FILE"
    exit 1
fi

echo "═══════════════════════════════════════════════════"
echo "  启动 Qoder (带自定义 CA 证书)"
echo "═══════════════════════════════════════════════════"
echo "  证书: $CERT_FILE"
echo ""

# 如果 Qoder 已在运行，先关闭
if pgrep -x "Qoder" > /dev/null 2>&1 || pgrep -x "Electron" > /dev/null 2>&1; then
    echo "[*] 检测到 Qoder 正在运行，正在关闭..."
    osascript -e 'tell application "Qoder" to quit' 2>/dev/null
    sleep 3
    # 如果还没退出，强制关闭
    pkill -x "Qoder" 2>/dev/null
    pkill -x "Electron" 2>/dev/null
    sleep 1
fi

echo "[✓] 正在启动 Qoder (NODE_EXTRA_CA_CERTS=$CERT_FILE)..."
# 直接调用 Electron 二进制文件，传递环境变量
NODE_EXTRA_CA_CERTS="$CERT_FILE" "$QODER_BIN" &
disown

sleep 2
if pgrep -f "Qoder.app" > /dev/null 2>&1; then
    echo ""
    echo "[✓] Qoder 已启动!"
    echo ""
    echo "  现在可以在 Qoder 中添加 Kimi 自定义模型:"
    echo "    Provider: Kimi"
    echo "    API Key:  sk-开头任意值 (如 sk-aBcDeFgHiJkLmNoPqRsTuVwXyZ012345)"
    echo "    模型:     从 Kimi 下拉列表选择默认模型"
else
    echo "[✗] Qoder 启动可能失败，请检查"
fi
