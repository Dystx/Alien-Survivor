#!/usr/bin/env python3
"""Offline motion review for the existing assets/pack_v1 contract.

Uses artpack.py for specification and delivery checks. Does not create artwork,
change approvals, export production resources or write into the game.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class ReviewError(ValueError):
    pass


def frame_data(path: Path, cell: list[int], margin: int = 2) -> tuple[str, str]:
    """Keep original pixels; return embedded PNG and translation-invariant hash."""
    with Image.open(path) as image:
        image.load()
        if image.format != 'PNG' or image.mode != 'RGBA' or list(image.size) != cell:
            raise ReviewError(f'{path}: expected RGBA PNG {cell}')
        alpha = image.getchannel('A')
        box = alpha.getbbox()
        if box is None or alpha.getextrema()[1] < 8:
            raise ReviewError(f'{path}: empty or effectively invisible frame')
        w, h = image.size
        if box[0] < margin or box[1] < margin or box[2] > w-margin or box[3] > h-margin:
            raise ReviewError(f'{path}: content reaches protected frame margin')
        # RGBa premultiplication removes invisible RGB noise from the motion hash.
        normalized = image.convert('RGBa').crop(box)
        shape = json.dumps(normalized.size).encode() + normalized.tobytes()
        digest = hashlib.sha256(shape).hexdigest()
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode(), digest


def prepare_clip(asset: dict, clip_name: str, paths: dict[str, list[Path]], sockets=None) -> dict:
    if clip_name not in asset['clips']:
        raise ReviewError(f'Unknown clip: {clip_name}')
    clip = asset['clips'][clip_name]
    if set(paths) != set(asset['directions']):
        raise ReviewError('Missing or extra direction in clip review')
    directions, fingerprints = {}, []
    margin = 0 if asset['category'] in ('floor', 'ui') else 2
    for direction in asset['directions']:
        if len(paths[direction]) != clip['frames']:
            raise ReviewError(f'{direction}: incomplete clip')
        images, hashes = [], []
        for p in paths[direction]:
            encoded, digest = frame_data(p, asset['cell'], margin)
            images.append(encoded)
            hashes.append(digest)
        if len(set(hashes)) < clip['min_unique_frames']:
            raise ReviewError(f'{direction}: shifted copies of one drawing are not articulated motion')
        if clip['loop'] and len(hashes) > 1 and hashes[0] == hashes[-1]:
            raise ReviewError(f'{direction}: translated/repeated loop endpoint')
        fingerprints.append(tuple(hashes))
        directions[direction] = images
    if len(set(fingerprints)) != len(fingerprints):
        raise ReviewError('Same view is labelled as multiple directions')
    return {'asset': asset['id'], 'clip': clip_name, 'cell': asset['cell'],
            'pivot': asset['pivot'], 'fps': clip['fps'], 'loop': clip['loop'],
            'directions': directions, 'sockets': sockets or {},
            'status': 'review_only_not_approval'}


def write_review(data: dict, destination: Path) -> None:
    if destination.exists():
        raise ReviewError('Refusing to overwrite an existing review')
    payload = json.dumps(data).replace('<', '\\u003c')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Alien Survivor motion review</title>
<style>body{background:#17191d;color:#ece7da;font:16px system-ui;margin:24px}button,select,input{font:inherit;margin:5px;padding:6px}canvas{image-rendering:pixelated;border:1px solid #777}small{display:block;max-width:760px;margin:14px 0}</style>
<h1>__TITLE__</h1><p>Motion review only. This page does not approve or integrate artwork.</p>
<label>Direction <select id="dir"></select></label><button id="play">Pause</button><button id="step">Step</button>
<label>Speed <select id="speed"><option value="0.5">Half</option><option value="1" selected>Normal</option></select></label>
<label>Scale <select id="scale"><option>1</option><option selected>2</option><option>3</option><option>4</option></select></label>
<label>Background <select id="bg"><option value="checker">Checker</option><option value="dark">Dark</option><option value="light">Light</option></select></label><br>
<canvas id="view"></canvas><br><input id="scrub" type="range" min="0" value="0"><span id="counter"></span>
<small>Red cross: declared ground pivot. Cyan cross: muzzle socket when supplied. Inspect foot planting, weapon attachment, anatomy, actual rear views and the loop join. Duplicate checks cannot judge animation quality or ownership.</small>
<script>const p=__DATA__,cv=document.querySelector('#view'),ctx=cv.getContext('2d'),dir=document.querySelector('#dir'),scrub=document.querySelector('#scrub');
const frames={};for(const [key,items]of Object.entries(p.directions)){dir.add(new Option(key,key));frames[key]=items.map(v=>{const im=new Image();im.src='data:image/png;base64,'+v;return im})}
let index=0,playing=true,last=0,acc=0;const play=document.querySelector('#play');function state(){play.textContent=playing?'Pause':'Play'}
dir.onchange=()=>{index=0;acc=0};play.onclick=()=>{if(!playing&&!p.loop&&index===frames[dir.value].length-1){index=0;acc=0}playing=!playing;state()};document.querySelector('#step').onclick=()=>{playing=false;index=(index+1)%frames[dir.value].length;state();draw()};
scrub.oninput=()=>{playing=false;index=+scrub.value;state();draw()};
function cross(x,y,color,z){ctx.strokeStyle=color;ctx.beginPath();ctx.moveTo(x*z-6,y*z);ctx.lineTo(x*z+6,y*z);ctx.moveTo(x*z,y*z-6);ctx.lineTo(x*z,y*z+6);ctx.stroke()}
function draw(){const f=frames[dir.value],z=+document.querySelector('#scale').value;cv.width=p.cell[0]*z;cv.height=p.cell[1]*z;ctx.imageSmoothingEnabled=false;
const bg=document.querySelector('#bg').value;if(bg==='checker'){for(let y=0;y<cv.height;y+=16)for(let x=0;x<cv.width;x+=16){ctx.fillStyle=((x+y)/16%2)?'#383c40':'#56595e';ctx.fillRect(x,y,16,16)}}else{ctx.fillStyle=bg==='dark'?'#15181c':'#e0dbd1';ctx.fillRect(0,0,cv.width,cv.height)}
if(f[index].complete&&f[index].naturalWidth)ctx.drawImage(f[index],0,0,cv.width,cv.height);cross(p.pivot[0],p.pivot[1],'#ff7368',z);const sockets=p.sockets[dir.value]||[];if(sockets[index]&&sockets[index].muzzle)cross(...sockets[index].muzzle,'#6de7ef',z);
scrub.max=f.length-1;scrub.value=index;document.querySelector('#counter').textContent=`Frame ${index+1}/${f.length} | ${p.fps} fps | ${p.loop?'loop':'one-shot'}`}
function tick(t){if(playing){acc+=Math.min(100,t-last);const ms=1000/(p.fps*+document.querySelector('#speed').value);while(acc>=ms){if(index<frames[dir.value].length-1)index++;else if(p.loop)index=0;else{playing=false;state()}acc-=ms}}last=t;draw();requestAnimationFrame(tick)}requestAnimationFrame(tick);
</script></html>'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page.replace('__TITLE__', html.escape(data['asset']+' / '+data['clip'])).replace('__DATA__', payload), encoding='utf-8')


def main() -> int:
    import artpack  # The existing authoritative contract/delivery validator.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', type=Path, default=artpack.PACK)
    parser.add_argument('--asset', required=True)
    parser.add_argument('--clip', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        _, assets = artpack.load_contract(args.pack)
        if args.asset not in assets:
            raise ReviewError('Unknown asset')
        asset = assets[args.asset]
        # Drafts may be reviewed; existing files still require valid delivery hashes/source.
        artpack.check_delivery(args.pack, asset, require_complete=False, require_approved=False)
        if args.clip not in asset['clips']:
            raise ReviewError('Unknown clip')
        paths = {d: [] for d in asset['directions']}
        socket_data = {d: [] for d in asset['directions']}
        delivery = artpack.read_json(args.pack/'families'/args.asset/'delivery.json')
        for clip, direction, _, rel in artpack.slots(asset):
            if clip == args.clip:
                paths[direction].append(artpack.safe(args.pack, rel))
                socket_data[direction].append(delivery.get('sockets', {}).get(rel, {}))
        target = args.out.resolve()
        if target.is_relative_to(args.pack.resolve()) or target.is_relative_to((ROOT/'game').resolve()):
            raise ReviewError('Write reviews to a separate art_build folder, not source or game directories')
        data = prepare_clip(asset, args.clip, paths, socket_data)
        write_review(data, target)
        print(f'REVIEW BUILT: {target}. No artwork approval or game changes.')
        return 0
    except (ReviewError, artpack.PackError, OSError, ValueError) as exc:
        print(f'REVIEW BLOCKED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
