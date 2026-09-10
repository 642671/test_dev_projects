#!/usr/bin/env bash
# SCSI host rescan helper for a dedicated test NAS.
# Simulates a hot-insert after a kernel-level remove while the physical drive
# remains installed. Default mode is --dry-run.
#
# Example:
#   HOST=host37 TARGET=/dev/sdj EXPECTED_SERIAL=ZGY7DDD2 \
#     bash nas_hdd_hot_insert.sh /dev/sdj --execute

set -u

TARGET="${1:-}"
MODE="dry-run"
HOST="${HOST:-host37}"
EXPECTED_SERIAL="${EXPECTED_SERIAL:-}"
EXPECTED_MODEL="${EXPECTED_MODEL:-}"

shift || true
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      ;;
    --execute)
      MODE="execute"
      ;;
    *)
      echo "UNKNOWN_OPTION $1" >&2
      exit 2
      ;;
  esac
  shift || true
done

if [ -z "$TARGET" ]; then
  echo "USAGE: $0 /dev/sdX [--dry-run|--execute]"
  exit 2
fi

HOST_FILE="/sys/class/scsi_host/$HOST/scan"
echo "TARGET=$TARGET"
echo "HOST=$HOST"
echo "MODE=$MODE"

if [ ! -e "$HOST_FILE" ]; then
  echo "SCAN_ENTRY_MISSING $HOST_FILE"
  exit 1
fi

if [ -b "$TARGET" ]; then
  echo "TARGET_ALREADY_PRESENT $TARGET"
  exit 0
fi

if [ "$MODE" = "execute" ]; then
  echo "SCAN_EXECUTING $HOST_FILE"
  if [ ! -w "$HOST_FILE" ]; then
    echo "SCAN_ENTRY_NOT_WRITABLE $HOST_FILE"
    exit 1
  fi
  echo "- - -" > "$HOST_FILE"
  udevadm settle --timeout=10 >/dev/null 2>&1 || true

  FOUND=""
  for i in $(seq 1 30); do
    if [ -b "$TARGET" ]; then
      FOUND="$TARGET"
      break
    fi
    if [ -n "$EXPECTED_SERIAL" ] && command -v lsblk >/dev/null 2>&1; then
      FOUND="$(lsblk -dn -o NAME,SERIAL,MODEL 2>/dev/null | grep -F "$EXPECTED_SERIAL" | head -n1 | awk '{print $1}')"
      if [ -n "$FOUND" ]; then
        FOUND="/dev/$FOUND"
        break
      fi
    fi
    sleep 1
  done

  if [ -z "$FOUND" ]; then
    echo "NOT_FOUND"
    exit 1
  fi

  echo "FOUND=$FOUND"
  lsblk -d -o NAME,PATH,TRAN,MODEL,SERIAL,SIZE "$FOUND"
else
  echo "DRY_RUN echo '- - -' > $HOST_FILE"
  echo "DRY_RUN udevadm settle && lsblk"
fi
