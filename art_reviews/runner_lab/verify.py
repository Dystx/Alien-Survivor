#!/usr/bin/env python3
"""Verify the real runner review atlas in Godot. No synthetic texture fixtures.
Only this isolated viewer is tested. No gameplay or artwork approvals change.
"""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, sys, zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'assets/pack_v1/families/runner/review_runtime'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(command, marker=None):
    result = subprocess.run(command, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, LIBGL_ALWAYS_SOFTWARE='1'))
    text = result.stdout + result.stderr
    print('RUN ' + ' '.join(map(str, command)), flush=True)
    print(text, flush=True)
    if result.returncode or re.search(r'SCRIPT ERROR:|Parse Error:|^ERROR:', text, re.M) or (marker and marker not in text):
        raise RuntimeError('Runner review engine verification failed')
    return text

def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python verify.py /path/to/godot')
    engine = str(Path(sys.argv[1]).resolve())
    for name in ('atlas.png', 'animation_index.json', 'sprite_frames.tres'):
        if digest(HERE / 'assets/runner_review' / name) != digest(SOURCE / name):
            raise RuntimeError('Review differs from canonical runner runtime: ' + name)
    if not shutil.which('xvfb-run'):
        raise RuntimeError('xvfb-run is required for actual-art drawing/captures')
    logs = []
    logs.append(run([engine, '--headless', '--path', str(HERE), '--editor', '--import', '--quit']))
    logs.append(run([engine, '--headless', '--path', str(HERE), '--script', 'res://check_review.gd'],
                    'RUNNER_REVIEW_TESTS: 45 passed, 0 failed'))
    logs.append(run(['xvfb-run', '-a', engine, '--path', str(HERE), '--audio-driver', 'Dummy',
                     '--fixed-fps', '60', '--script', 'res://capture_review.gd'], 'RUNNER_CAPTURE_PASS'))
    for name in ('move', 'attack', 'death'):
        capture = HERE / 'captures' / (name + '.png')
        if not capture.is_file() or capture.stat().st_size < 1000:
            raise RuntimeError('Missing or empty actual engine capture: ' + name)
    evidence = HERE / 'verification'
    evidence.mkdir(exist_ok=True)
    (evidence / 'engine.log').write_text('\n'.join(logs), encoding='utf-8')
    files = [p for p in HERE.rglob('*') if p.is_file() and
             '.godot' not in p.parts and 'verification' not in p.parts and
             p.suffix not in ('.import', '.uid', '.pyc') and '__pycache__' not in p.parts]
    report = {'status': 'real_runner_engine_checks_passed', 'assertions': 45,
              'engine': '4.7.2', 'actual_textures': True, 'fixture_textures': False,
              'canonical_runner_runtime_matches': True,
              'source_revision': os.environ.get('GITHUB_SHA', 'local-unrecorded'),
              'files_sha256': {p.relative_to(HERE).as_posix(): digest(p) for p in sorted(files)},
              'not_established': ['owner artwork approval', 'human firing pixel appearance',
                                  'human-played game balance', 'Mac/mobile/controller',
                                  'audio', 'exports', 'performance benchmarks']}
    (evidence / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    archive = HERE / 'Runner_Animation_Review.zip'
    if archive.exists():
        raise RuntimeError('Refusing to overwrite an existing review archive')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for p in sorted(files + list(evidence.glob('*'))):
            bundle.write(p, 'RunnerReview/' + p.relative_to(HERE).as_posix())
    print('RUNNER_REAL_ART_VERIFIED: actual PNG import, 45 checks and three engine captures; not final artwork approval')

if __name__ == '__main__':
    main()
