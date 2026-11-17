#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 D-LAB-5
"""
Start Claude Code in the DigitalHome.Cloud umbrella (this repository) with
the edge repositories that sit beside it added:

    ../digitalhome-cloud-darkfactory   here: the platform, its docs, the session
    ../digitalhome-devops-edge         added with --add-dir when it is there
    ../digitalhome-pro-edge            added with --add-dir when it is there

Run it through start-claude.sh. Anything after the command goes to claude as
it is, e.g. `./start-claude.sh --continue`. `--print-command` only shows what
would run.

A repository that is not beside this one is named with the command that
clones it, and left out: the session starts anyway.

Python's standard library only. Made from the shared-docs template's
start-claude.py (d-lab-5/template-dlab5-shared), with the list here instead
of shared.json.
"""

import shlex
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


ADD_REPOS = [
    "DigitalHome-cloud/digitalhome-devops-edge",
    "DigitalHome-cloud/digitalhome-pro-edge",
]


def app_dirs():
    found = []
    for repo in ADD_REPOS:
        here = REPO.parent / repo.split("/")[-1]
        if (here / ".git").exists():
            found.append(here)
        else:
            print(f"not beside {REPO.name}: {repo}  (gh repo clone {repo} {here})", file=sys.stderr)
    return found


def main(argv):
    dry = "--print-command" in argv
    rest = [a for a in argv if a != "--print-command"]
    args = [a for d in app_dirs() for a in ("--add-dir", str(d))] + rest
    if dry:
        print(" ".join(["claude"] + [shlex.quote(a) for a in args]))
        return 0
    exe = shutil.which("claude")     # on Windows this finds claude.exe or the claude.cmd shim
    if not exe:
        print("Claude Code (`claude`) is not installed or not on PATH", file=sys.stderr)
        return 1
    try:
        return subprocess.call([exe] + args, cwd=REPO)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
