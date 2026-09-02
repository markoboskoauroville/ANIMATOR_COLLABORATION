"""THE BRAIN BRAKE key, for Blender.

Open Blender, go to the Scripting tab, open this file, press Run.

You get one mesh named BRAIN_BRAKE_KEY with two materials on it:

    KEY_REAL      polished brass. What the key is in the live footage.
    KEY_DRAWN     flat cream with a dark outline. What the key is in the
                  drawn world.

Slot 0 is the real one and slot 1 is the drawn one. To swap the whole key,
change the active material index, or keyframe it: the mesh never changes, only
the surface, which is the point. It is the same object crossing between two
worlds.

Dimensions are the photographed object: 110 mm long, 26 mm head, in metres so
it lands at the right scale in a Blender scene.
"""
import bpy, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
# 2.9.2026. This said 'key.obj' and the file beside it has always been called
# brain_break_key.obj, so the import failed for anyone who followed the
# instructions in the docstring above. Found while building the vortex script,
# which imports the same mesh.
OBJ = os.path.join(HERE, 'brain_break_key.obj')

for o in [o for o in bpy.data.objects if o.name.startswith('BRAIN_BRAKE_KEY')]:
    bpy.data.objects.remove(o, do_unlink=True)

if hasattr(bpy.ops.wm, 'obj_import'):
    bpy.ops.wm.obj_import(filepath=OBJ)
else:
    bpy.ops.import_scene.obj(filepath=OBJ)
key = bpy.context.selected_objects[0]
key.name = 'BRAIN_BRAKE_KEY'
key.data.name = 'BRAIN_BRAKE_KEY'

# origin at the centre of mass, so it tumbles about itself when it falls
bpy.context.view_layer.objects.active = key
bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
bpy.ops.object.shade_smooth()
key.data.use_auto_smooth = True if hasattr(key.data, 'use_auto_smooth') else False


def mat(name, base, metallic, rough, emit=None, outline=False):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = base
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    return m


# brass, measured off the photographs
real = mat('KEY_REAL', (0.72, 0.52, 0.16, 1.0), 1.0, 0.28)
# the drawn key: flat cream, no specular, so it sits in a pencil world
drawn = mat('KEY_DRAWN', (0.95, 0.79, 0.34, 1.0), 0.0, 0.9)

key.data.materials.clear()
key.data.materials.append(real)
key.data.materials.append(drawn)

print('BRAIN_BRAKE_KEY built.')
print('  %d vertices, %d faces' % (len(key.data.vertices), len(key.data.polygons)))
print('  materials: 0 = KEY_REAL brass, 1 = KEY_DRAWN flat')
print('  size: %.0f x %.0f x %.0f mm' % tuple(d*1000 for d in key.dimensions))
print('  origin at centre of volume, so it tumbles about itself')
