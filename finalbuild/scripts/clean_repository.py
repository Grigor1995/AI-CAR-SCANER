"""Remove only untracked Python/test/lint caches. Preview is the default.

Build outputs, test reports, SDKs, environments, models and user data are kept.
The entrypoint is repository-root clean.py and works from any working directory.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIRS = frozenset({'__pycache__', '.pytest_cache', '.ruff_cache'})
SKIP_DIRS = frozenset({'.git', '.venv', 'venv', '.build-tools', 'artifacts', 'build',
                       'build-debug', 'build-release', 'dist', 'dist-debug', 'dist-release',
                       'desktop-test-reports', '.gradle', '.kotlin', 'node_modules',
                       'models', 'assets', 'VehicleModels', 'resources'})


@dataclass(frozen=True)
class Candidate:
    path: Path
    bytes: int


def tracked_paths(root: Path) -> frozenset[str]:
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True, check=True)
    return frozenset(os.fsdecode(path) for path in result.stdout.split(b'\0') if path)


def is_link(path: Path) -> bool:
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def tree_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [name for name in dirs if not is_link(Path(base) / name)]
        for name in files:
            file = Path(base) / name
            if not is_link(file):
                total += file.stat().st_size
    return total


def candidates(root: Path, tracked: frozenset[str]) -> list[Candidate]:
    root = root.resolve()
    result = []
    def protected(path):
        relative = path.relative_to(root).as_posix()
        return relative in tracked or any(name.startswith(relative + '/') for name in tracked)
    for base, dirs, files in os.walk(root, followlinks=False):
        retained = []
        for name in dirs:
            path = Path(base) / name
            if is_link(path) or name in SKIP_DIRS:
                continue
            if name in CACHE_DIRS:
                if not protected(path): result.append(Candidate(path, tree_bytes(path)))
                # Do not traverse even a tracked cache directory.
            else:
                retained.append(name)
        dirs[:] = retained
        for name in files:
            path = Path(base) / name
            if (name == '.coverage' or name.startswith('.coverage.')) and not is_link(path) and not protected(path):
                result.append(Candidate(path, tree_bytes(path)))
    return sorted(result, key=lambda candidate: str(candidate.path))


def remove(root: Path, candidate: Candidate) -> None:
    root = root.resolve()
    path = candidate.path
    if is_link(path) or not path.resolve().is_relative_to(root) or path.resolve() == root:
        raise ValueError(f'Unsafe cleanup path: {path}')
    if path.is_dir(): shutil.rmtree(path)
    elif path.exists(): path.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Remove the listed untracked caches; otherwise preview only')
    args = parser.parse_args(argv)
    try:
        plan = candidates(ROOT, tracked_paths(ROOT))
        for candidate in plan:
            print(f'{candidate.path.relative_to(ROOT)} ({candidate.bytes:,} bytes)')
        if args.apply:
            for candidate in plan: remove(ROOT, candidate)
        print(f'{"Removed" if args.apply else "Preview"}: {len(plan)} cache entries, {sum(c.bytes for c in plan):,} bytes')
        if not args.apply: print('Run python clean.py --apply to remove these caches.')
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Cleanup stopped: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
