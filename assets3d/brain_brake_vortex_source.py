#!/usr/bin/env python3
"""Build the vortex guide surface, the funnel the keys are laid on.

    python3 brain_brake_vortex_source.py

Writes brain_brake_vortex_guide.obj. No Blender and no libraries beyond the
standard library, so the shape can be checked by anybody, in any package, and
the numbers below are the single source of truth for both this and the Blender
script beside it.

THE SHAPE

Viktor Schauberger's implosion vortex. Two facts do all the work.

    THE SECTION IS A RECTANGULAR HYPERBOLA, not a cone. Schauberger held that
    the right form for a vortex chamber was the egg, which is a cross section
    through the hyperboloid of rotation of the square hyperbola. So the wall
    curves inward as it descends. A cone would be wrong and would read as a
    funnel rather than a vortex.

    THE SPIRAL IS KEPLER'S HARMONIC SPIRAL. Seen from above, successive turns
    come in to 1, 1/2, 1/3, 1/4, 1/5 of the mouth radius. The turns tighten
    toward the centre, which is what pulls the eye in rather than along.

Everything is centripetal. Inward and downward, never outward. That is the
whole of Schauberger's argument and it is also what the shot is about: Manan is
not being blown anywhere, he is being drawn in.

Keep MOUTH_R, TURNS and DEPTH identical to brain_brake_vortex.py or the guide
will not sit under the keys.
"""
import math

MOUTH_R = 7.0
TURNS   = 10
DEPTH   = 26.0
RINGS   = 80         # samples down the axis
SEGS    = 64         # samples around


def radius_at(t):
    """t is the turn parameter, 1 at the mouth and TURNS at the throat."""
    return MOUTH_R / t


def z_at(t):
    return DEPTH * (t - 1.0) / (TURNS - 1.0)


def main():
    verts, faces = [], []
    for i in range(RINGS):
        t = 1.0 + (TURNS - 1.0) * i / (RINGS - 1.0)
        r, z = radius_at(t), z_at(t)
        for j in range(SEGS):
            a = 2.0 * math.pi * j / SEGS
            verts.append((r * math.cos(a), r * math.sin(a), z))

    for i in range(RINGS - 1):
        for j in range(SEGS):
            a = i * SEGS + j + 1
            b = i * SEGS + (j + 1) % SEGS + 1
            c = (i + 1) * SEGS + (j + 1) % SEGS + 1
            d = (i + 1) * SEGS + j + 1
            faces.append((a, b, c, d))

    with open('brain_brake_vortex_guide.obj', 'w') as f:
        f.write('# THE BRAIN BRAKE, the passage. Schauberger vortex guide surface.\n')
        f.write('# rectangular hyperbola in section, Kepler harmonic spiral in plan.\n')
        f.write('# mouth radius %.3f m, throat radius %.3f m, depth %.3f m, %d turns\n'
                % (MOUTH_R, MOUTH_R / TURNS, DEPTH, TURNS))
        f.write('o VORTEX_GUIDE\n')
        for v in verts:
            f.write('v %.6f %.6f %.6f\n' % v)
        for q in faces:
            f.write('f %d %d %d %d\n' % q)

    print('brain_brake_vortex_guide.obj')
    print('  %d vertices, %d quads' % (len(verts), len(faces)))
    print('  mouth radius %.2f m -> throat radius %.2f m over %.1f m of depth'
          % (MOUTH_R, MOUTH_R / TURNS, DEPTH))
    print('  turn radii:', ', '.join('%.2f' % (MOUTH_R / k) for k in range(1, TURNS + 1)))


if __name__ == '__main__':
    main()
