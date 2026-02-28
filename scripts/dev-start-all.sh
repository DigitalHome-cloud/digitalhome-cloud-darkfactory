#!/usr/bin/env bash
# Start all 3 Gatsby dev servers in parallel.
# Portal: 8000, Designer: 8001, Modeler: 8002
#
# Each app must have node_modules installed and .env.development configured.
# Press Ctrl+C to stop all servers.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
_ORIG_DIR="$(pwd)"

echo "Starting DigitalHome.Cloud dev servers..."
echo "  Portal:   http://localhost:8000"
echo "  Designer: http://localhost:8001"
echo "  Modeler:  http://localhost:8002"
echo ""

# Trap Ctrl+C to kill all background jobs
trap 'echo "Stopping all servers..."; kill 0; exit 0' INT TERM

(cd "$ROOT_DIR/repos/portal"   && yarn develop) &
(cd "$ROOT_DIR/repos/designer" && yarn develop) &
(cd "$ROOT_DIR/repos/modeler"  && yarn develop) &

wait

cd "$_ORIG_DIR"
unset _ORIG_DIR
