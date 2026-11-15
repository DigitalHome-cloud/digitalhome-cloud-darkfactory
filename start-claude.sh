#!/usr/bin/env bash
# Claude Code in this repository, with the edge repositories beside it added
# (scripts/start-claude.py). Arguments go on to claude.
cd "$(dirname "$0")" && exec python3 scripts/start-claude.py "$@"
