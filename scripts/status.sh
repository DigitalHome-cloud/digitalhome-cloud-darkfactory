#!/usr/bin/env bash
# Show git status and recent commits across all sub-repos.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
_ORIG_DIR="$(pwd)"

REPOS=("portal" "designer" "modeler")

echo "=== DarkFactory Workspace Status ==="
echo ""

# Umbrella repo status
echo "--- darkfactory (umbrella) ---"
cd "$ROOT_DIR"
echo "Branch: $(git branch --show-current)"
git status --short
echo ""

for repo in "${REPOS[@]}"; do
  REPO_DIR="$ROOT_DIR/repos/$repo"
  if [ -d "$REPO_DIR/.git" ] || [ -f "$REPO_DIR/.git" ]; then
    echo "--- $repo ---"
    cd "$REPO_DIR"
    echo "Branch: $(git branch --show-current)"
    git status --short
    echo "Recent commits:"
    git log --oneline -3
    echo ""
  else
    echo "--- $repo --- (not initialized)"
    echo ""
  fi
done

cd "$_ORIG_DIR"
unset _ORIG_DIR
