"""V4: sculpted architectural joinery, mineral finishes and padded inscriptions.

Builds from the preserved V3 native file. All shelves remain empty; room,
window tracery, fresco, floor, hinges and furniture keep their original scale.
"""
import ast
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent / 'v3/XR_Guild_Library_v3.blend'))
S = bpy.context.scene
S.frame_set(1)
collections = {c.name[:2]: c for c in S.collection.children}
for code, title in [('19', 'V4 sculpted capitals'), ('20', 'V4 cabinetmaking'),
                    ('21', 'V4 profiled arch surrounds'), ('22', 'V4 inscription panels')]:
    col = bpy.data.collections.new(code + ' ' + title)
    S.collection.children.link(col)
    collections[code] = col
module = ast.parse((ROOT.parent / 'scripts/build_library.py').read_text())
helpers = {'mesh', 'cube', 'curve', 'bez', 'P', 'C', 'CV', 'arch'}
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef)
                             and n.name in helpers], type_ignores=[]), 'geometry_helpers', 'exec'))
wood = bpy.data.materials['Handcrafted figured walnut']
dark = bpy.data.materials['Walnut endgrain and recess']
gold = bpy.data.materials['Gilt brass | gently aged']
edge = bpy.data.materials['Polished gold leaf edges']
bronze = bpy.data.materials['Patinated bronze recesses']
lab = bpy.data.materials['Labradorite | green stone with blue schiller']
headline = bpy.data.materials['V3 | high contrast architectural gold']
headline.name = 'V4 | high contrast architectural gold'


def solid(name, color, metallic=0, roughness=.5):
    ma = bpy.data.materials.new(name)
    ma.use_nodes = True
    bs = ma.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Roughness'].default_value = roughness
    return ma


stone = solid('V4 | smoked limestone arch mouldings', (.13, .105, .072), .06, .40)
inset = solid('V4 | charcoal enamel inscription fields', (.016, .021, .020), .10, .52)
burled = dark.copy()
burled.name = 'V4 | burr walnut recessed panels'

# Preserve V3 fine ornament; replace only plain fields and the outer arch casing.
removed = []
to_remove = []
for ob in list(S.objects):
    col = next((c.name[:2] for c in ob.users_collection), '')
    remove = ((col == '14' and 'recessed field panel' in ob.name)
              or ob.name.startswith('V3 | bookcase wall heading')
              or (col == '03' and 'arched surround' in ob.name and not ob.name.endswith('-0.075'))
              or (col == '15' and 'layered window archivolt' in ob.name))
    if remove:
        removed.append(ob.name)
        to_remove.append(ob)
bpy.data.batch_remove(ids=to_remove)


def sculpt_leaf(name, spine, width, depth, ma, col):
    """A broad, folded leaf with a tapered edge and a raised central rib."""
    vs, fs = [], []
    for j, p in enumerate(spine):
        u = j / (len(spine) - 1)
        tangent = Vector(spine[min(j + 1, len(spine) - 1)]) - Vector(spine[max(j - 1, 0)])
        across = Vector((tangent.z, 0, -tangent.x)).normalized()
        half = width * .5 * max(.002, math.sin(math.pi * u)) ** .72
        half *= 1 + .10 * math.sin(u * math.pi * 6)
        for k in range(9):
            v = k / 4 - 1
            q = Vector(p) + across * v * half
            q.y -= depth * (1 - v * v) * math.sin(math.pi * u)
            q.y += depth * .17 * math.cos(v * math.pi * 4) * math.sin(math.pi * u)
            vs.append(tuple(q))
    for j in range(len(spine) - 1):
        for k in range(8):
            q = j * 9 + k
            fs.append((q, q + 1, q + 10, q + 9))
    return mesh(name, vs, fs, ma, col, True)


# Preserve every V3 capital leaf, midrib, side vein and rolled volute.
# New edging follows the actual lobed leaf mesh, so it remains fine and fitted.
capital_leaves = [o for o in S.objects if o.type == 'MESH' and 'acanthus row' in o.name]
for leaf in capital_leaves:
    vertices = [leaf.matrix_world @ v.co for v in leaf.data.vertices]
    left = [vertices[j * 5] for j in range(25)]
    right = [vertices[j * 5 + 4] for j in reversed(range(25))]
    outline = [tuple(v) for v in left + right]
    curve('V4 | acanthus scalloped leaf edging', [outline], .0018, edge, '19', True)
for i in range(12):
    a = (i + .5) * math.pi / 6
    cx, cy = 3.95 * math.cos(a), 3.95 * math.sin(a)
    for radius, height in [(.181, 4.012), (.282, 4.468)]:
        for phase in [0, math.pi]:
            pts = []
            for j in range(385):
                t = j * math.tau / 384
                rr = radius + .0035 * math.sin(48 * t + phase)
                pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t),
                            height + .0035 * math.cos(48 * t + phase)))
            curve('V4 | capital fine twisted fillet', [pts], .002, edge, '19')


def profile_sweep(name, a, line, y, profile, ma, col, closed=False):
    """Sweep a carved cross-section around a facade path in the x/z plane."""
    vs, fs = [], []
    n = len(line)
    for j, (x, z) in enumerate(line):
        before = Vector(line[(j - 1) % n] if closed else line[max(0, j - 1)])
        after = Vector(line[(j + 1) % n] if closed else line[min(n - 1, j + 1)])
        tangent = (after - before).normalized()
        normal = Vector((-tangent.y, tangent.x))
        for offset, relief in profile:
            vs.append(P(a, x + normal.x * offset, y - relief, z + normal.y * offset))
    stride = len(profile)
    for j in range(n if closed else n - 1):
        for k in range(stride - 1):
            q = j * stride + k
            qn = ((j + 1) % n) * stride + k
            fs.append((q, q + 1, qn + 1, qn))
    return mesh(name, vs, fs, ma, col, True)


def frame(name, a, x, y, z, w, h, ma, col, thickness=.028):
    line = [(x - w / 2, z - h / 2), (x + w / 2, z - h / 2),
            (x + w / 2, z + h / 2), (x - w / 2, z + h / 2)]
    profile = [(-thickness, 0), (-thickness * .7, .012),
               (-thickness * .35, .025), (0, .030), (thickness * .25, .018)]
    return profile_sweep(name, a, line, y, profile, ma, col, True)


def facade_leaf(a, name, points, width, ma=gold, col='20'):
    leaf = sculpt_leaf(name, bez(points, 22), width, .012, ma, col)
    # Local mesh is a facade; transform its vertices into the same bay frame.
    for v in leaf.data.vertices:
        v.co = P(a, *v.co)
    leaf.data.update()


for bay in [1, 3, 5, 7, 11]:
    a = bay * math.pi / 6
    # Preserve the original fine center inlay and broad two-bay layout.
    for sign in [-1, 1]:
        for offset in [-.017, .017]:
            C('V4 | routed stile flute', a, sign * .84 + offset, 3.474, 1.95,
              .008, .011, 2.87, dark, '20', .003)
        # A continuous, fine climbing inlay fills the long lower stile; its
        # leaves sit on the stems instead of becoming detached decorations.
        stem = [(sign * .84 + .010 * math.sin(j / 96 * math.tau * 4),
                 3.444, .52 + j / 96 * 2.12) for j in range(97)]
        CV('V4 | stile climbing vine inlay', a, [stem], .0026, gold, '20')
        for j in range(9):
            z = .62 + j * .222
            side = -1 if j % 2 else 1
            x = sign * .84 + .010 * math.sin((z - .52) / 2.12 * math.tau * 4)
            branch = bez([(x, 3.442, z), (x + side * .015, 3.442, z + .01),
                          (x + side * .027, 3.442, z + .027),
                          (x + side * .027, 3.442, z + .05)], 12)
            CV('V4 | stile fine branching inlay', a, [branch], .002, edge, '20')
            facade_leaf(a, 'V4 | stile tiny chased leaf',
                        [(x + side * .020, 3.439, z + .028),
                         (x + side * .03, 3.439, z + .04),
                         (x + side * .027, 3.439, z + .06),
                         (x + side * .025, 3.439, z + .075)], .018)
        # Shaped bracket joins crown and stile rather than a floating ornament.
        for k in range(3):
            facade_leaf(a, 'V4 | crown carved corbel',
                        [(sign * .84, 3.447, 3.34), (sign * .83, 3.43, 3.48),
                         (sign * (.81 - k * .035), 3.39, 3.63),
                         (sign * (.79 - k * .04), 3.43, 3.66)], .045, wood)
    for xc in [-.402, .402]:
        line3 = bez([(xc - .38, 0, 3.16), (xc - .38, 0, 3.48),
                     (xc - .22, 0, 3.61), (xc, 0, 3.63)], 24)
        line3 += bez([(xc, 0, 3.63), (xc + .22, 0, 3.61),
                      (xc + .38, 0, 3.48), (xc + .38, 0, 3.16)], 24)[1:]
        line = [(x, z) for x, _, z in line3]
        profile_sweep('V4 | bookcase carved ogee arch', a, line, 3.49,
                      [(-.032, 0), (-.025, .015), (-.01, .035), (0, .042),
                       (.012, .039), (.022, .019), (.026, 0)], wood, '20')
        CV('V4 | arch fine gilt lip', a, [[(x, 3.447, z) for x, z in line]], .0035, edge, '20')
        # A five-leaf palmette occupies only the upper arch spandrel.
        for k in range(-2, 3):
            facade_leaf(a, 'V4 | upper arch palmette',
                        [(xc, 3.515, 3.39), (xc + k * .035, 3.51, 3.46),
                         (xc + k * .080, 3.505, 3.52),
                         (xc + k * .093, 3.51, 3.565 - abs(k) * .017)], .049, wood)
    # Recessed burr panels and substantial bevelled frames under the first shelf.
    for xc in [-.57, 0, .57]:
        C('V4 | recessed burr walnut field', a, xc, 3.463, .30, .48, .025, .225, burled, '20', .007)
        frame('V4 | raised cabinet panel moulding', a, xc, 3.440, .30, .49, .235, wood, '20', .016)
        for sign in [-1, 1]:
            facade_leaf(a, 'V4 | panel inlaid iris',
                        [(xc, 3.455, .225), (xc + sign * .06, 3.455, .245),
                         (xc + sign * .16, 3.455, .29), (xc + sign * .16, 3.455, .355)], .039, wood)
        facade_leaf(a, 'V4 | panel central iris',
                    [(xc, 3.455, .225), (xc - .018, 3.455, .28),
                     (xc + .014, 3.455, .34), (xc, 3.455, .39)], .045, wood)
    # Cornice profile with a real shadow gap and restrained gilt highlights.
    for z, w, d, h, ma in [(3.66, 1.78, .49, .030, dark), (3.692, 1.85, .53, .036, wood),
                          (3.73, 1.91, .56, .022, wood), (3.755, 1.94, .57, .012, edge),
                          (3.784, 1.88, .53, .040, wood)]:
        C('V4 | case crown stepped profile', a, 0, 3.72, z, w, d, h, ma, '20', .008)
    # Side leaves echo the pediment's shape while leaving its silhouette legible.
    for sign in [-1, 1]:
        for k in range(3):
            facade_leaf(a, 'V4 | pediment carved foliage',
                        [(0, 3.739, 3.86), (sign * .18, 3.716, 3.9),
                         (sign * (.35 + k * .12), 3.722, 3.98 + k * .03),
                         (sign * (.35 + k * .13), 3.735, 4.12 - k * .045)], .09, wood)

# Original crown rosettes and cabochons remain above the deeper cornice.
for ob in collections['14'].objects:
    if ob.parent: continue
    if ob.type == 'CURVE' and 'chased rosette' in ob.name:
        pts = [p.co for sp in ob.data.splines for p in sp.points]
        if pts and 3.68 < sum(p.z for p in pts) / len(pts) < 3.80:
            for sp in ob.data.splines:
                for p in sp.points:
                    r = math.hypot(p.co.x, p.co.y)
                    p.co.x *= (r - .035) / r; p.co.y *= (r - .035) / r
    elif 'cabochon rosette heart' in ob.name and 3.68 < ob.location.z < 3.80:
        a = math.atan2(ob.location.y, ob.location.x)
        ob.location += Vector(P(a, 0, -.035, 0))

# The actual gilt window tracery is unchanged. A profiled, stepped stone casing
# replaces round tubes around it, and stops outside the clear glazing aperture.
for bay in range(0, 12, 2):
    a = bay * math.pi / 6
    path = arch(1.10, .56, 3.53, 4.31, 40)
    line = [path[0]] + list(reversed(path[2:])) + [path[1]]
    profile_sweep('V4 | window carved stone archivolt', a, line, 4.00,
                  [(0, .020), (.012, .030), (.025, .072), (.045, .080),
                   (.064, .050), (.085, .025), (.105, .035), (.125, .025)], stone, '21')
    CV('V4 | window outer bronze reed', a,
       [[(x, 3.955, z) for x, z in line]], .012, bronze, '21')
    for sign in [-1, 1]:
        C('V4 | jamb foot block', a, sign * .62, 3.976, .64, .17, .20, .23, stone, '21', .012)
        C('V4 | jamb foot gilt fillet', a, sign * .62, 3.87, .73, .17, .013, .012, edge, '21', .003)
    # Recessed panels beneath each window continue the cabinet plinth rhythm.
    for xc in [-.37, 0, .37]:
        C('V4 | window dado recessed field', a, xc, 3.963, .27, .32, .018, .27, burled, '21', .008)
        frame('V4 | window dado raised frame', a, xc, 3.934, .27, .33, .28, wood, '21', .016)
        veins = []
        for k in range(-2, 3):
            veins.append(bez([(xc, 3.943, .16), (xc + k * .014, 3.943, .25),
                              (xc + k * .05, 3.943, .26),
                              (xc + k * .056, 3.943, .35 - abs(k) * .014)], 18))
        CV('V4 | dado five-branch gilt marquetry', a, veins, .0028, gold, '21')
        facade_leaf(a, 'V4 | dado fine central leaf',
                    [(xc, 3.939, .27), (xc - .008, 3.939, .3),
                     (xc + .006, 3.939, .33), (xc, 3.939, .36)], .027, edge, '21')

# Material scale follows the long column shaft instead of stretching a square
# procedural pattern over its full height. Blue occurs in mineral plates.
def noise_node(nodes, links, vector, scale, detail=4):
    node = nodes.new('ShaderNodeTexNoise')
    node.inputs['Scale'].default_value = scale
    node.inputs['Detail'].default_value = detail
    links.new(vector, node.inputs['Vector'])
    return node


def ramp(nodes, links, source, stops):
    node = nodes.new('ShaderNodeValToRGB')
    node.color_ramp.elements.remove(node.color_ramp.elements[-1])
    for i, (position, color) in enumerate(stops):
        e = node.color_ramp.elements[0] if i == 0 else node.color_ramp.elements.new(position)
        e.position = position
        e.color = (*color, 1)
    links.new(source, node.inputs[0])
    return node


n, l = lab.node_tree.nodes, lab.node_tree.links
n.clear()
out = n.new('ShaderNodeOutputMaterial')
bs = n.new('ShaderNodeBsdfPrincipled')
l.new(bs.outputs[0], out.inputs['Surface'])
bs.inputs['Metallic'].default_value = .16
bs.inputs['Roughness'].default_value = .26
bs.inputs['Coat Weight'].default_value = .28
bs.inputs['Coat Roughness'].default_value = .19
tc = n.new('ShaderNodeTexCoord')
mapping = n.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
mapping.inputs[1].default_value = (1, 1, 7.5)
l.new(tc.outputs['Generated'], mapping.inputs[0])
noise = noise_node(n, l, mapping.outputs[0], 4, 5)
base = ramp(n, l, noise.outputs['Fac'], [(.20, (.005, .012, .014)),
             (.43, (.014, .029, .028)), (.58, (.043, .071, .063)),
             (.70, (.14, .15, .112)), (.83, (.22, .23, .18))])
warp = noise_node(n, l, mapping.outputs[0], 3.3, 5)
warp_scale = n.new('ShaderNodeVectorMath'); warp_scale.operation = 'SCALE'
warp_scale.inputs[3].default_value = .32; l.new(warp.outputs['Color'], warp_scale.inputs[0])
warped = n.new('ShaderNodeVectorMath'); warped.operation = 'ADD'
l.new(mapping.outputs[0], warped.inputs[0]); l.new(warp_scale.outputs[0], warped.inputs[1])
vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 9
l.new(warped.outputs[0], vor.inputs['Vector'])
sep = n.new('ShaderNodeSeparateColor'); l.new(vor.outputs['Color'], sep.inputs[0])
plate = ramp(n, l, sep.outputs[0], [(.65, (0, 0, 0)), (.84, (.025, .025, .025)),
             (.95, (.45, .45, .45)), (1, (.75, .75, .75))])
mask = n.new('ShaderNodeMath'); mask.operation = 'MULTIPLY'
l.new(plate.outputs[0], mask.inputs[0]); l.new(noise.outputs['Fac'], mask.inputs[1])
mix = n.new('ShaderNodeMixRGB'); l.new(mask.outputs[0], mix.inputs[0])
l.new(base.outputs[0], mix.inputs[1]); mix.inputs[2].default_value = (.016, .11, .19, 1)
l.new(mix.outputs[0], bs.inputs['Base Color'])
micro = noise_node(n, l, mapping.outputs[0], 95, 2)
bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .12
bump.inputs['Distance'].default_value = .0008
l.new(micro.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs[0], bs.inputs['Normal'])

for ma, is_burr in [(wood, False), (burled, True)]:
    n, l = ma.node_tree.nodes, ma.node_tree.links
    n.clear(); out = n.new('ShaderNodeOutputMaterial'); bs = n.new('ShaderNodeBsdfPrincipled')
    l.new(bs.outputs[0], out.inputs['Surface'])
    bs.inputs['Roughness'].default_value = .36
    bs.inputs['Coat Weight'].default_value = .20; bs.inputs['Coat Roughness'].default_value = .28
    tc = n.new('ShaderNodeTexCoord'); mapping = n.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (3, 3, 1.1) if is_burr else (5, 4, .65)
    l.new(tc.outputs['Generated'], mapping.inputs[0])
    noise = noise_node(n, l, mapping.outputs[0], 4.5, 5)
    noise.inputs['Distortion'].default_value = 2.4 if is_burr else .8
    colors = ramp(n, l, noise.outputs['Fac'], [(.20, (.009, .004, .002)),
                     (.39, (.024, .010, .004)), (.57, (.065, .027, .010)),
                     (.73, (.125, .059, .022)), (.88, (.19, .094, .037))])
    l.new(colors.outputs[0], bs.inputs['Base Color'])
    bump = n.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = .0002
    bump.inputs['Strength'].default_value = .08
    l.new(noise.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs[0], bs.inputs['Normal'])

for ma, color, rough in [(gold, (.39, .235, .080, 1), .34), (edge, (.64, .425, .15, 1), .27)]:
    bs = ma.node_tree.nodes['Principled BSDF']
    for link in list(bs.inputs['Base Color'].links): ma.node_tree.links.remove(link)
    bs.inputs['Base Color'].default_value = color
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = .80

# Inscriptions sit in their own flat fascia with measured margins. Their
# plane is forward of the cornice, safely above the capitals and case crowns.
inscriptions = []
for ob in list(S.objects):
    if ob.type != 'FONT': continue
    if ob.name.startswith(('V3 | large gold topic', 'Frieze |')):
        a = math.atan2(ob.location.y, ob.location.x)
        ob.name = ob.name.replace('V3', 'V4')
        ob.location = P(a, 0, 3.643, 4.642)
        ob.scale = (1, 1, 1)
        ob.data.align_y = 'CENTER'; ob.data.size = .205; ob.data.space_character = 1.04
        bpy.context.view_layer.update()
        width = max(v[0] for v in ob.bound_box) - min(v[0] for v in ob.bound_box)
        if width > 1.60: ob.scale = (1.60 / width,) * 3
        C('V4 | inscription recessed plaque', a, 0, 3.78, 4.642, 1.98, .24, .206, inset, '22', .009)
        for z in [4.521, 4.763]:
            C('V4 | projecting fascia moulding', a, 0, 3.80, z, 2.15, .35, .026, dark, '22', .009)
            C('V4 | fascia gilt pencil edge', a, 0, 3.622, z, 2.15, .010, .008, edge, '22', .003)
        # Borders stay outside the text safe area, with no flourishes in it.
        for z in [4.542, 4.742]:
            C('V4 | inscription fine border', a, 0, 3.648, z, 1.99, .012, .006, gold, '22', .002)
        bpy.context.view_layer.update()
        w = (max(v[0] for v in ob.bound_box) - min(v[0] for v in ob.bound_box)) * ob.scale.x
        h = (max(v[1] for v in ob.bound_box) - min(v[1] for v in ob.bound_box)) * ob.scale.y
        inscriptions.append({'text': ob.data.body, 'width_m': w, 'height_m': h,
                             'horizontal_padding_m': (1.98 - w) / 2,
                             'vertical_padding_m': (.206 - h) / 2})
    elif ob.name.startswith('Rotunda |'):
        ob.data.align_y = 'CENTER'
        ob.location.z = 5.115
    elif ob.name == 'Library interface | carved lintel':
        ob.data.body = 'RESOURCES & RESEARCH'
        ob.data.size = .068
        ob.data.align_y = 'CENTER'
        ob.location.z = 2.325

# Bring the original fine upper-cornice ornament to the projecting fascia's
# front so its running honeysuckle remains visible from a standing viewpoint.
for ob in collections['15'].objects:
    if not any(s in ob.name for s in ['cornice running honeysuckle', 'cornice bud']): continue
    if ob.type == 'CURVE':
        for sp in ob.data.splines:
            for p in sp.points:
                r = math.hypot(p.co.x, p.co.y)
                p.co.x *= (r - .18) / r; p.co.y *= (r - .18) / r
    elif ob.type == 'MESH':
        for v in ob.data.vertices:
            r = math.hypot(v.co.x, v.co.y)
            if r > 1: v.co.x *= (r - .18) / r; v.co.y *= (r - .18) / r

# More directional daylight reveals the new relief without luminous glass.
for ob in S.objects:
    if ob.type == 'LIGHT' and '| daylight' in ob.name:
        ob.data.energy = 380
S.world.color = (.12, .12, .12)
S.view_settings.exposure = .10
S.camera = bpy.data.objects['01 | Entrance interior']
craft = bpy.data.objects['09 | V3 craftsmanship']; craft.name = '09 | V4 craftsmanship'
collections['11'].hide_render = True; collections['11'].hide_viewport = True
S['version'] = '4.0 | sculpted craftsmanship and padded inscriptions'
S['v4_detail_notes'] = 'Preserved V3 acanthus, ferns, fans, rosettes and scrolls; fitted leaf-edge chasing and twisted fillets; deeper ogee shelf arches, corbels, recessed burr panels and stone archivolts; padded inscription fascias.'
S['books'] = 0
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file: im.pack()
S.render.resolution_x = 1800; S.render.resolution_y = 1440
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'XR_Guild_Library_v4.blend'), compress=True)
report = {'version': 4, 'width_m': 8, 'apex_m': 6.2, 'books': 0,
          'empty_shelf_meshes': sum('empty shelf' in o.name or 'empty side shelf' in o.name for o in S.objects),
          'replaced_objects': len(removed), 'objects': len(S.objects),
          'new_detail_objects': {c: len(collections[c].objects) for c in ['19', '20', '21', '22']},
          'inscriptions': inscriptions, 'source_v3_unchanged': True}
(ROOT / 'evidence/build_manifest.json').write_text(json.dumps(report, indent=2) + '\n')
print('V4_BUILD_COMPLETE', json.dumps(report), flush=True)
