#!/usr/bin/env bash
# 将除系统盘 sdza 之外的所有磁盘重建为单个未格式化 GPT 分区。
# 注意：这是破坏性操作，默认只做 dry-run。
#
# 用法：
#   wipe_all_non_system_disks.sh --dry-run
#   wipe_all_non_system_disks.sh --execute --stop-storage

set -u

MODE="dry-run"
STOP_STORAGE="no"
PROTECTED="sdza"
ALL_DISKS="$(lsblk -d -o NAME,TYPE 2>/dev/null | awk '$2=="disk" && $1!="'$PROTECTED'"{print $1}')"

if [ "$#" -gt 0 ]; then
  case "$1" in
    --dry-run) MODE="dry-run" ;;
    --execute) MODE="execute" ;;
    --stop-storage) STOP_STORAGE="yes" ;;
    *) echo "USAGE: $0 --dry-run|--execute" >&2; exit 2 ;;
  esac
fi

echo "PROTECTED_DISK=$PROTECTED"
echo "MODE=$MODE"
echo "TARGET_DISKS=$ALL_DISKS"

if [ -z "$ALL_DISKS" ]; then
  echo "NO_TARGET_DISKS"
  exit 1
fi

for disk in $ALL_DISKS; do
  [ "$disk" = "$PROTECTED" ] && continue
  dev="/dev/$disk"
  [ -b "$dev" ] || continue

  # 拒绝挂载中的盘
  mounts="$(lsblk -rno MOUNTPOINTS "$dev" 2>/dev/null | grep -v '^[[:space:]]*$' || true)"
  if [ -n "$mounts" ]; then
    echo "SAFETY_BLOCKED mounted $dev"
    exit 1
  fi

  # 拒绝活跃 md 成员，避免格式化正在使用的 RAID
  parent="$(lsblk -dn -o PKNAME "$dev" 2>/dev/null | head -n1)"
  for md in /dev/md*; do
    [ -b "$md" ] || continue
    md_name="${md##*/}"
    for slave in /sys/class/block/$md_name/slaves/*; do
      [ -e "$slave" ] || continue
      member="/dev/$(basename "$slave")"
      member_parent="$(lsblk -dn -o PKNAME "$member" 2>/dev/null | head -n1)"
      if [ "$member" = "$dev" ] || { [ -n "$member_parent" ] && [ "/dev/$member_parent" = "$dev" ]; }; then
        echo "SAFETY_BLOCKED active_md $dev $md"
        exit 1
      fi
    done
  done
done

if [ "$MODE" = "dry-run" ]; then
  echo "[dry-run] commands: wipefs, parted mklabel gpt, parted mkpart primary 1MiB 100%"
  for disk in $ALL_DISKS; do
    [ -b "/dev/$disk" ] && echo "DRY_RUN /dev/$disk"
  done
  exit 0
fi

restore_storage() {
  if [ "$STOP_STORAGE" = "yes" ]; then
    systemctl unmask StorageManager.service >/dev/null 2>&1 || true
    systemctl daemon-reload >/dev/null 2>&1 || true
    systemctl reset-failed StorageManager.service >/dev/null 2>&1 || true
    systemctl start StorageManager.service >/dev/null 2>&1 || true
    sleep 2
    if ! systemctl is-active --quiet StorageManager.service; then
      systemctl start StorageManager.service >/dev/null 2>&1 || true
    fi
  fi
}

if [ "$STOP_STORAGE" = "yes" ]; then
  trap restore_storage EXIT
  systemctl mask StorageManager.service >/dev/null 2>&1 || true
  systemctl stop StorageManager.service >/dev/null 2>&1 || true
  sleep 2
fi

FAILED=""
LOG_FILE="/tmp/nas_wipe_before_$(date +%Y%m%d_%H%M%S).txt"
{
  echo "WIPE BEFORE $(date '+%Y-%m-%d %H:%M:%S')"
  lsblk -o NAME,TYPE,TRAN,MODEL,SERIAL,SIZE,FSTYPE,MOUNTPOINTS
} > "$LOG_FILE"
echo "LOG_FILE=$LOG_FILE"

for disk in $ALL_DISKS; do
  [ "$disk" = "$PROTECTED" ] && continue
  dev="/dev/$disk"
  [ -b "$dev" ] || continue

  echo "=== wiping $dev ==="
  wipefs -a "$dev" >/dev/null 2>&1 || true
  parted -s "$dev" mklabel gpt || { FAILED="$FAILED $dev"; continue; }
  parted -s "$dev" mkpart primary 1MiB 100% || { FAILED="$FAILED $dev"; continue; }
  blockdev --rereadpt "$dev" >/dev/null 2>&1 || true
  udevadm settle --timeout=5 >/dev/null 2>&1 || true
  wipefs -a "${dev}1" >/dev/null 2>&1 || true
  sync
  echo "OK $dev -> ${dev}1"
done

echo "=== after ==="
lsblk -o NAME,TYPE,TRAN,MODEL,SERIAL,SIZE,FSTYPE,MOUNTPOINTS

if [ -n "$FAILED" ]; then
  echo "FAILED_DISKS=$FAILED"
  exit 1
fi
echo "RESULT=completed"
