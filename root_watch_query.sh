#!/bin/bash
# 根目录写入监控查询脚本
# 用法: root_watch_query.sh            # 最近10分钟
#       root_watch_query.sh today      # 今天
#       root_watch_query.sh hour       # 最近1小时
if [ "$1" = "today" ]; then
    TS="today"
    N=5000
elif [ "$1" = "hour" ]; then
    TS="$(date -d '1 hour ago' '+%m/%d/%Y %H:%M:%S')"
    N=3000
else
    TS="recent"
    N=500
fi

LOGDIR=/usr/local/var/log/root_watch

echo "======== 1. 根目录直下文件事件（已排除系统噪音）========"
tail -n "$N" "$LOGDIR/inotify.log" 2>/dev/null | grep -E ' (CREATE|MODIFY|DELETE|MOVED_(FROM|TO)|ATTRIB) ' | grep -v 'ISDIR root'
echo "---- 以上无输出 = 该时段根目录没有被写入 ----"

echo ""
echo "======== 2. 写入者详情（仅根目录直下创建/删除，含进程+完整命令）========"
ausearch -if "$LOGDIR/audit.log" -k root_write -ts "$TS" -i 2>/dev/null \
  | awk '/^----/ { if (show && !bad) print buf; buf=""; show=0; bad=0; next } { buf = buf $0 "\n" } /name=\/ inode=2 / { show=1 } /success=no / { bad=1 }' \
  | grep -E 'type=PROCTITLE|type=PATH|type=SYSCALL|^----'

echo ""
echo "======== 3. 当前根目录直下内容（供对比异常文件）========"
ls -la /
