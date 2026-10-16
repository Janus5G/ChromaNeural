"""REA-only Linux cgroup v2 containment. No fallback to unrestricted execution.

The SDK still owns MCP. This helper only supervises bounded byte pipes and a
transient systemd user service. The entire REA tree enters its cgroup BEFORE
Node starts. Settings are fixed profile constants, never config/env overrides.
"""
import asyncio
import contextlib
from dataclasses import dataclass
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import uuid


@dataclass(frozen=True)
class Limits:
    memory: int = 1536 * 1024 * 1024
    cpu_percent: int = 100
    tasks: int = 64
    wall_seconds: int = 30


LIMITS = Limits()
FRAME_BYTES = 4 * 1024 * 1024
SESSION_BYTES = 8 * 1024 * 1024
STDERR_BYTES = 128 * 1024
INPUT_BYTES = 64 * 1024


def available():
    if sys.platform != "linux":
        return False
    try:
        controllers = Path('/sys/fs/cgroup/cgroup.controllers').read_text().split()
        return (set(('cpu', 'memory', 'pids')) <= set(controllers) and
                Path('/usr/bin/systemd-run').is_file() and Path('/usr/bin/systemctl').is_file() and
                Path(f'/run/user/{os.getuid()}/bus').exists())
    except OSError:
        return False


def control_environment():
    return {'PATH': '/usr/bin:/bin', 'XDG_RUNTIME_DIR': f'/run/user/{os.getuid()}',
            'DBUS_SESSION_BUS_ADDRESS': f'unix:path=/run/user/{os.getuid()}/bus',
            'LANG': 'C.UTF-8'}


def service_command(unit, directory, command, limits=LIMITS):
    if not available() or not unit.startswith('chromaneural-rea-') or not unit.endswith('.service'):
        raise RuntimeError('REA secure resource isolation unavailable')
    properties = (
        f'MemoryMax={limits.memory}', 'MemorySwapMax=0', f'CPUQuota={limits.cpu_percent}%',
        f'TasksMax={limits.tasks}', f'RuntimeMaxSec={limits.wall_seconds}',
        'KillMode=control-group', 'TimeoutStopSec=2s', 'SendSIGKILL=yes', 'OOMPolicy=kill',
        'MemoryAccounting=yes', 'CPUAccounting=yes', 'TasksAccounting=yes', 'Delegate=no',
        'NoNewPrivileges=yes', 'PrivateUsers=yes', 'PrivateNetwork=yes',
        'ProtectControlGroups=yes', 'ProtectSystem=strict', 'ProtectHome=read-only',
        'RestrictNamespaces=yes', 'RestrictAddressFamilies=AF_UNIX',
        f'InaccessiblePaths=/run/user/{os.getuid()}', f'ReadWritePaths={directory}',
        f'WorkingDirectory={directory}', 'UMask=0077')
    result = ['/usr/bin/systemd-run', '--user', '--quiet', '--wait', '--pipe', '--collect', '--unit='+unit]
    for prop in properties:
        result += ['--property', prop]
    return result + ['--'] + list(command)


def verify_cgroup(limits=LIMITS):
    rows = Path('/proc/self/cgroup').read_text().splitlines()
    path = next((r[3:] for r in rows if r.startswith('0::/')), '')
    if not path or not Path(path).name.startswith('chromaneural-rea-'):
        raise RuntimeError('REA missing resource container')
    group = Path('/sys/fs/cgroup') / path.lstrip('/')
    memory = int((group/'memory.max').read_text())
    swap = int((group/'memory.swap.max').read_text())
    quota, period = map(int, (group/'cpu.max').read_text().split())
    tasks = int((group/'pids.max').read_text())
    if not (0 < memory <= limits.memory and swap == 0 and 0 < quota <= period * limits.cpu_percent / 100
            and 0 < tasks <= limits.tasks and (group/'memory.oom.group').read_text().strip() == '1'):
        raise RuntimeError('REA resource limits not enforced')
    return {'memory': memory, 'cpu_quota': quota, 'cpu_period': period, 'tasks': tasks}


def stop(unit):
    # Also runs if the pipe supervisor was killed. RuntimeMaxSec is the final
    # independent systemd deadline if the entire ChromaNeural worker disappears.
    try:
        subprocess.run(['/usr/bin/systemctl', '--user', 'stop', unit], env=control_environment(),
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('REA container cleanup unavailable') from None


@contextlib.contextmanager
def exclusive_slot():
    """One active REA worker budget per user; never wait."""
    import fcntl
    import stat
    path = f'/run/user/{os.getuid()}/chromaneural-rea.lock'
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode):
            raise RuntimeError('REA isolation lock unavailable')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('REA is already busy') from None
        yield
    finally:
        os.close(fd)


@contextlib.asynccontextmanager
async def transport(server):
    if not available():
        raise RuntimeError('REA secure resource isolation unavailable')
    from .mcp_rea import valid_launch
    if not valid_launch(server['command'], server['args']):
        raise ValueError('REA installed MCP target is invalid')
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client
    import anyio
    unit = 'chromaneural-rea-' + uuid.uuid4().hex + '.service'
    with exclusive_slot(), tempfile.TemporaryDirectory(prefix='chromaneural-rea-') as directory:
        try:
            with open(os.devnull, 'w') as errlog:
                params = StdioServerParameters(command=sys.executable,
                    args=['-I', '-B', str(Path(__file__).resolve()), 'relay', unit, directory,
                          server['command'], server['args'][0]], env=control_environment())
                async with stdio_client(params, errlog=errlog) as streams:
                    yield streams
        finally:
            with anyio.CancelScope(shield=True):
                await asyncio.to_thread(stop, unit)


def inside(directory, node, script):
    verify_cgroup()  # Must succeed before executing REA or any child.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from chroma.mcp_rea import valid_launch
    if not valid_launch(node, [script, 'mcp']):
        raise ValueError('REA target invalid')
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': directory,
           'TMPDIR': directory, 'XDG_CONFIG_HOME': directory, 'XDG_CACHE_HOME': directory,
           'LANG': 'C.UTF-8', 'REA_MCP_INPUT_SCHEMA_PROFILE': 'compact',
           'REA_MCP_OUTPUT_SCHEMA_PROFILE': 'off'}
    os.execve(node, [node, script, 'mcp'], env)


def relay(unit, directory, node, script):
    command = service_command(unit, directory, [sys.executable, '-I', '-B',
                str(Path(__file__).resolve()), 'inside', directory, node, script])
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=control_environment())
    start, output, errors, inputs = time.monotonic(), 0, 0, 0
    pending = bytearray()
    def terminated(*unused):
        raise RuntimeError('REA supervisor cancelled')
    signal.signal(signal.SIGTERM, terminated)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(sys.stdin.buffer, selectors.EVENT_READ, 'input')
            selector.register(process.stdout, selectors.EVENT_READ, 'output')
            selector.register(process.stderr, selectors.EVENT_READ, 'error')
            while process.poll() is None:
                if time.monotonic() - start > LIMITS.wall_seconds + 3:
                    raise TimeoutError('REA wall-clock deadline')
                for key, _ in selector.select(.1):
                    chunk = os.read(key.fileobj.fileno(), 16384)
                    if not chunk:
                        if key.data == 'input':
                            return
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == 'input':
                        inputs += len(chunk)
                        if inputs > INPUT_BYTES:
                            raise ValueError('REA input limit')
                        process.stdin.write(chunk); process.stdin.flush()
                    elif key.data == 'error':
                        errors += len(chunk)
                        if errors > STDERR_BYTES:
                            raise ValueError('REA diagnostic output limit')
                        # No target content or child diagnostic text reaches logs.
                    else:
                        output += len(chunk); pending.extend(chunk)
                        if output > SESSION_BYTES or len(pending) > FRAME_BYTES:
                            raise ValueError('REA transport output limit')
                        while b'\n' in pending:
                            line, _, rest = pending.partition(b'\n')
                            pending = bytearray(rest)
                            sys.stdout.buffer.write(line+b'\n'); sys.stdout.buffer.flush()
            if process.returncode:
                raise RuntimeError('REA contained process failed')
    finally:
        stop(unit)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=2)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


if __name__ == '__main__':
    try:
        if sys.argv[1] == 'inside' and len(sys.argv) == 5:
            inside(*sys.argv[2:])
        elif sys.argv[1] == 'relay' and len(sys.argv) == 6:
            relay(*sys.argv[2:])
        else:
            raise ValueError('REA helper arguments')
    except BaseException:
        sys.stderr.write('REA isolation or bounded operation failed\n')
        raise SystemExit(1)