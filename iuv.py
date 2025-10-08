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
    print(f"[watch] watching {root} recursively. Press Ctrl+C to stop.")
    print(f"[watch] command: {' '.join(cmd)}")
    run_once(cmd)
    try:
        for changes in watch(root, debounce=debounce_ms):  # type: ignore[arg-type]
            # Filter ignored directories manually
            filtered = [c for c in changes if not any(part in IGNORED_DIRS for part in Path(c[1]).parts)]
            if not filtered:
                continue
            print(f"[watch] {len(filtered)} change(s) detected -> rerun")
            run_once(cmd)
    except KeyboardInterrupt:
        print("\n[watch] stopped")
        return 0
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='iuv', description='Simple uv watch wrapper.')
    sub = parser.add_subparsers(dest='subcommand')
    w = sub.add_parser('watch', help='Watch current directory & rerun uv command')
    w.add_argument('--debounce', '-d', type=int, default=150, help='Debounce time in ms (default 150)')
    w.add_argument('cmd', nargs=argparse.REMAINDER, help='Command to execute (e.g. uvx run script.py)')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.subcommand == 'watch':
        if not args.cmd:
            print('No command provided to watch. Example: iuv.py watch uvx run app.py', file=sys.stderr)
            return 1
        cmd = [c for c in args.cmd if c != '--']
        return watch_loop(cmd, args.debounce)
    else:
        print('Use: iuv.py watch <uv / uvx args...>')
        return 0

if __name__ == "__main__":
    raise SystemExit(main())

