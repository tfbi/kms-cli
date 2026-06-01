#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CONFIG_PATH=$(CDPATH= cd -- "$SCRIPT_DIR/../config" 2>/dev/null && pwd)/config.toml
OS_NAME=$(uname -s 2>/dev/null || echo unknown)
ARCH_NAME=$(uname -m 2>/dev/null || echo unknown)

if [ "$OS_NAME" = "Darwin" ] && [ "$ARCH_NAME" = "arm64" ] && [ -x "$SCRIPT_DIR/kms-darwin-arm64" ]; then
  KMS_BIN="$SCRIPT_DIR/kms-darwin-arm64"
elif [ "$OS_NAME" = "Linux" ] && { [ "$ARCH_NAME" = "x86_64" ] || [ "$ARCH_NAME" = "amd64" ]; } && [ -x "$SCRIPT_DIR/kms-linux-amd64" ]; then
  KMS_BIN="$SCRIPT_DIR/kms-linux-amd64"
elif [ -x "$SCRIPT_DIR/kms" ]; then
  KMS_BIN="$SCRIPT_DIR/kms"
else
  echo "未找到适合当前系统的 kms 可执行文件: $OS_NAME/$ARCH_NAME" >&2
  echo "请检查 bin 目录是否包含 kms-darwin-arm64、kms-linux-amd64 或 kms。" >&2
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
