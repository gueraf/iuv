#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
from watchfiles import watch

IGNORED_DIRS = {'.git', '.venv', '__pycache__'}


def run_once(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"[watch] error running command: {e}", file=sys.stderr)


def watch_loop(cmd: list[str], debounce_ms: int) -> int:
    root = Path.cwd()
    print(f"[iuv] watching {root} recursively. Press Ctrl+C to stop.")
    print(f"[iuv] command: {' '.join(cmd)}")
    run_once(cmd)
    try:
        for changes in watch(root, debounce=debounce_ms):  # type: ignore[arg-type]
            # Filter ignored directories manually
            filtered = [c for c in changes if not any(part in IGNORED_DIRS for part in Path(c[1]).parts)]
            if not filtered:
                continue
            print(f"[iuv] {len(filtered)} change(s) detected -> rerun")
            run_once(cmd)
    except KeyboardInterrupt:
        print("\n[iuv] stopped")
        return 0
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='iuv', description='Simple uv watch wrapper.')
    parser.add_argument('--debounce', '-d', type=int, default=150, help='Debounce time in ms (default 150)')
    parser.add_argument('cmd', nargs=argparse.REMAINDER, help='iuv run <args...> -> executes `uv run <args...>` on changes')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.cmd or args.cmd[0] != 'run':
        print('Usage: iuv run <script_or_module> [args...]', file=sys.stderr)
        return 1
    # Transform: iuv run foo.py --arg -> uv run foo.py --arg
    uv_cmd = ['uv', 'run'] + [c for c in args.cmd[1:] if c != '--']
    return watch_loop(uv_cmd, args.debounce)

if __name__ == "__main__":
    raise SystemExit(main())

