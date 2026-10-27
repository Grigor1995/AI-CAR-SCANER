"""Prepare and compile a pinned Windows installer; never publishes a release."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'finalbuild/installer/windows'


def compiler(explicit=None):
    candidates = [explicit, shutil.which('ISCC.exe')]
    for environment in ('ProgramFiles(x86)', 'ProgramFiles', 'LOCALAPPDATA'):
        if os.environ.get(environment):
            base = Path(os.environ[environment])
            candidates += [base / 'Inno Setup 6/ISCC.exe', base / 'Programs/Inno Setup 6/ISCC.exe']
    return next((Path(p).resolve() for p in candidates if p and Path(p).is_file()), None)


def prepare(output, commit):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Use a full 40-character commit SHA; branch names are not pinned installers')
    payload = output / 'payload'
    payload.mkdir(parents=True, exist_ok=True)
    for name in ('bootstrap.ps1', 'windows_installer.py', 'AI-Car-Scanner.iss', 'wizard-side.bmp', 'wizard-icon.bmp'):
        shutil.copy2(SOURCE / name, payload / name)
    shutil.copy2(ROOT / 'finalbuild/assets/AI-Car-Scanner.ico', payload / 'app.ico')
    (payload / 'manifest.json').write_text(json.dumps({
        'repository': 'Grigor1995/AI-CAR-SCANER', 'commit': commit,
    }, indent=2) + '\n', encoding='utf-8')
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iscc', type=Path, help='Inno Setup 6.3+ ISCC.exe')
    parser.add_argument('--commit', help='Official repository commit, default: local HEAD; must be pushed before distributing')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/windows-installer')
    parser.add_argument('--prepare-only', action='store_true', help='Prepare inspectable payload without a Windows compiler')
    args = parser.parse_args(argv)
    try:
        commit = args.commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        iscc = compiler(args.iscc)
        if not args.prepare_only and platform.system() != 'Windows':
            raise ValueError('Compile Setup.exe on Windows; use --prepare-only to inspect the payload here')
        if not args.prepare_only and iscc is None:
            raise ValueError('Install Inno Setup 6.3+ from https://jrsoftware.org/isdl.php or pass --iscc "C:\\path\\ISCC.exe"')
        output = args.output.resolve()
        payload = prepare(output, commit)
        print(f'[INSTALLER] Pinned source: {commit}\n[INSTALLER] Payload: {payload}')
        if args.prepare_only:
            return 0
        destination = output / 'dist'
        destination.mkdir(exist_ok=True)
        subprocess.run([str(iscc), '/DPayloadDir=' + str(payload), '/DOutputDir=' + str(destination),
                        '/DAppVersion=1.0-' + commit[:8], str(payload / 'AI-Car-Scanner.iss')], check=True)
        artifact = destination / 'AI-Car-Scanner-Setup.exe'
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise ValueError('Compiler returned without a Setup executable')
        with artifact.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        artifact.with_suffix('.exe.sha256').write_text(digest + '  ' + artifact.name + '\n', encoding='utf-8')
        print(f'[READY] {artifact}\n[SHA256] {digest}')
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('[INSTALLER ERROR] ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
