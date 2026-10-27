"""Local setup/launch runner. No administrator access, global installs or CI/CD.

Windows x64 setup installs missing Python dependencies, JDK/Android tooling,
llama.cpp CPU runtime and Qwen3 GGUF weights. Existing tools/files are reused.
Downloads may total several GB. Interrupted downloads can resume on rerun.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import venv
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'finalbuild'
TOOLS = ROOT / '.build-tools/setup'
STATE = ROOT / '.runner-state.json'
MODEL_NAME = 'Qwen3-8B-Q4_K_M.gguf'
MODEL_REPO = 'Qwen/Qwen3-8B-GGUF'
PACKAGE = 'com.aicarscaner.mobile'
USER_AGENT = 'AI-Car-Scanner-local-setup/1'
# Use the Java-based SDK tools compatible with JDK 17; latest may require a newer runtime.
CMDLINE_PACKAGE = 'cmdline-tools;19.0'
SDK_PACKAGES = ('platform-tools', 'platforms;android-36', 'build-tools;35.0.0')

# The existing builder owns process-tree cancellation, live logs and tool discovery.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from finalbuild.scripts.build_all import Runner, BuildError, android_sdk, java_executable  # noqa: E402
from finalbuild.shared.environment import environment_values  # noqa: E402


class SetupError(RuntimeError):
    pass


def api_url(value: str) -> str:
    value = value.strip()
    if any(char.isspace() for char in value): raise argparse.ArgumentTypeError('API URL cannot contain whitespace')
    try:
        parsed = urllib.parse.urlsplit(value)
        if parsed.port == 0: raise ValueError('Port zero')
    except ValueError as error:
        raise argparse.ArgumentTypeError('Invalid API port') from error
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise argparse.ArgumentTypeError('Use an HTTP(S) API URL without credentials, query or fragment')
    return value.rstrip('/') + '/'


def fetch_json(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': USER_AGENT}), timeout=45) as response:
            return json.load(response)
    except (OSError, ValueError, http.client.HTTPException) as error:
        raise SetupError(f'Cannot read official download metadata: {url}\n{error}\nRetry, or supply existing tool/model paths to setup.') from error


def checksum(path: Path, algorithm='sha256') -> str:
    digest = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path, expected: str | None = None, algorithm='sha256', size: int | None = None) -> Path:
    if urllib.parse.urlsplit(url).scheme != 'https': raise SetupError('Downloads require HTTPS')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        if (size is None or target.stat().st_size == size) and (expected is None or checksum(target, algorithm) == expected.lower()):
            return target
        raise SetupError(f'Existing file does not match the official artifact; it was kept: {target}')
    partial = target.with_name(target.name + '.part')
    if target.is_symlink() or partial.is_symlink(): raise SetupError('Linked download targets are not overwritten')
    offset = partial.stat().st_size if partial.is_file() else 0
    if offset and expected and (size is None or size == offset) and checksum(partial, algorithm) == expected.lower():
        partial.replace(target); return target
    if offset and size is not None and offset >= size:
        partial.unlink();offset = 0
    headers = {'User-Agent': USER_AGENT}
    if offset: headers['Range'] = f'bytes={offset}-'
    print(f'[DOWNLOAD] {target.name} ({"resuming at " + str(offset) if offset else "starting"}; may be large)', flush=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
            if urllib.parse.urlsplit(response.geturl()).scheme != 'https': raise SetupError('Insecure download redirect rejected')
            resumed = offset > 0 and response.status == 206
            if resumed and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                raise SetupError('Server returned an inconsistent resume range')
            count = offset if resumed else 0
            announced = count
            with partial.open('ab' if resumed else 'wb') as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk: break
                    output.write(chunk); count += len(chunk)
                    if count - announced >= 64 * 1024 * 1024:
                        print(f'[DOWNLOAD] {target.name}: {count / (1024**2):.0f} MiB', flush=True); announced = count
        if size is not None and partial.stat().st_size != size: raise SetupError(f'Incomplete download: {target.name}; rerun to resume')
        if expected and checksum(partial, algorithm) != expected.lower():
            partial.unlink()
            raise SetupError(f'Checksum mismatch: {target.name}. Rejected download; rerun setup.')
        partial.replace(target)
        return target
    except (OSError, urllib.error.URLError, http.client.HTTPException) as error:
        raise SetupError(f'Download interrupted: {url}\nPartial file kept for resume: {partial}\n{error}') from error


def extract_zip(archive: Path, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for item in source.infolist():
            name = PurePosixPath(item.filename.replace('\\', '/'))
            if name.is_absolute() or '..' in name.parts or any(':' in part for part in name.parts) or stat.S_ISLNK(item.external_attr >> 16):
                raise SetupError(f'Unsafe archive entry: {item.filename}')
            destination = directory.joinpath(*name.parts)
            if not destination.resolve().is_relative_to(directory.resolve()): raise SetupError('Archive path escapes installation directory')
        source.extractall(directory)


def venv_python() -> Path:
    return ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def load_state() -> dict:
    if not STATE.is_file(): return {}
    try:
        state = json.loads(STATE.read_text(encoding='utf-8'))
        if not isinstance(state, dict): raise ValueError('Expected a JSON object')
        return state
    except (ValueError, OSError) as error: raise SetupError(f'Invalid runner state: {STATE}: {error}') from error


def save_state(state):
    temporary = STATE.with_suffix('.tmp')
    if STATE.is_symlink() or temporary.is_symlink(): raise SetupError('Linked runner state files are not overwritten')
    temporary.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    temporary.replace(STATE)


def child_env(state):
    # Process ENV > local/explicit JSON > saved runner settings > shipped JSON.
    env = environment_values()
    env.update(PYTHONUNBUFFERED='1', AI_CAR_BACKEND_HOST='0.0.0.0',
               AI_CAR_BACKEND_PORT=str(state.get('port', env.get('AI_CAR_BACKEND_PORT', 8001))),
               LOCAL_LLM_SERVER_HOST='127.0.0.1',
               LOCAL_LLM_SERVER_PORT=str(state.get('ai_port', env.get('LOCAL_LLM_SERVER_PORT', 8000))))
    for key, field in [('JAVA_HOME', 'java_home'), ('ANDROID_HOME', 'sdk'), ('ANDROID_SDK_ROOT', 'sdk'),
                       ('LOCAL_LLM_MODEL_PATH', 'model'), ('LOCAL_LLM_SERVER_PATH', 'llama')]:
        if state.get(field): env[key] = str(state[field])
    env.update(environment_values(include_defaults=False))
    env.update(os.environ)
    env.setdefault('LOCAL_LLM_SERVER_URL', f'http://{env["LOCAL_LLM_SERVER_HOST"]}:{env["LOCAL_LLM_SERVER_PORT"]}')
    if env.get('JAVA_HOME'): env['PATH'] = str(Path(env['JAVA_HOME']) / 'bin') + os.pathsep + env.get('PATH', '')
    env.setdefault('GRADLE_USER_HOME', str(ROOT / '.build-tools/gradle'))
    return env


def require_python() -> None:
    if sys.version_info < (3, 12) or sys.maxsize <= 2**32:
        raise SetupError('Use 64-bit Python 3.12+ (Windows Python 3.14 recommended)')


def setup_python(runner, with_tests=False):
    python = venv_python()
    if not (ROOT / '.venv').resolve().is_relative_to(ROOT.resolve()): raise SetupError('External linked .venv is not modified; use a local project environment')
    if not python.is_file():
        if (ROOT / '.venv').exists(): raise SetupError('The existing .venv is incomplete. Move it aside before rerunning setup.')
        print('[SETUP] Creating isolated .venv', flush=True)
        try:
            venv.EnvBuilder(with_pip=True).create(ROOT / '.venv')
        except SystemExit as error:
            raise SetupError('Python venv/ensurepip support is missing. Install that Python component, move aside the incomplete .venv and retry.') from error
    runner.run([str(python), '-c', 'import sys; sys.exit(0 if sys.version_info >= (3,12) and sys.maxsize > 2**32 else "Move aside the old venv and rerun with 64-bit Python 3.12+")'], cwd=PROJECT)
    runner.run([str(python), '-m', 'pip', 'install', '--upgrade', 'pip'], cwd=PROJECT)
    requirements = ['-r', 'requirements.txt']
    if with_tests: requirements += ['-r', 'backend/requirements-dev.txt', '-r', 'apps/desktop/requirements-dev.txt']
    runner.run([str(python), '-m', 'pip', 'install', *requirements], cwd=PROJECT)
    runner.run([str(python), '-m', 'pip', 'check'], cwd=PROJECT)
    runner.run([str(python), '-c', 'from PySide6 import QtCore; import fastapi, reportlab, sqlalchemy, PIL; print("Desktop/backend imports OK")'], cwd=PROJECT)
    return str(python)


def existing_java(path=None):
    executable = str(Path(path) / 'bin' / ('java.exe' if os.name == 'nt' else 'java')) if path else java_executable()
    if not executable: return None
    try:
        result = subprocess.run([executable, '-XshowSettings:properties', '-version'], capture_output=True, text=True, timeout=20)
        text = result.stdout + result.stderr
        version = re.search(r'version\s+"(\d+)', text)
        home = re.search(r'^\s*java.home\s*=\s*(.+)$', text, re.MULTILINE)
        if result.returncode == 0 and version and 17 <= int(version[1]) <= 23 and home:
            location = Path(home[1].strip())
            if (location / 'bin' / ('javac.exe' if os.name == 'nt' else 'javac')).is_file(): return location
    except (OSError, subprocess.SubprocessError): pass
    return None


def ensure_java(explicit=None):
    managed = TOOLS / 'jdk'
    found = existing_java(explicit) if explicit else existing_java(managed) or existing_java()
    if not found and not explicit and os.environ.get('ProgramFiles'):
        found = existing_java(Path(os.environ['ProgramFiles']) / 'Android/Android Studio/jbr')
    if found: return found
    if explicit: raise SetupError(f'Configured JAVA_HOME is not a working JDK 17–23: {explicit}')
    if platform.system() != 'Windows' or platform.machine().lower() not in {'amd64', 'x86_64'}:
        raise SetupError('Install a JDK 17 locally and rerun with --java-home PATH; automatic JDK install supports Windows x64')
    entries = fetch_json('https://api.adoptium.net/v3/assets/latest/17/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse')
    package = entries[0]['binary']['package']
    archive = download(package['link'], TOOLS / 'downloads' / Path(package['name']).name, package['checksum'], size=package.get('size'))
    with tempfile.TemporaryDirectory(dir=TOOLS, prefix='jdk-extract-') as temp:
        extract_zip(archive, Path(temp))
        homes = [path.parent.parent for path in Path(temp).rglob('bin/java.exe')]
        if len(homes) != 1: raise SetupError('Official JDK archive has an unexpected layout')
        if managed.exists(): raise SetupError(f'Incomplete managed JDK kept at {managed}; move it aside to reinstall')
        shutil.copytree(homes[0], managed)
    if not existing_java(managed): raise SetupError('Installed JDK did not pass its version/compiler check')
    return managed


def sdk_tools_metadata(raw: bytes, host: str):
    try: root = ET.fromstring(raw)
    except ET.ParseError as error: raise SetupError('Invalid official Android repository XML') from error
    package = next((p for p in root.iter('remotePackage') if p.attrib.get('path') == CMDLINE_PACKAGE), None)
    if package is None: raise SetupError(f'Official Android manifest lacks {CMDLINE_PACKAGE}')
    archive = next((a for a in package.findall('archives/archive') if a.findtext('host-os') == host), None)
    if archive is None: raise SetupError(f'No official command-line tools archive for {host}')
    url = urllib.parse.urljoin('https://dl.google.com/android/repository/', archive.findtext('complete/url'))
    digest = archive.findtext('complete/checksum')
    if not digest or not re.fullmatch('[0-9a-fA-F]{40}', digest): raise SetupError('Android tools manifest has no valid SHA-1 checksum')
    return url, digest, int(archive.findtext('complete/size') or 0) or None


def ensure_sdk(explicit, java_home, accept_licenses, runner):
    sdk = Path(explicit).expanduser().resolve() if explicit else android_sdk() or TOOLS / 'android-sdk'
    sdk.mkdir(parents=True, exist_ok=True)
    needed = not all(path.is_file() for path in (sdk / 'platforms/android-36/android.jar', sdk / 'build-tools/35.0.0/source.properties', sdk / 'platform-tools' / ('adb.exe' if os.name == 'nt' else 'adb')))
    if not needed: return sdk
    tools = sdk / 'cmdline-tools/19.0'
    jar = tools / 'lib/sdkmanager-classpath.jar'
    if not jar.is_file():
        request = urllib.request.Request('https://dl.google.com/android/repository/repository2-1.xml', headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response: raw = response.read()
        host = {'Windows': 'windows', 'Darwin': 'macosx', 'Linux': 'linux'}[platform.system()]
        url, digest, size = sdk_tools_metadata(raw, host)
        archive = download(url, TOOLS / f'downloads/android-tools-{host}-19.zip', digest, 'sha1', size=size)
        with tempfile.TemporaryDirectory(dir=TOOLS, prefix='sdk-extract-') as temp:
            extract_zip(archive, Path(temp))
            source = Path(temp) / 'cmdline-tools'
            if not (source / 'lib/sdkmanager-classpath.jar').is_file(): raise SetupError('Unexpected Android tools archive layout')
            if tools.exists(): raise SetupError(f'Incomplete command-line tools kept at {tools}; move them aside to reinstall')
            shutil.copytree(source, tools)
    env = child_env({'sdk': str(sdk), 'java_home': str(java_home)})
    java = java_home / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
    command = [str(java), '-cp', str(jar), 'com.android.sdklib.tool.sdkmanager.SdkManagerCli', f'--sdk_root={sdk}']
    print('[SETUP] Android SDK licenses: review in this terminal, or use --accept-android-licenses for noninteractive acceptance.', flush=True)
    runner.run(command + ['--licenses'], env=env, input_text='y\n' * 100 if accept_licenses else None)
    runner.run(command + list(SDK_PACKAGES), env=env, input_text='y\n' * 100 if accept_licenses else None)
    for path in (sdk / 'platforms/android-36/android.jar', sdk / 'build-tools/35.0.0/source.properties', sdk / 'platform-tools' / ('adb.exe' if os.name == 'nt' else 'adb')):
        if not path.is_file(): raise SetupError(f'SDK installation incomplete: {path}')
    return sdk


def gguf(path: Path) -> bool:
    try:
        with path.open('rb') as stream: return stream.read(4) == b'GGUF'
    except OSError: return False


def ensure_model(explicit=None):
    path = Path(explicit).expanduser().resolve() if explicit else PROJECT / 'models' / MODEL_NAME
    if path.exists():
        if not gguf(path): raise SetupError(f'Existing model is not GGUF; kept unchanged: {path}')
        return path
    if explicit: raise SetupError(f'Model does not exist: {path}')
    metadata = fetch_json(f'https://huggingface.co/api/models/{MODEL_REPO}?blobs=true')
    item = next((item for item in metadata.get('siblings', []) if item.get('rfilename') == MODEL_NAME), None)
    if item is None: raise SetupError('Official model repository does not expose the expected single-file GGUF; use --model PATH')
    digest = (item.get('lfs') or {}).get('sha256')
    revision = metadata.get('sha', '')
    if not digest or not re.fullmatch('[0-9a-fA-F]{64}', digest) or not re.fullmatch('[0-9a-fA-F]{40,64}', revision):
        raise SetupError('Model metadata lacks a verifiable revision/SHA-256; use an existing --model PATH')
    download(f'https://huggingface.co/{MODEL_REPO}/resolve/{revision}/{MODEL_NAME}', path, digest, size=item.get('size'))
    if not gguf(path): raise SetupError('Downloaded file is not a GGUF model')
    return path


def ensure_llama(explicit=None):
    executable = 'llama-server.exe' if os.name == 'nt' else 'llama-server'
    choices = [Path(explicit) / executable] if explicit else [PROJECT / 'tools/llama.cpp' / executable, PROJECT / executable, PROJECT / 'bin' / executable, TOOLS / 'llama.cpp' / executable]
    if not explicit and (TOOLS / 'llama.cpp').is_dir(): choices += sorted((TOOLS / 'llama.cpp').rglob(executable))
    system = shutil.which(executable)
    if not explicit and system: choices.append(Path(system))
    for path in choices:
        if path.is_file():
            subprocess.run([str(path), '--version'], check=True, timeout=30)
            return path.resolve()
    if explicit: raise SetupError(f'llama-server not found in {explicit}; keep the companion DLLs with the executable')
    if platform.system() != 'Windows' or platform.machine().lower() not in {'amd64', 'x86_64'}:
        raise SetupError('Install llama.cpp locally and use --llama-dir PATH; automatic runtime download supports Windows x64')
    release = fetch_json('https://api.github.com/repos/ggml-org/llama.cpp/releases/latest')
    asset = next((a for a in release.get('assets', []) if re.search(r'-bin-win-cpu-x64\.zip$', a['name'])), None)
    if asset is None: raise SetupError('Official llama.cpp release has no Windows CPU x64 archive; use --llama-dir PATH')
    expected = asset.get('digest') or ''
    digest = expected.removeprefix('sha256:') if expected.startswith('sha256:') else None
    archive = download(asset['browser_download_url'], TOOLS / 'downloads' / asset['name'], digest, size=asset.get('size'))
    target = TOOLS / 'llama.cpp'
    if target.exists(): raise SetupError(f'Incomplete runtime kept at {target}; move it aside before reinstalling')
    with tempfile.TemporaryDirectory(dir=TOOLS, prefix='llama-extract-') as temp:
        extract_zip(archive, Path(temp))
        servers = list(Path(temp).rglob('llama-server.exe'))
        if len(servers) != 1: raise SetupError('Unexpected llama.cpp archive layout')
        # Keep the complete release directory, including sibling DLLs.
        relative = servers[0].relative_to(Path(temp))
        shutil.copytree(Path(temp), target)
    server = target / relative
    subprocess.run([str(server), '--version'], check=True, timeout=30)
    return server


def java_path(state):
    return Path(state['java_home']) / 'bin' / ('java.exe' if os.name == 'nt' else 'java')


def build_android(state, runner, tests=False):
    project = PROJECT / 'apps/mobile-android'
    wrapper = project / 'gradle/wrapper/gradle-wrapper.jar'
    tasks = [':app:assembleDebug'] + ([':app:testDebugUnitTest', ':app:lintDebug'] if tests else [])
    # Direct Java avoids shell/.bat quoting and command-injection differences on Windows.
    runner.run([str(java_path(state)), '-cp', str(wrapper), 'org.gradle.wrapper.GradleWrapperMain', *tasks,
                f'-PapiBaseUrl={state["api_url"]}', '--no-daemon', '--console=plain'], cwd=project, env=child_env(state))
    apk = project / 'app/build/outputs/apk/debug/app-debug.apk'
    if not apk.is_file() or not apk.stat().st_size: raise SetupError('Gradle returned without the expected debug APK')
    return apk


@contextmanager
def setup_lock():
    TOOLS.mkdir(parents=True, exist_ok=True)
    lock = TOOLS / 'setup.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise SetupError(f'Setup lock exists: {lock}. Another setup may be running. If it stopped, remove only that lock and retry.') from error
    try:
        with os.fdopen(descriptor, 'w') as stream: stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def setup(args):
    with setup_lock():
        result = perform_setup(args)
    if args.run: return desktop(argparse.Namespace(no_ai=args.skip_ai))
    return result


def perform_setup(args):
    require_python()
    TOOLS.mkdir(parents=True, exist_ok=True)
    log = TOOLS / 'logs' / ('setup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.log')
    runner = Runner(log)
    state = {'port': args.port, 'ai_port': getattr(args, 'ai_port', 8000), 'api_url': args.api_url or f'http://10.0.2.2:{args.port}/', 'ai_enabled': not args.skip_ai, 'android_enabled': not args.skip_android}
    state['python'] = setup_python(runner, args.with_tests)
    if not args.skip_ai:
        state['llama'] = str(ensure_llama(args.llama_dir))
        state['model'] = str(ensure_model(args.model))
    if not args.skip_android:
        state['java_home'] = str(ensure_java(args.java_home))
        state['sdk'] = str(ensure_sdk(args.android_sdk, Path(state['java_home']), args.accept_android_licenses, runner))
        if not args.skip_android_build: state['apk'] = str(build_android(state, runner, args.with_tests))
    if args.with_tests:
        test_env = child_env(state)
        test_env.pop('DATABASE_URL', None)
        test_env['QT_QPA_PLATFORM'] = 'offscreen'
        runner.run([state['python'], '-m', 'pytest', 'tests', '-q'], cwd=PROJECT, env=test_env)
        runner.run([state['python'], 'scripts/run_desktop_tests.py', '--min-core-coverage', '90'], cwd=PROJECT, env=test_env)
    state['configured_at'] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print(f'[READY] Selected setup components completed. State: {STATE}\n[LOG] {log}', flush=True)
    print('Next: python runner.py desktop  |  python runner.py android', flush=True)
    return 0


def health(url):
    try:
        with urllib.request.urlopen(url.rstrip('/') + '/health', timeout=5) as response:
            value = json.load(response)
            return isinstance(value, dict) and value.get('status') == 'ok'
    except (OSError, ValueError, http.client.HTTPException): return False


def desktop(args):
    state = load_state()
    python = venv_python()
    if not python.is_file(): raise SetupError('Run python runner.py setup first')
    env = child_env(state)
    command = [str(python), '-m', 'apps.desktop.main', '--with-backend']
    if not args.no_ai and state.get('ai_enabled', True):
        if not gguf(Path(env.get('LOCAL_LLM_MODEL_PATH', ''))) or not Path(env.get('LOCAL_LLM_SERVER_PATH', '')).is_file():
            raise SetupError('Local AI is not configured. Run setup or use desktop --no-ai.')
        command.append('--local-ai')
    else: env['AI_CAR_DISABLE_LLM_AUTOSTART'] = '1'
    print(f'[RUN] Desktop + Backend at http://127.0.0.1:{env["AI_CAR_BACKEND_PORT"]}; keep this terminal open.', flush=True)
    return subprocess.call(command, cwd=PROJECT, env=env)


def adb_command(state, *args, serial=None, **kwargs):
    adb = Path(state['sdk']) / 'platform-tools' / ('adb.exe' if os.name == 'nt' else 'adb')
    return subprocess.run([str(adb), *(['-s', serial] if serial else []), *args], check=True, **kwargs)


def choose_device(state, requested=None):
    result = adb_command(state, 'devices', capture_output=True, text=True)
    entries = [line.split() for line in result.stdout.splitlines()[1:] if line.strip()]
    online = [parts[0] for parts in entries if len(parts) >= 2 and parts[1] == 'device']
    if requested:
        if requested not in online: raise SetupError(f'ADB device is not ready: {requested}')
        return requested
    if len(online) != 1: raise SetupError('Start one emulator in Android Studio, or specify --serial. ADB list:\n' + result.stdout)
    return online[0]


def android(args):
    state = load_state()
    if not state.get('sdk') or not state.get('java_home'): raise SetupError('Run setup with Android enabled first')
    env = child_env(state)
    port = env['AI_CAR_BACKEND_PORT']
    requested = args.api_url or env.get('AI_CAR_ANDROID_API_URL')
    if requested:
        state['api_url'] = api_url(requested)
    elif args.reverse:
        state['api_url'] = f'http://127.0.0.1:{port}/'
    elif urllib.parse.urlsplit(state['api_url']).hostname == '10.0.2.2':
        state['api_url'] = f'http://10.0.2.2:{port}/'
    if not args.build_only:
        target = urllib.parse.urlsplit(state['api_url'])
        check = urllib.parse.urlunsplit(target._replace(netloc='127.0.0.1' + (f':{target.port}' if target.port else ''))) if target.hostname == '10.0.2.2' else state['api_url']
        if not health(check): raise SetupError(f'Backend is not healthy at {check}. Start python runner.py desktop in another terminal first.')
        serial = choose_device(state, args.serial)
    log = TOOLS / 'logs' / ('android-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.log')
    apk = build_android(state, Runner(log), args.with_tests)
    if args.build_only: print(f'[APK] {apk}'); return 0
    adb_command(state, 'install', '-r', str(apk), serial=serial)
    if args.reverse: adb_command(state, 'reverse', f'tcp:{port}', f'tcp:{port}', serial=serial)
    adb_command(state, 'shell', 'am', 'force-stop', PACKAGE, serial=serial)
    # Debug run-as changes only the backend URL; retain drafts and other app settings.
    root = ET.Element('map'); ET.SubElement(root, 'string', name='url').text = state['api_url'].rstrip('/')
    xml = ET.tostring(root, encoding='unicode')
    adb_command(state, 'shell', '-T', 'run-as', PACKAGE, 'sh', '-c', "'mkdir -p shared_prefs && cat > shared_prefs/backend.xml'", serial=serial, input=xml, text=True)
    adb_command(state, 'shell', 'am', 'start', '-n', PACKAGE + '/.MainActivity', serial=serial)
    print(f'[RUN] Android on {serial}; backend={state["api_url"]}. Log: {log}')
    return 0


def check(args):
    state = load_state()
    env = child_env(state)
    problems = []
    if not state: problems.append('Runner is not configured: run python runner.py setup')
    python = venv_python()
    if not python.is_file(): problems.append('Python venv missing: run setup')
    else:
        result = subprocess.run([str(python), '-c', 'from PySide6 import QtCore; import fastapi, reportlab, sqlalchemy'], cwd=PROJECT, capture_output=True, text=True)
        if result.returncode: problems.append('Python dependencies incomplete: ' + result.stderr[-1000:])
    if state.get('ai_enabled', True):
        if not gguf(Path(env.get('LOCAL_LLM_MODEL_PATH') or PROJECT / 'models' / MODEL_NAME)): problems.append('GGUF model missing/invalid')
        if not env.get('LOCAL_LLM_SERVER_PATH') or not Path(env['LOCAL_LLM_SERVER_PATH']).is_file(): problems.append('llama-server not configured')
    if state.get('android_enabled', True):
        if not existing_java(state.get('java_home')): problems.append('Working JDK 17–23 not configured')
        sdk = Path(state.get('sdk') or TOOLS / 'android-sdk')
        if not (sdk / 'platforms/android-36/android.jar').is_file(): problems.append('Android SDK 36 not configured')
        if not (sdk / 'build-tools/35.0.0/source.properties').is_file(): problems.append('Android build-tools 35.0.0 missing')
        if not (sdk / 'platform-tools' / ('adb.exe' if os.name == 'nt' else 'adb')).is_file(): problems.append('Android platform-tools / ADB missing')
    if args.services:
        if not health(env.get('AI_CAR_BACKEND_URL', f'http://127.0.0.1:{env["AI_CAR_BACKEND_PORT"]}')): problems.append('Backend is stopped: run python runner.py desktop')
        if state.get('ai_enabled', True) and not health(env['LOCAL_LLM_SERVER_URL']): problems.append('Local AI server is not healthy')
    for message in problems: print('[NEEDS SETUP] ' + message)
    if not problems: print('[READY] Configured components' + (' and services' if args.services else '') + ' checked')
    return 2 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog='runner.py', description=__doc__)
    commands = parser.add_subparsers(dest='command')
    configure = commands.add_parser('setup', help='Install/reuse local environment, AI and Android tools')
    configure.add_argument('--skip-ai', action='store_true')
    configure.add_argument('--skip-android', action='store_true')
    configure.add_argument('--model', type=Path, help='Existing GGUF path; otherwise download the verified default model if missing')
    configure.add_argument('--llama-dir', type=Path, help='Existing llama.cpp directory including DLLs')
    configure.add_argument('--java-home', type=Path)
    configure.add_argument('--android-sdk', type=Path)
    configure.add_argument('--accept-android-licenses', action='store_true', help='Accept Android SDK licenses noninteractively')
    configure.add_argument('--skip-android-build', action='store_true', help='Prepare tools without compiling the APK')
    configure.add_argument('--with-tests', action='store_true', help='Install and run Python/Desktop tests, plus Android JVM/lint when building Android')
    configure.add_argument('--run', action='store_true', help='Open Desktop/backend after setup')
    configure.add_argument('--port', type=int, default=int(os.environ.get('AI_CAR_BACKEND_PORT', environment_values().get('AI_CAR_BACKEND_PORT', 8001))))
    configure.add_argument('--ai-port', type=int, default=int(os.environ.get('LOCAL_LLM_SERVER_PORT', environment_values().get('LOCAL_LLM_SERVER_PORT', 8000))))
    configure.add_argument('--api-url', type=api_url)
    launch = commands.add_parser('desktop', help='Run Desktop + Backend + local AI using the project venv')
    launch.add_argument('--no-ai', action='store_true')
    phone = commands.add_parser('android', help='Build, install, configure and launch on one connected emulator/device')
    phone.add_argument('--build-only', action='store_true')
    phone.add_argument('--serial')
    routing = phone.add_mutually_exclusive_group()
    routing.add_argument('--api-url', type=api_url)
    routing.add_argument('--reverse', action='store_true', help='Use ADB reverse instead of emulator host routing')
    phone.add_argument('--with-tests', action='store_true')
    verify = commands.add_parser('check', help='Read-only setup validation; no downloads')
    verify.add_argument('--services', action='store_true', help='Also require running Backend and AI health endpoints')
    values = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(values or ['setup'])
    if args.command == 'setup':
        if not 1 <= args.port <= 65535 or not 1 <= args.ai_port <= 65535: parser.error('Ports must be 1..65535')
        if not args.skip_ai and args.port == args.ai_port: parser.error('Backend and local AI must use different ports')
    if args.command is None: parser.print_help(); return 0
    try: return {'setup': setup, 'desktop': desktop, 'android': android, 'check': check}[args.command](args)
    except KeyboardInterrupt: print('\nRunner cancelled; completed installs/downloads were retained.', file=sys.stderr); return 130
    except (SetupError, BuildError, OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as error:
        print(f'[FAILED] {error}', file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
