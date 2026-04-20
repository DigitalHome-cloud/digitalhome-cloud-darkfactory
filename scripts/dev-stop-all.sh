#!/usr/bin/env bash
# Stop the dev servers started by dev-start-all.sh.

echo "Stopping DigitalHome.Cloud dev servers..."

for name in portal designer modeler; do
  pidfile="/tmp/dhc-${name}.pid"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile")
    if kill "$pid" 2>/dev/null; then
      echo "  ${name}: stopped pid ${pid}"
    fi
    rm -f "$pidfile"
  fi
done

# Belt-and-suspenders: free the ports in case children outlived the parent
for port in 8000 8001 8002; do
  if fuser -k "${port}/tcp" 2>/dev/null; then
    echo "  Freed port ${port}"
  fi
done
