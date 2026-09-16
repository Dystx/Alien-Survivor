#!/usr/bin/env python3
"""Audit the official asset contract, inspect deliveries, and export approved families.
No command generates character artwork or grants owner approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'assets' / 'pack_v1'
ID = re.compile(r'^[a-z][a-z0-9_]*$')
REVIEWS = ('style', 'motion', 'alpha_edges', 'pivot_and_scale', 'direction_coverage', 'source_rights')

class PackError(ValueError):
    pass

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise PackError(f'{path}: {exc}') from exc
    if not isinstance(value, dict):
        raise PackError(f'{path}: expected an object')
    return value

def safe(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise PackError('Invalid portable relative path')
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise PackError(f'Unsafe path: {relative}')
    result = (root / p).resolve()
    if not result.is_relative_to(root.resolve()):
        raise PackError(f'Path leaves pack: {relative}')
    return result

def load_contract(pack: Path = PACK) -> tuple[dict, dict]:
    spec = read_json(pack / 'pack.json')
    if spec.get('schema_version') != 1:
        raise PackError('Unsupported schema_version')
    if spec.get('state') != 'specification_baseline_art_not_approved':
        raise PackError('The specification cannot represent artwork approval')
    assets = {}
    for group in spec.get('asset_groups', []):
        for name in group['ids']:
            if not ID.fullmatch(name) or name in assets:
                raise PackError(f'Invalid or duplicate ID: {name}')
            a = {k: v for k, v in group.items() if k != 'ids'}
            a['id'] = name
            w, h = a['cell']
            if any(type(v) is not int or v <= 0 or v > 1024 for v in (w, h)):
                raise PackError(f'{name}: invalid cell')
            px, py = a['pivot']
            if not (0 <= px < w and 0 <= py < h):
                raise PackError(f'{name}: pivot outside cell')
            dirs = a['directions']
            if not dirs or len(set(dirs)) != len(dirs) or any(d not in ['e', 's', 'w', 'n', 'none'] for d in dirs):
                raise PackError(f'{name}: invalid direction coverage')
            if not a.get('clips'):
                raise PackError(f'{name}: no clips')
            for key, c in a['clips'].items():
                if not ID.fullmatch(key) or type(c['frames']) is not int or c['frames'] <= 0:
                    raise PackError(f'{name}/{key}: invalid frame count')
                if not math.isfinite(c['fps']) or c['fps'] <= 0:
                    raise PackError(f'{name}/{key}: invalid FPS')
                if type(c['loop']) is not bool or not 1 <= c['min_unique_frames'] <= c['frames']:
                    raise PackError(f'{name}/{key}: invalid playback rules')
            assets[name] = a
    if not assets:
        raise PackError('Empty catalogue')
    for name in spec['batch_001']['assets']:
        if name not in assets:
            raise PackError(f'Batch references unknown asset: {name}')
    return spec, assets

def slots(asset: dict, stages: set[str] | None = None):
    for clip_name, clip in asset['clips'].items():
        if stages is not None and clip['stage'] not in stages:
            continue
        for direction in asset['directions']:
            for index in range(clip['frames']):
                rel = f"families/{asset['id']}/frames/{clip_name}/{direction}/{index:03d}.png"
                yield clip_name, direction, index, rel

def check_png(path: Path, asset: dict) -> str:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != 'PNG' or image.mode != 'RGBA' or list(image.size) != asset['cell']:
                raise PackError(f'{path}: expected RGBA PNG {asset["cell"]}, got {image.mode} {image.size}')
            alpha = image.getchannel('A')
            if alpha.getextrema()[1] < 8:
                raise PackError(f'{path}: empty or effectively invisible image')
            if asset['category'] not in ('floor', 'ui'):
                w, h = image.size
                margin = 2
                for box in [(0, 0, w, margin), (0, h-margin, w, h), (0, 0, margin, h), (w-margin, 0, w, h)]:
                    if alpha.crop(box).getextrema()[1] > 0:
                        raise PackError(f'{path}: silhouette/effect touches protected frame border')
            if asset['category'] == 'floor':
                w, h = image.size
                outside = inside = filled = 0
                for y in range(h):
                    for x in range(w):
                        inside_diamond = abs((x+.5)-w/2)/(w/2) + abs((y+.5)-h/2)/(h/2) <= 1
                        av = alpha.getpixel((x, y))
                        if inside_diamond:
                            inside += 1
                            filled += int(av >= 128)
                        elif av > 16:
                            outside += 1
                if outside > 4 or filled < .96*inside:
                    raise PackError(f'{path}: floor must fill the 2:1 top diamond without slab sidewalls')
            # Transparent RGB noise cannot make duplicate frames appear distinct.
            rgba = image.convert('RGBa')
            return hashlib.sha256(rgba.tobytes()).hexdigest()
    except (OSError, SyntaxError) as exc:
        raise PackError(f'{path}: invalid PNG: {exc}') from exc

def check_delivery(pack: Path, asset: dict, require_complete=False, require_approved=False) -> dict:
    name = asset['id']
    required = list(slots(asset))
    expected = {r for _, _, _, r in required}
    present = {r for r in expected if safe(pack, r).is_file()}
    folder = pack / 'families' / name
    unexpected = {p.relative_to(pack).as_posix() for p in (folder/'frames').rglob('*.png')} - expected
    if unexpected:
        raise PackError(f'{name}: undeclared frame paths: {sorted(unexpected)[:5]}')
    pixel_hashes = {}
    for rel in sorted(present):
        pixel_hashes[rel] = check_png(safe(pack, rel), asset)
    for clip_name, clip in asset['clips'].items():
        for direction in asset['directions']:
            sequence = [r for cn, d, _, r in required if cn == clip_name and d == direction]
            if all(r in present for r in sequence):
                hashes = [pixel_hashes[r] for r in sequence]
                if len(set(hashes)) < clip['min_unique_frames']:
                    raise PackError(f'{name}/{clip_name}/{direction}: duplicated stills do not meet motion coverage')
                if clip['loop'] and len(hashes) > 1 and hashes[0] == hashes[-1]:
                    raise PackError(f'{name}/{clip_name}/{direction}: repeated loop endpoint creates a held frame')
    delivery_path = folder/'delivery.json'
    status = 'planned'
    if delivery_path.exists():
        delivery = read_json(delivery_path)
        status = delivery.get('status')
        if delivery.get('asset_id') != name or status not in ('draft', 'review', 'approved'):
            raise PackError(f'{name}: wrong asset ID or delivery status')
        if delivery.get('spec_sha256') != digest(pack/'pack.json'):
            raise PackError(f'{name}: submission targets a different specification revision')
        hashes = delivery.get('frame_sha256', {})
        if set(hashes) != present:
            raise PackError(f'{name}: delivery hashes must exactly match the frames currently present')
        for rel, value in hashes.items():
            if digest(safe(pack, rel)) != value:
                raise PackError(f'{name}: frame changed since delivery: {rel}')
        sockets = delivery.get('sockets', {})
        if name == 'player' or asset['category'] == 'weapon':
            for rel in present:
                muzzle = sockets.get(rel, {}).get('muzzle')
                if not isinstance(muzzle, list) or len(muzzle) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in muzzle):
                    raise PackError(f'{name}: per-frame muzzle socket required: {rel}')
                if not (0 <= muzzle[0] < asset['cell'][0] and 0 <= muzzle[1] < asset['cell'][1]):
                    raise PackError(f'{name}: muzzle socket outside frame: {rel}')
        sources = delivery.get('sources', [])
        if not sources:
            raise PackError(f'{name}: editable source/provenance record is required')
        for source in sources:
            source_path = safe(pack, source['path'])
            if not source_path.is_file() or digest(source_path) != source.get('sha256'):
                raise PackError(f'{name}: source missing or modified')
            if not source.get('provenance'):
                raise PackError(f'{name}: source provenance missing')
        if status == 'approved':
            if present != expected:
                raise PackError(f'{name}: cannot approve an incomplete family')
            review = delivery.get('review', {})
            if not all(review.get(key) is True for key in REVIEWS):
                raise PackError(f'{name}: human review checks are incomplete')
            if name == 'player' and review.get('aim_and_strafe') is not True:
                raise PackError('player: manual aim and strafe review is required')
            owner = delivery.get('owner_approval', {})
            if not all(isinstance(owner.get(k), str) and owner[k].strip() for k in ('reviewer', 'date', 'evidence')):
                raise PackError(f'{name}: explicit owner approval record missing')
            if delivery.get('public_source_permission') is not True:
                raise PackError(f'{name}: public-source distribution not confirmed')
    elif present:
        raise PackError(f'{name}: frames without a delivery record are not a submission')
    if require_complete and present != expected:
        raise PackError(f'{name}: incomplete ({len(present)}/{len(expected)} frames)')
    if require_approved and status != 'approved':
        raise PackError(f'{name}: owner approval not recorded; export refused')
    return {'id':name,'status':status,'present':len(present),'required':len(expected)}

def audit(pack: Path = PACK) -> list[dict]:
    _, assets = load_contract(pack)
    return [check_delivery(pack, asset) for asset in assets.values()]

def export_family(pack: Path, asset: dict, destination: Path) -> dict:
    check_delivery(pack, asset, require_complete=True, require_approved=True)
    out = destination / asset['id']
    if out.exists():
        raise PackError(f'{out}: exists; choose a fresh build folder')
    out.mkdir(parents=True)
    spec, _ = load_contract(pack)
    gutter = spec['image_contract']['atlas_gutter_pixels']
    limit = spec['image_contract']['max_atlas_size']
    w, h = asset['cell']; cw, ch = w+2*gutter, h+2*gutter
    columns = limit//cw; rows = limit//ch
    if columns < 1 or rows < 1:
        raise PackError('Frame exceeds atlas limit')
    frame_slots = list(slots(asset)); capacity = columns*rows
    frames = []; pages=[]
    for offset in range(0, len(frame_slots), capacity):
        chunk=frame_slots[offset:offset+capacity]
        used_columns=min(columns,len(chunk)); used_rows=math.ceil(len(chunk)/columns)
        page=Image.new('RGBA',(used_columns*cw,used_rows*ch))
        page_id=len(pages)
        for index,(clip,direction,number,rel) in enumerate(chunk):
            x=(index%columns)*cw+gutter; y=(index//columns)*ch+gutter
            with Image.open(safe(pack,rel)) as image:
                page.paste(image,(x,y))
            frames.append({'clip':clip,'direction':direction,'frame':number,'page':page_id,'region':[x,y,w,h]})
        filename=f'atlas_{page_id:02d}.png'; page.save(out/filename)
        pages.append({'file':filename,'size':list(page.size),'sha256':digest(out/filename)})
    delivery = read_json(pack/'families'/asset['id']/'delivery.json')
    metadata={'sockets': delivery.get('sockets', {}), 'asset_id':asset['id'],'spec_sha256':digest(pack/'pack.json'),'cell':asset['cell'],'pivot':asset['pivot'],'clips':asset['clips'],'pages':pages,'frames':frames}
    (out/'atlas.json').write_text(json.dumps(metadata,indent=2)+'\n')
    # Stable sprite cells: centre minus pivot places the ground anchor at node origin.
    resource_root=f"res://assets/pack_v1/{asset['id']}"
    text=[f'[gd_resource type="SpriteFrames" load_steps={1+len(pages)+len(frames)} format=3]', '']
    for index,p in enumerate(pages):
        text.append(f'[ext_resource type="Texture2D" path="{resource_root}/{p["file"]}" id="p{index}"]')
    for index,f in enumerate(frames):
        text += ['',f'[sub_resource type="AtlasTexture" id="f{index}"]',f'atlas = ExtResource("p{f["page"]}")', 'region = Rect2(%d, %d, %d, %d)'%tuple(f['region'])]
    animations=[]
    for clip,c in asset['clips'].items():
        for direction in asset['directions']:
            refs=[f'{{"duration": 1.0, "texture": SubResource("f{i}")}}' for i,f in enumerate(frames) if f['clip']==clip and f['direction']==direction]
            animations.append('{"frames": ['+', '.join(refs)+'], "loop": '+str(c['loop']).lower()+', "name": &"'+clip+'_'+direction+'", "speed": '+str(float(c['fps']))+'}')
    text += ['', '[resource]', 'animations = ['+',\n'.join(animations)+']','']
    (out/'sprite_frames.tres').write_text('\n'.join(text))
    (out/'sprite.tscn').write_text('[gd_scene load_steps=2 format=3]\n\n[ext_resource type="SpriteFrames" path="'+resource_root+'/sprite_frames.tres" id="1"]\n\n[node name="Asset" type="AnimatedSprite2D"]\nsprite_frames = ExtResource("1")\noffset = Vector2(%s, %s)\n'%(w/2-asset['pivot'][0],h/2-asset['pivot'][1]))
    return metadata

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack',type=Path,default=PACK)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('audit')
    family=sub.add_parser('check-family'); family.add_argument('asset')
    export=sub.add_parser('export'); export.add_argument('--asset',help='omit for the entire approved pack'); export.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        spec, assets=load_contract(args.pack)
        if args.command=='audit':
            report=audit(args.pack)
            present=sum(r['present'] for r in report); required=sum(r['required'] for r in report); approved=sum(r['status']=='approved' for r in report)
            print(f'CONTRACT VALID: {len(assets)} assets / {required} required frames. {present} present; {approved} approved families.')
            print('ART INCOMPLETE / NOT RELEASE-READY' if approved<len(assets) else 'All families carry approval records; export may proceed.')
            return 0
        if args.command=='check-family':
            if args.asset not in assets: raise PackError('Unknown asset')
            print(json.dumps(check_delivery(args.pack,assets[args.asset],require_complete=True),indent=2))
            print('File validity does not grant animation/art approval.')
            return 0
        chosen=list(assets.values()) if args.asset is None else [assets[args.asset]]
        # Validate all before writing: missing actors must never create a half-exported full pack.
        for a in chosen: check_delivery(args.pack,a,require_complete=True,require_approved=True)
        for a in chosen: export_family(args.pack,a,args.out)
        print(f'EXPORTED {len(chosen)} approved assets to {args.out}. No gameplay files were edited.')
        return 0
    except (PackError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f'ASSET CHECK FAILED: {exc}',file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
