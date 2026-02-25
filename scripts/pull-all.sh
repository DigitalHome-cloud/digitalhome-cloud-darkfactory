#!/usr/bin/env bash
# Pull latest changes in each sub-repo.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

REPOS=("portal" "designer" "modeler")

echo "=== Pulling latest changes ==="
echo ""

for repo in "${REPOS[@]}"; do
  REPO_DIR="$ROOT_DIR/repos/$repo"
  if [ -d "$REPO_DIR/.git" ] || [ -f "$REPO_DIR/.git" ]; then
    echo "--- $repo ---"
    cd "$REPO_DIR"
    git pull
    echo ""
  else
    echo "--- $repo --- (not initialized, skipping)"
    echo ""
  fi
done

echo "Done."
