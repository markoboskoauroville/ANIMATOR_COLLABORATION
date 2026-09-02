"""THE BRAIN BRAKE — the passage. A vortex built out of keys, for Blender.

    Put this file, brain_break_key.obj and brain_brake_vortex_guide.obj in one
    folder. Open Blender, Scripting tab, open this file, press Run.

WHAT YOU GET

    VORTEX_KEYS        one collection of linked instances of the real key,
                       laid along the spiral. Linked, so 480 keys cost one mesh
    VORTEX_GUIDE       the funnel surface itself, hidden in render. It is there
                       to fly the camera against and to check the silhouette
    VORTEX_CAM         a camera on the axis, animated from outside the mouth
                       to the throat, rolling with the spiral
    KEY_PENCIL         the material. Flat paper white, no specular, black
                       Freestyle outline. THE KEYS IN THIS SHOT ARE PENCIL

WHY THE KEYS ARE NOT GOLD, AND THIS IS NOT A LOOK NOTE

Baba, 2.9.2026. Gold in this film means FOUND. Manan has not found the key yet
when he goes through the passage, so there is no gold in it. Every key here is
graphite on paper like everything else around it. The first gold in the film is
the key at Coach Brain's neck, and the last is the key falling out of the sky.

If you make these gold the ending stops being an event. Slot 1 on the key mesh
is the drawn cream one and slot 0 is brass, and NEITHER is used here. This
script adds a third material and assigns it. That is deliberate.

THE SHAPE, AND WHERE IT COMES FROM

Viktor Schauberger's implosion vortex, not a funnel that merely narrows.

    the spiral is Kepler's harmonic spiral. Each turn comes in to 1, 1/2, 1/3,
    1/4 of the mouth radius, so the turns tighten as they approach the centre
    and the eye is pulled inward rather than led along

    the wall is a rectangular hyperbola in section, r * z constant, which is
    the cross section through the hyperboloid Schauberger called the egg. So
    the wall curves inward, it does not slope straight like a cone

    everything moves inward. Centripetal, in-winding. Schauberger's whole
    argument is that inward is the direction of life and outward is the
    direction of decay, and that is also what this shot is about

    the keys get smaller and denser toward the throat, because their scale
    follows the local radius. Nothing is hand placed

TUNING

Everything worth changing is in the block below. KEYS_PER_TURN is the one to
reach for first: raise it until the wall reads as solid at your camera angle,
lower it if the viewport crawls.
"""
import bpy, os, math
from mathutils import Vector, Matrix

# ----------------------------------------------------------------- parameters
MOUTH_R      = 7.0      # metres, radius of the near opening
TURNS        = 10       # how many times the spiral goes round on the way in
KEYS_PER_TURN= 48       # raise until the wall reads solid. 48 overlaps at the mouth
DEPTH        = 26.0     # metres from mouth plane to throat
KEY_SCALE    = 12.0     # the key is 94 mm long, so 12 makes it 1.13 m at the mouth
SCALE_FALLOFF= 0.6      # how fast keys shrink going in. 1.0 = strictly with radius
FRAMES       = 100      # length of the camera move
FPS          = 25
CAM_START    = -3.0     # metres outside the mouth, so we fly INTO it
CAM_END      = 0.86     # fraction of DEPTH the camera reaches. Never 1.0
CAM_LENS     = 24.0     # wide, so the walls wrap around the edge of frame

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_OBJ   = os.path.join(HERE, 'brain_break_key.obj')
GUIDE_OBJ = os.path.join(HERE, 'brain_brake_vortex_guide.obj')


# ------------------------------------------------------------------- the maths
def spiral(t):
    """Position on the Kepler harmonic spiral at turn parameter t, t >= 1.

    r = MOUTH_R / t          each whole turn halves, thirds, quarters the radius
    z = DEPTH * (t-1)/(T-1)  paired with r so that r*z tends to a constant,
                             which is the rectangular hyperbola in section
    theta = 2*pi*t           one full turn per unit of t
    """
    r = MOUTH_R / t
    z = DEPTH * (t - 1.0) / (TURNS - 1.0)
    th = 2.0 * math.pi * t
    return Vector((r * math.cos(th), r * math.sin(th), z)), r, th


def tangent(t, eps=1e-4):
    a, _, _ = spiral(max(1.0, t - eps))
    b, _, _ = spiral(t + eps)
    return (b - a).normalized()


# ------------------------------------------------------------------- the scene
def wipe(prefix):
    for o in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
        bpy.data.objects.remove(o, do_unlink=True)


wipe('VORTEX_')

col = bpy.data.collections.get('VORTEX_KEYS')
if col:
    bpy.data.collections.remove(col)
col = bpy.data.collections.new('VORTEX_KEYS')
bpy.context.scene.collection.children.link(col)

# the key, imported once. Everything else is a linked duplicate of this mesh
if hasattr(bpy.ops.wm, 'obj_import'):
    bpy.ops.wm.obj_import(filepath=KEY_OBJ)
else:
    bpy.ops.import_scene.obj(filepath=KEY_OBJ)
src = bpy.context.selected_objects[0]
src.name = 'VORTEX_KEY_SOURCE'
mesh = src.data

# the pencil material. Flat, unlit, no specular, so it sits on paper
pencil = bpy.data.materials.get('KEY_PENCIL') or bpy.data.materials.new('KEY_PENCIL')
pencil.use_nodes = True
bsdf = pencil.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (0.96, 0.95, 0.92, 1.0)   # warm paper
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 1.0
if 'Specular IOR Level' in bsdf.inputs:
    bsdf.inputs['Specular IOR Level'].default_value = 0.0
elif 'Specular' in bsdf.inputs:
    bsdf.inputs['Specular'].default_value = 0.0
mesh.materials.clear()
mesh.materials.append(pencil)

# lay the keys along the spiral. The key model runs along its own +Y, head at
# the origin end and bit at the far end, so +Y is aimed down the tangent and the
# key lies IN the flow rather than across it
n = 0
step = 1.0 / KEYS_PER_TURN
t = 1.0
while t < TURNS:
    pos, r, th = spiral(t)
    tan = tangent(t)
    # local +Y to the tangent, local +Z pointing out of the funnel wall
    out = Vector((math.cos(th), math.sin(th), 0.0))
    y = tan
    z = (out - y * out.dot(y)).normalized()
    x = y.cross(z)
    rot = Matrix((x, y, z)).transposed().to_4x4()

    s = KEY_SCALE * (r / MOUTH_R) ** SCALE_FALLOFF
    ob = bpy.data.objects.new('VORTEX_KEY_%04d' % n, mesh)   # LINKED, one mesh
    ob.matrix_world = Matrix.Translation(pos) @ rot @ Matrix.Scale(s, 4)
    col.objects.link(ob)
    n += 1
    t += step

bpy.data.objects.remove(src, do_unlink=True)

# the guide surface, for aiming the camera and checking the silhouette
if os.path.exists(GUIDE_OBJ):
    if hasattr(bpy.ops.wm, 'obj_import'):
        bpy.ops.wm.obj_import(filepath=GUIDE_OBJ)
    else:
        bpy.ops.import_scene.obj(filepath=GUIDE_OBJ)
    g = bpy.context.selected_objects[0]
    g.name = 'VORTEX_GUIDE'
    g.display_type = 'WIRE'
    g.hide_render = True

# the camera. Down the axis, into the throat, rolling with the spiral
cam_data = bpy.data.cameras.new('VORTEX_CAM')
cam_data.lens = CAM_LENS
cam = bpy.data.objects.new('VORTEX_CAM', cam_data)
bpy.context.scene.collection.objects.link(cam)

scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = FPS

for f in range(1, FRAMES + 1):
    u = (f - 1) / float(FRAMES - 1)
    ease = u * u * (3 - 2 * u)                      # slow out of the gate, slow in
    z = CAM_START + ease * (DEPTH * CAM_END - CAM_START)
    # roll with the spiral, so the wall turns as we go rather than sliding
    tz = 1.0 + (TURNS - 1.0) * (z / DEPTH if DEPTH else 0.0)
    roll = 2.0 * math.pi * tz * 0.5
    cam.matrix_world = (Matrix.Translation(Vector((0.0, 0.0, z)))
                        @ Matrix.Rotation(roll, 4, 'Z'))
    cam.keyframe_insert('location', frame=f)
    cam.keyframe_insert('rotation_euler', frame=f)

scene.camera = cam

# the drawn world: white, flat, outlines on
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in \
    [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] \
    else 'BLENDER_EEVEE'
world = scene.world or bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (1.0, 0.99, 0.96, 1.0)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0

scene.render.use_freestyle = True
vl = bpy.context.view_layer
vl.use_freestyle = True
if not vl.freestyle_settings.linesets:
    vl.freestyle_settings.linesets.new('pencil')
ls = vl.freestyle_settings.linesets[0]
ls.linestyle.color = (0.18, 0.17, 0.16)
ls.linestyle.thickness = 1.1

print('VORTEX built.')
print('  %d keys, one linked mesh of %d vertices' % (n, len(mesh.vertices)))
print('  mouth radius %.1f m, depth %.1f m, %d turns' % (MOUTH_R, DEPTH, TURNS))
print('  throat radius %.2f m' % (MOUTH_R / TURNS))
print('  key length %.2f m at the mouth, %.2f m at the throat'
      % (0.094 * KEY_SCALE, 0.094 * KEY_SCALE * (1.0 / TURNS) ** SCALE_FALLOFF))
print('  camera VORTEX_CAM, %d frames at %d fps = %.1f seconds'
      % (FRAMES, FPS, FRAMES / float(FPS)))
print('  material KEY_PENCIL. NOT gold. Gold in this film means found.')
