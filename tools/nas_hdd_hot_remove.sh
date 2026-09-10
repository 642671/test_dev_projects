#!/usr/bin/env bash
# Safe kernel-level hot-remove helper for a dedicated test NAS.
# Usage:
#   nas_hdd_hot_remove.sh /dev/sdX [--dry-run|--execute] [--raid-fail]
# Default mode is --dry-run.

set -u

TARGET="${1:-}"
MODE="dry-run"
RAID_FAIL="no"

shift || true
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      ;;
    --execute)
      MODE="execute"
      ;;
    --raid-fail)
      RAID_FAIL="yes"
      ;;
    *)
      echo "UNKNOWN_OPTION $1" >&2
      exit 2
      ;;
  esac
  shift || true
done

if [ -z "$TARGET" ] || [ ! -b "$TARGET" ]; then
  echo "TARGET_NOT_PRESENT $TARGET"
  exit 0
fi

TARGET_BASE="${TARGET##*/}"
SYSDIR="/sys/block/$TARGET_BASE"
DELETE_FILE="$SYSDIR/device/delete"

echo "TARGET=$TARGET"
echo "TARGET_BASE=$TARGET_BASE"
echo "MODE=$MODE"

# Never let a remote command touch the disk that backs the running root or swap.
ROOT_SOURCE="$(findmnt -n -o SOURCE / 2>/dev/null | head -n1)"
SWAP_SOURCE="$(findmnt -n -o SOURCE /swapfile 2>/dev/null | head -n1)"
SYSTEM_BASE=""
if [ -n "$ROOT_SOURCE" ] && [ -e "/sys/class/block/${ROOT_SOURCE##*/}" ]; then
  SYSTEM_BASE="$(lsblk -dn -o PKNAME "$ROOT_SOURCE" 2>/dev/null | head -n1)"
fi
if [ -n "$SWAP_SOURCE" ] && [ -e "/sys/class/block/${SWAP_SOURCE##*/}" ]; then
  SWAP_BASE="$(lsblk -dn -o PKNAME "$SWAP_SOURCE" 2>/dev/null | head -n1)"
else
  SWAP_BASE=""
fi
PARENT_BASE="$(lsblk -dn -o PKNAME "$TARGET" 2>/dev/null | head -n1)"
if [ "$PARENT_BASE" = "$SYSTEM_BASE" ] || [ "$PARENT_BASE" = "$SWAP_BASE" ]; then
  echo "SAFETY_BLOCKED system_disk"
  exit 1
fi

MOUNTS="$(lsblk -rno MOUNTPOINTS "$TARGET" 2>/dev/null | grep -v '^$' || true)"
if [ -n "$MOUNTS" ]; then
  echo "SAFETY_BLOCKED mounted"
  echo "MOUNTS=$MOUNTS"
  exit 1
fi

MD_ARRAY=""
MD_MEMBER=""
for md in /dev/md*; do
  [ -b "$md" ] || continue
  md_name="${md##*/}"
  for slave in /sys/class/block/$md_name/slaves/*; do
    [ -e "$slave" ] || continue
    member="/dev/$(basename "$slave")"
    member_parent="$(lsblk -dn -o PKNAME "$member" 2>/dev/null | head -n1)"
    if [ "$member" = "$TARGET" ] || [ -n "$member_parent" ] && [ "/dev/$member_parent" = "$TARGET" ]; then
      MD_ARRAY="$md"
      MD_MEMBER="$member"
      break 2
    fi
  done
done

echo "ROOT_SOURCE=$ROOT_SOURCE"
echo "MD_ARRAY=${MD_ARRAY:-none}"
echo "MD_MEMBER=${MD_MEMBER:-none}"

if [ -n "$MD_ARRAY" ]; then
  if [ "$RAID_FAIL" != "yes" ]; then
    echo "SAFETY_BLOCKED active_md_member"
    echo "USE --raid-fail only if this is a deliberate RAID failure test."
    exit 1
  fi
  echo "ACTION=mdadm_fail"
  if [ "$MODE" = "execute" ]; then
    mdadm --manage "$MD_ARRAY" --fail "$MD_MEMBER"
  else
    echo "DRY_RUN mdadm --manage $MD_ARRAY --fail $MD_MEMBER"
  fi
  exit 0
fi

if [ ! -e "$DELETE_FILE" ]; then
  echo "SAFETY_BLOCKED delete_entry_missing"
  echo "TARGET_ALREADY_ABSENT"
  exit 0
fi

echo "ACTION=device_delete"
echo "DELETE_FILE=$DELETE_FILE"
if [ "$MODE" = "execute" ]; then
  if [ ! -w "$DELETE_FILE" ]; then
    echo "SAFETY_BLOCKED delete_entry_not_writable"
    exit 1
  fi
  echo 1 > "$DELETE_FILE"
  udevadm settle --timeout=5 >/dev/null 2>&1 || true
  sync
  sleep 2
  if [ -e "/dev/$TARGET_BASE" ] || [ -e "$SYSDIR" ]; then
    echo "AFTER_STATE=still_present"
    exit 1
  fi
  echo "AFTER_STATE=absent"
else
  echo "DRY_RUN echo 1 > $DELETE_FILE"
fi
