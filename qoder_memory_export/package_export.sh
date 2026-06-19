#!/bin/bash
# ============================================================
# Qoder 记忆与知识库导出打包脚本
# 用途：将 Mac 环境的 Qoder 记忆、知识库等数据打包，
#       用于迁移到 Windows 公司电脑
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$SCRIPT_DIR"
OUTPUT_FILE="$PROJECT_DIR/qoder_memory_export_$(date +%Y%m%d).zip"

echo "=== Qoder 记忆导出打包工具 ==="
echo "项目目录: $PROJECT_DIR"
echo ""

# 检查导出目录是否存在
if [ ! -d "$EXPORT_DIR" ]; then
    echo "错误: 导出目录不存在: $EXPORT_DIR"
    echo "请先运行完整导出流程"
    exit 1
fi

# 检查 repowiki 是否已复制
if [ ! -d "$EXPORT_DIR/repowiki" ]; then
    echo "提示: repowiki 目录不存在，正在复制..."
    mkdir -p "$EXPORT_DIR/repowiki"
    if [ -d "$PROJECT_DIR/.qoder/repowiki" ]; then
        cp -r "$PROJECT_DIR/.qoder/repowiki/"* "$EXPORT_DIR/repowiki/"
        echo "  ✓ repowiki 已复制"
    else
        echo "  ⚠ .qoder/repowiki 不存在，跳过"
    fi
fi

# 检查 JSON 备份是否已复制
if [ ! -d "$EXPORT_DIR/json_backup" ]; then
    echo "提示: json_backup 目录不存在，正在复制..."
    mkdir -p "$EXPORT_DIR/json_backup"
    QODER_CACHE="$HOME/Library/Application Support/Qoder/SharedClientCache/index"
    if [ -d "$QODER_CACHE" ]; then
        cp "$QODER_CACHE/memory_topic_tree/"*.json "$EXPORT_DIR/json_backup/" 2>/dev/null || true
        cp "$QODER_CACHE/memory_network/"*.json "$EXPORT_DIR/json_backup/" 2>/dev/null || true
        echo "  ✓ JSON 备份已复制"
    else
        echo "  ⚠ Qoder 缓存目录不存在（非 Mac 环境？），跳过"
    fi
fi

# 检查 memories_export.md 是否存在
if [ ! -f "$EXPORT_DIR/memories_export.md" ]; then
    echo "  ⚠ memories_export.md 不存在！记忆内容未导出"
    echo "  请确保已通过 Qoder 对话完成记忆导出流程"
fi

# 检查 restore_prompt.md 是否存在
if [ ! -f "$EXPORT_DIR/restore_prompt.md" ]; then
    echo "  ⚠ restore_prompt.md 不存在！恢复提示词未生成"
fi

# 统计导出内容
echo ""
echo "=== 导出内容统计 ==="
echo "记忆导出文件: $([ -f "$EXPORT_DIR/memories_export.md" ] && echo '✓ 存在' || echo '✗ 缺失')"
echo "恢复提示词:   $([ -f "$EXPORT_DIR/restore_prompt.md" ] && echo '✓ 存在' || echo '✗ 缺失')"
echo "知识库文件:   $([ -d "$EXPORT_DIR/repowiki" ] && echo "✓ $(find "$EXPORT_DIR/repowiki" -name '*.md' | wc -l) 个文档" || echo '✗ 缺失')"
echo "JSON备份:     $([ -d "$EXPORT_DIR/json_backup" ] && echo "✓ $(ls "$EXPORT_DIR/json_backup/"*.json 2>/dev/null | wc -l) 个文件" || echo '✗ 缺失')"

# 打包为 zip
echo ""
echo "正在打包为 zip..."
cd "$PROJECT_DIR"
zip -r "$OUTPUT_FILE" "qoder_memory_export/" -x "qoder_memory_export/.DS_Store"
echo ""
echo "=== 打包完成 ==="
echo "输出文件: $OUTPUT_FILE"
echo "文件大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
