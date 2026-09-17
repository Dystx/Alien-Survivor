#!/usr/bin/env python3
"""Deterministic creature-only surface shading, baked by the offline renderer.

Pigmentation, keratin grain and acid membranes are attached in each mesh part's
UV coordinates. No frame, camera, time, screenshot or human image enters the
pattern. Geometry, skeletal poses, pivots and sockets are not modified.
The existing GLB is the geometry master; this module is the surface source.
"""
from __future__ import annotations
import hashlib
from functools import lru_cache
import numpy as np

VERSION = 'creature_surface_1'
KINDS = frozenset(('runner', 'spitter', 'charger', 'brute', 'brood_warden'))
TEXTURE_SIZE = (256, 128)


def seed_for(asset: str, part: str) -> int:
    return int.from_bytes(hashlib.sha256((VERSION+asset+'/'+part).encode()).digest()[:4], 'little')


def value_noise(p: np.ndarray, seed: int) -> np.ndarray:
    """Bounded continuous 3D noise; uses local position, not random frame data."""
    cell = np.floor(p).astype(np.int64)
    f = p - cell
    f = f*f*(3-2*f)
    result = np.zeros(p.shape[:-1], dtype=float)
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                q = cell + (x, y, z)
                h = (q[...,0]*73856093 ^ q[...,1]*19349663 ^ q[...,2]*83492791 ^ seed) & 0xFFFFFFFF
                h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
                h = (h ^ (h >> 16)) / 4294967295.0
                weight = (f[...,0] if x else 1-f[...,0]) * (f[...,1] if y else 1-f[...,1]) * (f[...,2] if z else 1-f[...,2])
                result += h*weight
    return result


def category(material: str) -> str:
    if material in ('eye', 'amber', 'ember', 'marking', 'mouth'):
        return 'accent'
    if material in ('acid', 'acid_light', 'acid_core', 'acid_rim', 'vein'):
        return 'membrane'
    if material in ('shell', 'shell_edge'):
        return 'shell'
    if material in ('ivory', 'claw', 'ridge'):
        return 'keratin'
    if material == 'tendon':
        return 'tendon'
    return 'skin'


def pigment(p: np.ndarray, material: str, base: np.ndarray, seed: int) -> np.ndarray:
    typ = category(material)
    broad = value_noise(p*2.8, seed)
    medium = value_noise(p*10.0, seed+17)
    fine = value_noise(p*33.0, seed+41)
    fibers = np.sin(p[...,2]*42.0 + value_noise(p*4, seed+37)*6 + p[...,0]*7)
    gain = np.ones(p.shape[:-1])
    colour = np.broadcast_to(np.asarray(base, float), (*gain.shape, 3)).copy()
    if typ == 'skin':
        # Larger bruised patches read at game size; pores remain subordinate.
        gain = 1.02 + .40*(broad-.5) + .34*(medium-.5) + .15*(fine-.5)
        scars = np.exp(-np.square((medium-.48)*32)) * np.clip((broad-.44)*5,0,1)
        pores = np.clip((fine-.69)*5,0,1)
        gain -= scars*.25 + pores*.19
        colour[...,0] += (.10*(medium-.5))
        colour[...,1] += (.025*(broad-.5))
    elif typ == 'tendon':
        gain = .98 + .16*fibers + .23*(medium-.5) + .10*(fine-.5)
    elif typ == 'keratin':
        # Long growth striations, stained root and chipped light seams.
        stain = np.clip(.15 - p[...,2]*.15,0,.32)
        gain = 1.08 - stain + .16*fibers + .31*(medium-.5) + .14*(fine-.5)
        colour = colour*.84 + np.array([.45,.38,.29])*.16
    elif typ == 'shell':
        grooves = np.exp(-np.square((medium-.50)*27))
        gain = 1.12 + .38*(broad-.5) + .34*(fine-.5) - .24*grooves
        chips = np.clip((medium-.67)*6,0,1) * (.6+.4*fine)
        colour += chips[...,None]*np.array([.14,.13,.10])
    elif typ == 'membrane':
        veins = np.exp(-np.square((medium-.47)*19))
        gain = .96 + .28*(broad-.5) + .18*(fine-.5) - .28*veins
        colour = colour*.78 + np.array([.27,.30,.12])*.22
    else:
        gain = .96 + .04*(medium-.5)
    return np.clip(colour*gain[...,None], 0.008, 1)


def mesh_uv(part: dict, normal_vectors) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Duplicate only a texture seam. Preserve every geometric triangle exactly."""
    v = part['vertices']; f = part['faces']; normals = normal_vectors(v, f)
    if len(v) == 28*19 and len(f) == 28*18*2:
        uv = np.column_stack(((np.arange(len(v)) % 28)/28., (np.arange(len(v))//28)/18.))
    elif len(v) % 10 == 0 and len(f) == (len(v)//10-1)*20:
        rows = len(v)//10
        uv = np.column_stack(((np.arange(len(v)) % 10)/10., (np.arange(len(v))//10)/max(1,rows-1)))
    else:
        # The charger's hand-modelled wedge is planar, not an ellipsoid.
        lo = v.min(axis=0); extent = np.maximum(v.max(axis=0)-lo, .0001)
        uv = ((v-lo)/extent)[:,[0,1]]
        return v, f, normals, uv
    vs=list(v); ns=list(normals); coords=list(uv); faces=f.copy(); cache={}
    for row,triangle in enumerate(f):
        values=uv[triangle,0]
        if values.max()-values.min() > .5:
            for col,index in enumerate(triangle):
                if uv[index,0] < .5:
                    if int(index) not in cache:
                        cache[int(index)] = len(vs)
                        vs.append(v[index]); ns.append(normals[index]); coords.append(uv[index]+[1,0])
                    faces[row,col] = cache[int(index)]
    return np.array(vs),faces,np.array(ns),np.array(coords)


@lru_cache(maxsize=1024)
def texture_pixels(asset: str, name: str, material: str, hex_colour: str) -> np.ndarray:
    width,height=TEXTURE_SIZE
    u=np.linspace(0,1,width); v=np.linspace(0,1,height)
    U,V=np.meshgrid(u,v)
    angle=U*2*np.pi; lat=(V-.5)*np.pi
    # Spherical embedding keeps both wrap seam and poles exactly continuous.
    p=np.stack((np.cos(angle)*np.cos(lat),np.sin(angle)*np.cos(lat),np.sin(lat)),axis=-1)
    base=np.array([int(hex_colour[i:i+2],16) for i in (0,2,4)])/255.
    pixels=np.uint8(np.round(pigment(p,material,base,seed_for(asset,name))*255))
    pixels[:,-1]=pixels[:,0]
    return pixels


def apply(master, actors, normal_vectors) -> None:
    """Attach finite, source-bound textures to existing actors; never the player."""
    if master.recipe['asset_id'] not in KINDS:
        raise ValueError('Creature surfaces must never process the selected human')
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    for part,actor in zip(master.parts,actors):
        spec=master.recipe['materials'][part['material']]
        v,f,n,uv=mesh_uv(part,normal_vectors)
        poly=vtk.vtkPolyData();points=vtk.vtkPoints();points.SetData(numpy_to_vtk(v,deep=True));poly.SetPoints(points)
        cells=vtk.vtkCellArray();data=np.column_stack([np.full(len(f),3),f]).astype(np.int64).ravel()
        cells.ImportLegacyFormat(numpy_to_vtkIdTypeArray(data,deep=True));poly.SetPolys(cells)
        normals=numpy_to_vtk(n,deep=True);normals.SetName('Normals');poly.GetPointData().SetNormals(normals)
        tcoords=numpy_to_vtk(uv,deep=True);tcoords.SetName('TextureCoordinates');poly.GetPointData().SetTCoords(tcoords)
        mapper=actor.GetMapper();mapper.SetInputData(poly);mapper.ScalarVisibilityOff()
        pixels=texture_pixels(master.recipe['asset_id'],part['name'],part['material'],spec['hex'])
        im=vtk.vtkImageData();im.SetDimensions(pixels.shape[1],pixels.shape[0],1)
        im.GetPointData().SetScalars(numpy_to_vtk(pixels.reshape(-1,3),deep=True,array_type=vtk.VTK_UNSIGNED_CHAR))
        texture=vtk.vtkTexture();texture.SetInputData(im);texture.InterpolateOn();texture.MipmapOn();texture.RepeatOn()
        actor.SetTexture(texture)
        prop=actor.GetProperty();prop.SetColor(1,1,1)
        typ=category(part['material'])
        prop.SetSpecular(min(float(spec.get('specular',.1)),.055 if typ=='membrane' else .022))
        prop.SetSpecularPower(12 if typ=='membrane' else 8)
        # Lighting and camera are deliberately unchanged; only material response.
    master.surface_version=VERSION
