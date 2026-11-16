#!/usr/bin/env python3
"""Makes README thumbnails: assets/flavors/<name>.png -> assets/flavors/thumbs/<name>.jpg (640px wide).
Needs ffmpeg on PATH.   python tools/make-thumbs.py
"""
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
src = root / 'assets' / 'flavors'
out = src / 'thumbs'
out.mkdir(exist_ok=True)

# only the main flavor screenshots get thumbnails (the -hsl / -settings ones are linked at full size)
images = sorted(p for p in src.glob('*.png') if not p.stem.endswith(('-hsl', '-settings')))
if not images:
    raise SystemExit('no .png screenshots found in assets/flavors/')
for p in images:
    dest = out / (p.stem + '.jpg')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(p), '-vf', 'scale=640:-2', '-q:v', '4', str(dest)], check=True)
    print('wrote', dest.relative_to(root))
