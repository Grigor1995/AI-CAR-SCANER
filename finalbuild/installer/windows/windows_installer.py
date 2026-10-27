"""User-scoped online installer helper; no Git client or shell interpolation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

OWNER = 'AI-Car-Scanner-online-installer-v1'
MARKER = '.ai-car-installer.json'
REPOSITORY = 'Grigor1995/AI-CAR-SCANER'


def manifest_data(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('repository') != REPOSITORY or not re.fullmatch(r'[0-9a-f]{40}', data.get('commit', '')):
        raise ValueError('Installer manifest must pin the official repository and a full commit SHA')
    return data


def claim_root(root):
    root = root.resolve()
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise ValueError('Choose a dedicated application folder')
    marker = root / MARKER
    if marker.is_file():
        if json.loads(marker.read_text(encoding='utf-8')).get('owner') != OWNER:
            raise ValueError('Installation folder belongs to another application')
    elif root.exists() and any(root.iterdir()):
        raise ValueError('Installation folder must be empty or managed by this installer')
    root.mkdir(parents=True, exist_ok=True)
    if not marker.exists():
        marker.write_text(json.dumps({'owner': OWNER}) + '\n', encoding='utf-8')
    return root


def extract_source(archive, output, commit):
    """Validate the whole snapshot before writing; never follow archive links."""
    prefix = 'AI-CAR-SCANER-' + commit
    with zipfile.ZipFile(archive) as source:
        total = 0
        for item in source.infolist():
            name = PurePosixPath(item.filename.replace('\\', '/'))
            if (not name.parts or name.parts[0] != prefix or name.is_absolute()
                    or '..' in name.parts or any(':' in part or part.rstrip(' .') != part
                        or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', part, re.I)
                        for part in name.parts)
                    or stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError('Unsafe repository snapshot entry: ' + item.filename)
            if not output.joinpath(*name.parts).resolve().is_relative_to(output.resolve()):
                raise ValueError('Repository snapshot escapes staging folder')
            total += item.file_size
        if total > 4 * 1024**3:
            raise ValueError('Unexpectedly large repository snapshot')
        source.extractall(output)
    checkout = output / prefix
    for relative in ('runner.py', 'finalbuild/scripts/local_runner.py', 'finalbuild/requirements.txt'):
        if not (checkout / relative).is_file():
            raise ValueError('Incomplete repository snapshot: ' + relative)
    return checkout


def promote_source(checkout, repository, previous_files=()):
    """Update only snapshot files; retain the venv, AI model and runner state."""
    files = {p.relative_to(checkout).as_posix() for p in checkout.rglob('*') if p.is_file()}
    # Validate manifest paths before deleting files from an earlier snapshot.
    for relative in set(previous_files) - files:
        path = repository / relative
        if not path.resolve().is_relative_to(repository.resolve()) or Path(relative).is_absolute():
            raise ValueError('Invalid previous installation manifest')
        if path.is_file():
            path.unlink()
    for relative in sorted(files):
        destination = repository / relative
        if not destination.resolve().is_relative_to(repository.resolve()):
            raise ValueError('Linked installation path is not overwritten')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checkout / relative, destination)
    return sorted(files)


def install(args):
    manifest = manifest_data(args.manifest)
    root = claim_root(args.root)
    logs = root / 'logs'
    logs.mkdir(exist_ok=True)
    log = logs / ('setup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.log')
    repository = root / 'repo'
    if repository.is_symlink() or getattr(repository, 'is_junction', lambda: False)():
        raise ValueError('A linked repository is not modified by the installer')
    previous = json.loads((root / MARKER).read_text(encoding='utf-8'))
    # Preserve the previous file list until a replacement snapshot is promoted.
    with log.open('w', encoding='utf-8') as output:
        def progress(message):
            print(message, flush=True)
            print(message, file=output, flush=True)
        progress('[SETUP] Repository: ' + REPOSITORY + '@' + manifest['commit'])
        with tempfile.TemporaryDirectory(prefix='ai-car-source-', dir=root) as staging:
            stage = Path(staging)
            archive = stage / 'repository.zip'
            url = f'https://codeload.github.com/{REPOSITORY}/zip/{manifest["commit"]}'
            progress('[DOWNLOAD] GitHub source snapshot; internet access required')
            request = urllib.request.Request(url, headers={'User-Agent': OWNER})
            with urllib.request.urlopen(request, timeout=60) as response, archive.open('wb') as destination:
                if not response.geturl().startswith('https://'):
                    raise ValueError('Insecure download redirect rejected')
                count = 0
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    if count > 1024**3:
                        raise ValueError('Unexpectedly large repository download')
                    destination.write(chunk)
            checkout = extract_source(archive, stage, manifest['commit'])
            previous['ready'] = False
            (root / MARKER).write_text(json.dumps(previous, indent=2), encoding='utf-8')
            previous['files'] = promote_source(checkout, repository, previous.get('files', []))
            previous.update(owner=OWNER, commit=manifest['commit'], ready=False)
            (root / MARKER).write_text(json.dumps(previous, indent=2), encoding='utf-8')
        command = [sys.executable, str(repository / 'runner.py'), 'setup', '--skip-android']
        if not args.with_ai:
            command.append('--skip-ai')
        progress('[SETUP] Desktop/backend dependencies' + (' + local AI (several GB)' if args.with_ai else '; local AI disabled'))
        env = os.environ.copy()
        env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
        with subprocess.Popen(command, cwd=repository, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace') as child:
            for line in child.stdout:
                progress(line.rstrip('\n'))
            code = child.wait()
        if code:
            raise RuntimeError(f'Application setup failed ({code}); see {log}')
        for relative in ('.venv/Scripts/pythonw.exe', '.runner-state.json'):
            if not (repository / relative).is_file():
                raise RuntimeError('Setup returned without required file: ' + relative)
        previous.update(ready=True, ai_enabled=args.with_ai)
        (root / MARKER).write_text(json.dumps(previous, indent=2), encoding='utf-8')
        progress('[READY] Desktop and backend installed. AI: ' + str(args.with_ai))
    return 0


def launch(args):
    root = args.root.resolve()
    installed = json.loads((root / MARKER).read_text(encoding='utf-8'))
    if installed.get('owner') != OWNER or not installed.get('ready'):
        raise RuntimeError('Installation is incomplete; run Setup again')
    repository = root / 'repo'
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
    # Desktop's runner owns backend + AI startup/shutdown. Hide its console,
    # retain stdout/stderr on disk, and report failed startup through a dialog.
    with (root / 'logs/desktop.log').open('a', encoding='utf-8') as output:
        result = subprocess.run([str(repository / '.venv/Scripts/python.exe'), str(repository / 'runner.py'), 'desktop'],
                                cwd=repository, env=env, stdout=output, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(f'Desktop exited with code {result.returncode}. See {root / "logs/desktop.log"}')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('install')
    setup.add_argument('--root', type=Path, required=True)
    setup.add_argument('--manifest', type=Path, required=True)
    setup.add_argument('--with-ai', action='store_true')
    run = commands.add_parser('launch')
    run.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return install(args) if args.command == 'install' else launch(args)
    except Exception as error:
        if args.command == 'launch' and os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(error), 'AI Car Scanner', 0x10)
        else:
            marker = args.root / MARKER
            if marker.is_file():
                try:
                    if json.loads(marker.read_text(encoding='utf-8')).get('owner') == OWNER:
                        logs = args.root / 'logs'
                        logs.mkdir(exist_ok=True)
                        with (logs / 'bootstrap-errors.log').open('a', encoding='utf-8') as output:
                            print(str(error), file=output)
                except (OSError, ValueError):
                    pass
            if sys.stderr is not None:
                print('[SETUP ERROR] ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
