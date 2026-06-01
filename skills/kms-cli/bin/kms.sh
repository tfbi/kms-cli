#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CONFIG_PATH=$(CDPATH= cd -- "$SCRIPT_DIR/../config" 2>/dev/null && pwd)/config.toml

if [ -x "$SCRIPT_DIR/kms-linux-amd64" ]; then
  KMS_BIN="$SCRIPT_DIR/kms-linux-amd64"
elif [ -x "$SCRIPT_DIR/kms" ]; then
  KMS_BIN="$SCRIPT_DIR/kms"
else
  echo "未找到 Linux 可执行文件，请把 kms-linux-amd64 放到: $SCRIPT_DIR" >&2
  exit 1
fi

HAS_CONFIG=0
for arg in "$@"; do
  case "$arg" in
    --config|--config=*)
      HAS_CONFIG=1
      ;;
  esac
done

if [ "$HAS_CONFIG" -eq 0 ] && [ -f "$CONFIG_PATH" ]; then
  exec "$KMS_BIN" --config "$CONFIG_PATH" "$@"
fi

exec "$KMS_BIN" "$@"
