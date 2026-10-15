"""Release-time locked ICP dependencies. End-user installation is offline."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, stat, subprocess

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def environment():
    env = dict(os.environ)
    for name in ('NODE_PATH', 'NODE_OPTIONS'):
        env.pop(name, None)
    return env

def command(args, cwd, timeout=60):
    result = subprocess.run(args, cwd=cwd, env=environment(), capture_output=True,
                            text=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

def verify(root=ROOT):
    services = root / 'client/services'
    lock = json.loads((services / 'package-lock.json').read_text(encoding='utf-8'))
    package = json.loads((services / 'package.json').read_text(encoding='utf-8'))
    if lock['lockfileVersion'] != 3 or package['dependencies'] != lock['packages']['']['dependencies']:
        raise RuntimeError('Package/lock mismatch')
    modules = services / 'node_modules'
    if not modules.is_dir():
        raise RuntimeError('Missing bundled Node runtime. Run scripts/prepare_node_runtime.py --prepare at release time.')
    versions = {}
    for relative, entry in lock['packages'].items():
        if not relative or entry.get('dev'):
            continue
        if not relative.startswith('node_modules/') or '..' in Path(relative).parts or not entry.get('integrity'):
            raise RuntimeError('Unsupported lock entry: ' + relative)
        installed = json.loads((services / relative / 'package.json').read_text(encoding='utf-8'))
        if installed['version'] != entry['version']:
            raise RuntimeError('Dependency version mismatch: ' + relative)
        versions[relative] = installed['version']
    for path in [modules, *modules.rglob('*')]:
        if path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT if os.name == 'nt' else path.is_symlink():
            raise RuntimeError('Linked dependency path: ' + str(path))
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    node = shutil.which('node')
    if not npm or not node:
        raise RuntimeError('Node.js and npm required for release verification')
    tree = json.loads(command([npm, 'ls', '--prefix', str(services), '--all', '--omit=dev', '--json'], services))
    if tree.get('problems'):
        raise RuntimeError('Incomplete dependency tree')
    code = """const {createRequire}=require('node:module');
const path=require('node:path');
const r=createRequire(path.join(process.cwd(),'connection_probe.mjs'));
const specs=['@icp-sdk/core/agent','@icp-sdk/core/principal','@icp-sdk/core/identity','@icp-sdk/core/candid'];
const found={};for(const s of specs){const p=r.resolve(s);const rel=path.relative(path.join(process.cwd(),'node_modules'),p);if(rel.startsWith('..')||path.isAbsolute(rel))throw Error('External dependency: '+p);r(s);found[s]=rel;}console.log(JSON.stringify(found));"""
    resolved = json.loads(command([node, '-e', code], services))
    return {'status': 'PASS', 'lockSha256': digest(services / 'package-lock.json'),
            'versions': versions, 'resolvedLocally': resolved, 'nodePathUsed': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Release builder only: npm ci from existing lock')
    parser.add_argument('--cache', type=Path, help='Optional release-time npm cache outside the candidate')
    args = parser.parse_args()
    if args.prepare:
        services = ROOT / 'client/services'
        if (services / 'node_modules').exists():
            raise SystemExit('Existing node_modules preserved; use a fresh isolated release copy')
        original = {name: (services / name).read_bytes() for name in ('package.json', 'package-lock.json')}
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        if not npm:
            raise SystemExit('npm is required for release preparation')
        cmd = [npm, 'ci', '--prefix', str(services), '--omit=dev', '--ignore-scripts', '--no-bin-links', '--no-audit', '--no-fund']
        if args.cache:
            cmd += ['--cache', str(args.cache.resolve())]
        print(command(cmd, services, timeout=180), flush=True)
        if any((services / name).read_bytes() != data for name, data in original.items()):
            raise RuntimeError('Package/lock changed; release refused')
    print(json.dumps(verify(), indent=2))
