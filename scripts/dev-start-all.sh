#!/usr/bin/env bash
# Start all 3 Gatsby dev servers detached in the background.
# Portal: 8000, Designer: 8001, Modeler: 8002
#
# Flags:
#   --clean   rm -rf .cache public node_modules/.cache in each app first
#
# Logs:  /tmp/dhc-{portal,designer,modeler}.log
# PIDs:  /tmp/dhc-{portal,designer,modeler}.pid
# Stop:  scripts/dev-stop-all.sh

# Guard against being sourced — would exit the caller's shell on any error
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
  echo "ERROR: run this script directly (./dev-start-all.sh), do not source it." >&2
  return 1 2>/dev/null || exit 1
fi

set -e

CLEAN=0
for arg in "$@"; do
  [ "$arg" = "--clean" ] && CLEAN=1
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# --- Preflight: Node version (needs 22.x) ---
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node not found on PATH" >&2
  exit 1
fi
NODE_MAJOR="$(node -v | sed 's/^v\([0-9]*\).*/\1/')"
if [ "$NODE_MAJOR" != "22" ]; then
  echo "WARNING: Node $(node -v) detected; Gatsby apps target Node 22 LTS." >&2
fi

echo "Starting DigitalHome.Cloud dev servers..."

# Free ports from any prior dev-server instances
for port in 8000 8001 8002; do
  if fuser -k "${port}/tcp" 2>/dev/null; then
    echo "  Killed process on port ${port}"
  fi
done

preflight_app() {
  local name="$1" dir="$2"
  local app_dir="$ROOT_DIR/repos/${dir}"

  if [ ! -d "$app_dir" ]; then
    echo "ERROR: $app_dir not found" >&2
    return 1
  fi

  # 1. aws-exports.js — must exist (symlink from umbrella master or file)
  if [ ! -f "$app_dir/src/aws-exports.js" ]; then
    echo "ERROR: ${name}: src/aws-exports.js missing — run '$SCRIPT_DIR/sync-env.sh' first" >&2
    return 1
  fi

  # 2. .env.development — generate from aws-exports if missing
  if [ ! -f "$app_dir/.env.development" ]; then
    if [ -f "$app_dir/scripts/generate-aws-config-from-master.js" ]; then
      echo "  ${name}: .env.development missing, generating…"
      (cd "$app_dir" && node scripts/generate-aws-config-from-master.js)
    else
      echo "ERROR: ${name}: .env.development missing and no generator script" >&2
      return 1
    fi
  fi

  # 3. node_modules present
  if [ ! -d "$app_dir/node_modules" ]; then
    echo "ERROR: ${name}: node_modules missing — run 'yarn install' in $app_dir" >&2
    return 1
  fi

  # 4. Optional cache wipe
  if [ "$CLEAN" = "1" ]; then
    echo "  ${name}: clearing .cache, public, node_modules/.cache"
    rm -rf "$app_dir/.cache" "$app_dir/public" "$app_dir/node_modules/.cache"
  fi
}

start_app() {
  local name="$1" dir="$2"
  local log="/tmp/dhc-${name}.log"
  local pidfile="/tmp/dhc-${name}.pid"
  (
    cd "$ROOT_DIR/repos/${dir}"
    nohup yarn develop >"$log" 2>&1 &
    echo $! >"$pidfile"
    disown
  )
  echo "  ${name}: pid $(cat "$pidfile"), log ${log}"
}

for app in portal designer modeler; do
  preflight_app "$app" "$app"
done

start_app portal   portal
start_app designer designer
start_app modeler  modeler

echo ""
echo "Servers starting (Gatsby takes ~30s to bind):"
echo "  Portal:   http://localhost:8000"
echo "  Designer: http://localhost:8001"
echo "  Modeler:  http://localhost:8002"
echo ""
echo "Tail logs:  tail -f /tmp/dhc-*.log"
echo "Stop all:   $SCRIPT_DIR/dev-stop-all.sh"
