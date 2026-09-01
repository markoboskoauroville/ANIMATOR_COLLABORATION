#!/usr/bin/env python3
"""Build the BRAIN BRAKE key as a 3D mesh, from the photographed object.

    python3 build_key.py

Writes key.obj. Dimensions in millimetres, taken from the photographs in
ANIMATOR_COLLABORATION/reference/key/ and the object sheet drawn from them.

    overall length      110
    head disc           26 across, 3 thick
    clover hole         three lobes around a centre, cut clean through
    collar              three raised rings where head meets shaft
    shaft               6 across, round
    bit                 14 long, 11 deep, 2.5 thick, three square teeth
"""
import numpy as np, trimesh
from mapbox_earcut import triangulate_float64

MM = 0.001                      # export in metres, which is what Blender expects
HEAD_R, HEAD_T = 13.0, 1.6
SHAFT_R, SHAFT_L = 3.0, 74.0
BIT_L, BIT_D, BIT_T = 14.0, 11.0, 1.3
LOBE_R, LOBE_OFF = 4.0, 4.2

def ring(n, r, cx=0.0, cy=0.0, start=0.0):
    a = np.linspace(start, start + 2*np.pi, n, endpoint=False)
    return np.stack([cx + r*np.cos(a), cy + r*np.sin(a)], 1)

def clover(n=64):
    """Three lobes and a stem, as one closed loop, the shape cut through the head."""
    pts = []
    for k in range(3):
        th = np.pi/2 + k*2*np.pi/3
        cx, cy = LOBE_OFF*np.cos(th), LOBE_OFF*np.sin(th)
        a = np.linspace(th - 2.3, th + 2.3, n//3)
        pts.append(np.stack([cx + LOBE_R*np.cos(a), cy + LOBE_R*np.sin(a)], 1))
    loop = np.concatenate(pts)
    c = loop.mean(0)
    ang = np.arctan2(loop[:,1]-c[1], loop[:,0]-c[0])
    return loop[np.argsort(ang)]

def prism(outer, holes, thickness):
    """Extrude a 2D polygon with holes into a solid, capped both ends."""
    rings = [outer] + list(holes)
    verts2d = np.concatenate(rings).astype(np.float64)
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    tri = triangulate_float64(verts2d, ends).reshape(-1, 3)

    n = len(verts2d)
    v = np.vstack([np.column_stack([verts2d, np.full(n, -thickness/2)]),
                   np.column_stack([verts2d, np.full(n,  thickness/2)])])
    f = [tri[:, ::-1], tri + n]
    start = 0
    for r in rings:                                  # walls around every loop
        m = len(r)
        idx = np.arange(m) + start
        nxt = (np.arange(m) + 1) % m + start
        f.append(np.column_stack([idx, nxt, nxt + n]))
        f.append(np.column_stack([idx, nxt + n, idx + n]))
        start += m
    return trimesh.Trimesh(v, np.vstack(f), process=True)

parts = []

head = prism(ring(96, HEAD_R), [clover()[::-1]], HEAD_T)
head.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
head.apply_translation([0, 0, 0])
parts.append(head)

shaft = trimesh.creation.cylinder(radius=SHAFT_R, height=SHAFT_L, sections=48)
shaft.apply_translation([0, 0, -SHAFT_L/2 - HEAD_R*0.55])
parts.append(shaft)

for i, z in enumerate([-HEAD_R*0.55 - 2.0, -HEAD_R*0.55 - 5.0, -HEAD_R*0.55 - 8.0]):
    r = trimesh.creation.cylinder(radius=SHAFT_R*1.45, height=1.8, sections=40)
    r.apply_translation([0, 0, z])
    parts.append(r)

# the bit: a plate below the far end of the shaft, with three teeth cut out
z0 = -HEAD_R*0.55 - SHAFT_L + 4.0
# built from solid boxes rather than cut with booleans: a subtraction that
# misses simply removes the whole plate and the key loses its business end,
# which is exactly what happened first time and is invisible in the numbers.
BAR_D = 3.2                              # the spine the teeth hang from
plate = trimesh.creation.box(extents=[BAR_D, BIT_T, BIT_L])
plate.apply_translation([-SHAFT_R - BAR_D/2, 0, z0 + BIT_L/2])
parts.append(plate)
for k in range(3):
    tooth = trimesh.creation.box(extents=[BIT_D - BAR_D, BIT_T, 2.8])
    tooth.apply_translation([-SHAFT_R - BAR_D - (BIT_D - BAR_D)/2, 0,
                             z0 + 2.4 + k*4.6])
    parts.append(tooth)

key = trimesh.util.concatenate(parts)
key.apply_scale(MM)
key.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))
key.export('key.obj')

print('parts      : %d' % len(parts))
print('vertices   : %d' % len(key.vertices))
print('faces      : %d' % len(key.faces))
e = key.extents / MM
print('size mm    : %.0f x %.0f x %.0f' % tuple(e))
print('watertight : %s' % key.is_watertight)
