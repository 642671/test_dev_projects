#!/bin/bash
# 根目录写入监控守护脚本
# 监控 / 直下的文件创建/删除/移动/修改/属性变更事件，记录时间戳
# 事件发生后尝试用 lsof 抓取正在操作该文件的进程（写入者调查）
LOG=/usr/local/var/log/root_watch/inotify.log
MAX_SIZE_KB=10240

inotifywait -m -e create -e moved_to -e delete -e moved_from -e modify -e attrib / 2>>"$LOG" | while IFS= read -r line; do
    TS=$(date '+%Y-%m-%d %H:%M:%S')
    # 日志轮转：超过 10MB 时备份一份
    if [ -f "$LOG" ] && [ "$(du -k "$LOG" | cut -f1)" -ge "$MAX_SIZE_KB" ]; then
        mv "$LOG" "$LOG.1"
    fi
    echo "[$TS] $line" >> "$LOG"
    # 从事件行提取文件名，尝试抓取写入进程
    fname=$(echo "$line" | awk '{print $NF}')
    if [ -n "$fname" ] && [ "$fname" != "/" ]; then
        echo "[PROC $TS] --- lsof /$fname ---" >> "$LOG"
        lsof "/$fname" 2>/dev/null | while IFS= read -r pline; do
            echo "[PROC $TS] $pline" >> "$LOG"
        done
    fi
done
