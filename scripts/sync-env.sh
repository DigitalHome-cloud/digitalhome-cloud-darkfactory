#!/usr/bin/env bash
# sync-env.sh — Single source of truth for Amplify config across all apps.
#
# 1. Symlinks umbrella amplify/ into each repo (replaces per-repo copies)
# 2. Symlinks umbrella src/aws-exports.js into each repo
# 3. Runs each repo's generate-aws-config-from-master.js to produce
#    .env.development and src/aws-exports.deployment.js
# 4. Runs amplify codegen in each repo (GraphQL queries/mutations/schema)
#
# Prerequisites:
#   amplify pull (run once at umbrella root to create amplify/ + src/aws-exports.js)
#
# Usage:
#   ./scripts/sync-env.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MASTER_EXPORTS="$ROOT_DIR/src/aws-exports.js"
MASTER_AMPLIFY="$ROOT_DIR/amplify"

# --- Verify umbrella master files ---

if [ ! -f "$MASTER_EXPORTS" ]; then
  echo "ERROR: $MASTER_EXPORTS not found." >&2
  echo "Run 'amplify pull' in $ROOT_DIR first." >&2
  exit 1
fi

if [ ! -d "$MASTER_AMPLIFY" ]; then
  echo "ERROR: $MASTER_AMPLIFY not found." >&2
  echo "Run 'amplify pull' in $ROOT_DIR first." >&2
  exit 1
fi

echo "Master aws-exports: $MASTER_EXPORTS"
echo "Master amplify/:    $MASTER_AMPLIFY"
echo ""

# --- Helper: create or verify a symlink ---
ensure_symlink() {
  local target="$1" link_path="$2" label="$3"

  if [ -L "$link_path" ]; then
    current="$(readlink -f "$link_path" 2>/dev/null || true)"
    expected="$(readlink -f "$target")"
    if [ "$current" = "$expected" ]; then
      echo "  ${label}: symlink already correct"
    else
      rm -f "$link_path"
      ln -s "$target" "$link_path"
      echo "  ${label}: symlink updated"
    fi
  elif [ -e "$link_path" ]; then
    # Real file or directory — remove and replace
    rm -rf "$link_path"
    ln -s "$target" "$link_path"
    echo "  ${label}: replaced with symlink"
  else
    ln -s "$target" "$link_path"
    echo "  ${label}: symlink created"
  fi
}

# --- Per-app sync ---

for app in portal designer modeler; do
  app_dir="$ROOT_DIR/repos/${app}"

  if [ ! -d "$app_dir" ]; then
    echo "  ${app}: repo not found at $app_dir — skipping"
    echo ""
    continue
  fi

  echo "[$app]"

  # 1. Symlink amplify/ → umbrella master
  ensure_symlink "$MASTER_AMPLIFY" "$app_dir/amplify" "${app}/amplify"

  # 2. Symlink src/aws-exports.js → umbrella master
  ensure_symlink "$MASTER_EXPORTS" "$app_dir/src/aws-exports.js" "${app}/aws-exports.js"

  # 3. Generate .env.development + aws-exports.deployment.js
  gen_script="$app_dir/scripts/generate-aws-config-from-master.js"
  if [ -f "$gen_script" ]; then
    (cd "$app_dir" && node scripts/generate-aws-config-from-master.js)
    echo "  ${app}: .env.development + aws-exports.deployment.js generated"
  else
    echo "  ${app}: no generate script — skipping env codegen"
  fi

  # 4. Amplify codegen (GraphQL queries, mutations, schema, types)
  if [ -f "$app_dir/.graphqlconfig.yml" ]; then
    echo "  ${app}: running amplify codegen..."
    (cd "$app_dir" && amplify codegen 2>&1 | sed 's/^/    /')
    echo "  ${app}: GraphQL codegen complete"
  else
    echo "  ${app}: no .graphqlconfig.yml — skipping amplify codegen"
  fi

  echo ""
done

echo "Done. All repos synced to umbrella amplify/ and aws-exports.js."
echo "Start dev servers with: $SCRIPT_DIR/dev-start-all.sh"
