# まめすけアナ 3DCG（Blender 4.2 / Cycles CPU）
# 使い方: blender -b -P cg/mamesuke.py -- <chunk> <nchunks>
import bpy, sys, json, math, os, time, wave
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
CHUNK, NCH = int(argv[0]), int(argv[1])
JOB = json.load(open("cg/job.json"))
FPS = 24

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS

# ---------------- materials ----------------
def P(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

def HAIR(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    try: h.parametrization = 'COLOR'
    except Exception: pass
    h.inputs["Color"].default_value = (*color, 1)
    h.inputs["Roughness"].default_value = 0.5
    if "Radial Roughness" in h.inputs: h.inputs["Radial Roughness"].default_value = 0.7
    nt.links.new(h.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

WHITE_C, TAN_C = (0.86, 0.82, 0.74), (0.62, 0.40, 0.20)
M_WHITE, M_TAN = P("white", WHITE_C, 0.9), P("tan", TAN_C, 0.9)
H_WHITE, H_TAN = HAIR("h_white", (0.93, 0.90, 0.84)), HAIR("h_tan", (0.66, 0.44, 0.24))
M_EYE = P("eye", (0.012, 0.008, 0.006), 0.03)
M_NOSE = P("nose", (0.01, 0.01, 0.01), 0.25)
M_MOUTH = P("mouth", (0.10, 0.02, 0.025), 0.6)
M_TONGUE = P("tongue", (0.85, 0.36, 0.42), 0.4)
M_SUIT = P("suit", (0.012, 0.014, 0.022), 0.75)
M_SHIRT = P("shirt", (0.9, 0.9, 0.9), 0.6)
M_TIE = P("tie", (0.55, 0.02, 0.04), 0.45)
M_DESK = P("desk", (0.55, 0.68, 0.80), 0.06, 0.7)
M_DARK = P("dark", (0.01, 0.015, 0.04), 0.3)
M_MIC = P("mic", (0.03, 0.03, 0.03), 0.4, 0.8)

# ---------------- helpers ----------------
def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.location = loc; e.parent = parent
    return e

def sph(name, loc, scale, mats, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    o.rotation_euler = rot
    for m in mats: o.data.materials.append(m)
    o.parent = parent
    return o

def box(name, loc, scale, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat); o.parent = parent
    return o

def mask(o, excl):
    vg = o.vertex_groups.new(name="dens"); off = Vector(o.location)
    for v in o.data.vertices:
        p = off + v.co; w = 1.0
        for c, r in excl:
            d = (p - Vector(c)).length
            w = min(w, max(0.0, min(1.0, (d - r) / (r * 0.5))))
        vg.add([v.index], w, 'REPLACE')
    return vg.name

def fur(o, n, length, align=(0, 0, 0), child=22, rad=0.0028, clump=0.35, rough=0.02, excl=None, seed=1, normal=1.0):
    md = o.modifiers.new("fur", "PARTICLE_SYSTEM"); ps = md.particle_system; s = ps.settings
    s.type = 'HAIR'; s.count = n; s.hair_length = length; s.use_advanced_hair = True
    s.normal_factor = normal; s.object_align_factor = align
    s.child_type = 'INTERPOLATED'; s.child_nbr = child; s.rendered_child_count = child
    s.clump_factor = clump; s.roughness_1 = rough; s.roughness_1_size = 0.4; s.roughness_endpoint = 0.03
    s.hair_step = 5; s.render_step = 4; s.display_step = 3
    s.root_radius = 1.0; s.tip_radius = 0.15; s.radius_scale = rad
    s.material = 2; ps.seed = seed
    if excl:
        g = mask(o, excl); ps.vertex_group_density = g; ps.vertex_group_length = g
    o.show_instancer_for_render = True

# ---------------- character ----------------
HEADZ = 1.50
head = empty("head", (0, -0.05, HEADZ))
EYE_L, EYE_R = (0.19, -0.415, 0.05), (-0.19, -0.415, 0.05)
NOSE = (0, -0.625, -0.07)
EX_FACE = [(EYE_L, 0.12), (EYE_R, 0.12), (NOSE, 0.08)]

core = sph("core", (0, 0, 0), (0.50, 0.46, 0.46), [M_WHITE, H_WHITE], head)
fur(core, 2600, 0.09, (0, 0.15, -0.1), excl=EX_FACE, seed=1)
for sx, nm in ((1, "L"), (-1, "R")):
    p = sph("patch" + nm, (0.29 * sx, -0.10, 0.08), (0.24, 0.38, 0.36), [M_TAN, H_TAN], head)
    fur(p, 2200, 0.085, (0.1 * sx, 0.1, -0.15), excl=EX_FACE, seed=2 + (sx > 0))
    ear = sph("ear" + nm, (0.53 * sx, 0.03, -0.14), (0.15, 0.20, 0.34), [M_TAN, H_TAN], head, rot=(0, -0.22 * sx, 0))
    fur(ear, 1800, 0.20, (0.05 * sx, 0, -0.9), child=30, clump=0.5, rough=0.035, seed=5 + (sx > 0), normal=0.6)
    eye = sph("eye" + nm, EYE_L if sx > 0 else EYE_R, (0.085, 0.085, 0.085), [M_EYE], head)
EARS = [bpy.data.objects["earL"], bpy.data.objects["earR"]]

# eyelids: upper hemisphere, rotate about X (10deg open .. 95deg closed)
LIDS = []
for nm, loc in (("L", EYE_L), ("R", EYE_R)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.093, location=loc)
    o = bpy.context.active_object; o.name = "lid" + nm
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in o.data.vertices: v.select = v.co.z < -0.001
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth(); o.data.materials.append(M_TAN); o.parent = head
    LIDS.append(o)

muzzle = sph("muzzle", (0, -0.44, -0.15), (0.27, 0.20, 0.17), [M_WHITE, H_WHITE], head)
fur(muzzle, 2400, 0.085, (0, -0.15, -0.45), clump=0.45, excl=[(NOSE, 0.07), (EYE_L, 0.12), (EYE_R, 0.12), ((0, -0.56, -0.31), 0.10)], seed=8)
sph("nose", NOSE, (0.075, 0.05, 0.055), [M_NOSE], head)

jaw = empty("jaw", (0, -0.30, -0.25), head)
chin = sph("chin", (0, -0.21, -0.035), (0.165, 0.16, 0.06), [M_WHITE, H_WHITE], jaw)
fur(chin, 900, 0.06, (0, -0.1, -0.5), excl=[((0, -0.24, 0.03), 0.13)], seed=9)
sph("mouth_in", (0, -0.19, -0.005), (0.145, 0.15, 0.045), [M_MOUTH], jaw)
sph("tongue", (0, -0.25, 0.025), (0.075, 0.10, 0.022), [M_TONGUE], jaw)

# body (world coords)
sph("torso", (0, 0.03, 0.74), (0.43, 0.30, 0.50), [M_SUIT])
sph("shirt", (0, -0.19, 0.88), (0.15, 0.11, 0.30), [M_SHIRT])
sph("tie", (0, -0.295, 0.84), (0.05, 0.025, 0.20), [M_TIE])
sph("knot", (0, -0.30, 1.05), (0.05, 0.035, 0.045), [M_TIE])
ruff = sph("ruff", (0, -0.03, 1.13), (0.33, 0.27, 0.16), [M_WHITE, H_WHITE])
fur(ruff, 1500, 0.09, (0, -0.1, -0.5), seed=11)
for sx in (1, -1):
    sph("arm", (0.31 * sx, -0.30, 0.60), (0.105, 0.30, 0.10), [M_SUIT])
    sph("cuff", (0.31 * sx, -0.57, 0.585), (0.10, 0.05, 0.092), [M_SHIRT])
    paw = sph("paw", (0.31 * sx, -0.66, 0.565), (0.10, 0.11, 0.07), [M_WHITE, H_WHITE])
    fur(paw, 700, 0.035, (0, -0.2, -0.1), seed=12 + (sx > 0))

# ---------------- set ----------------
box("desk", (0, -0.75, 0.47), (1.7, 0.55, 0.03), M_DESK)
box("deskfront", (0, -1.28, 0.20), (1.7, 0.02, 0.25), M_DARK)
box("strip", (0, -1.305, 0.36), (1.7, 0.005, 0.012), P("strip", (0, 0, 0), 0.5, 0, (0.2, 0.5, 1.0), 6))
box("floor", (0, 0, -0.06), (8, 8, 0.01), P("floor", (0.02, 0.03, 0.06), 0.15, 0.3))
box("wall", (0, 3.2, 2.0), (6, 0.05, 3), P("wall", (0.01, 0.02, 0.06), 0.6))
import random
random.seed(4)
for i in range(7):
    x = -3.3 + i * 1.1
    c = random.choice([(0.05, 0.25, 0.9), (0.1, 0.45, 1.0), (0.3, 0.6, 1.0)])
    box(f"scr{i}", (x, 3.1, 1.4 + 0.5 * random.random()), (0.45, 0.02, 0.5 + 0.4 * random.random()), P(f"scr{i}", (0, 0, 0), 0.5, 0, c, 1.5 + 2 * random.random()))
box("band", (0, 3.05, 2.75), (5, 0.02, 0.03), P("band", (0, 0, 0), 0.5, 0, (0.5, 0.75, 1.0), 8))
bpy.ops.object.text_add(location=(0, 3.0, 3.0), rotation=(math.pi / 2, 0, 0))
t = bpy.context.active_object; t.data.body = "MAMESUKE NEWS"; t.data.align_x = 'CENTER'; t.data.size = 0.42; t.data.extrude = 0.01
t.data.materials.append(P("txt", (0, 0, 0), 0.5, 0, (1, 1, 1), 4))
# microphone
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.36, location=(0.62, -0.80, 0.66), rotation=(0.35, 0, 0))
bpy.context.active_object.data.materials.append(M_MIC)
sph("michead", (0.62, -0.865, 0.84), (0.04, 0.04, 0.055), [M_MIC])

w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.02, 0.05, 1)

target = empty("target", (0, 0, 1.38))
def light(name, loc, power, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc
    c = o.constraints.new('TRACK_TO'); c.target = target; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
light("key", (-1.8, -3.2, 3.0), 700, 2.5, (1.0, 0.96, 0.9))
light("fill", (2.2, -2.6, 1.6), 220, 3.0, (0.85, 0.92, 1.0))
light("rimL", (-1.6, 1.6, 2.6), 500, 1.0, (0.4, 0.65, 1.0))
light("rimR", (1.6, 1.6, 2.6), 500, 1.0, (0.4, 0.65, 1.0))

cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam)
cam.location = (0, -4.3, 1.30); cam_d.lens = 50
ct = empty("camt", (0, 0, 1.08))
c = cam.constraints.new('TRACK_TO'); c.target = ct; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
cam_d.dof.use_dof = True; cam_d.dof.focus_object = head; cam_d.dof.aperture_fstop = 2.0
sc.camera = cam

# ---------------- animation ----------------
OPENV = {"a": 1.0, "o": 0.72, "e": 0.6, "i": 0.36, "u": 0.3, "N": 0.12, "cl": 0.04, "pau": 0.0}
vp = JOB["voice"]
wv = wave.open(vp + ".wav"); VDUR = wv.getnframes() / wv.getframerate()
q = json.load(open(vp + ".json", encoding="utf-8"))
LEAD, TAIL = 0.5, 0.9
segs = [(q["prePhonemeLength"], 0.0)]
for ap in q["accent_phrases"]:
    for m in ap["moras"]:
        v = m["vowel"]; red = 0.55 if v in "AIUEO" else 1.0; o = OPENV.get(v.lower() if v in "AIUEO" else v, 0.4) * red
        cns = m.get("consonant")
        if cns: segs.append((m["consonant_length"], 0.0 if cns in ("m", "b", "p", "my", "by", "py") else 0.5 * o))
        segs.append((m["vowel_length"], o))
    if ap.get("pause_mora"): segs.append((ap["pause_mora"]["vowel_length"], 0.0))
segs.append((q["postPhonemeLength"], 0.0))
k = VDUR / sum(s[0] for s in segs)
HZ = 240; TOTAL = LEAD + VDUR + TAIL; N = int(TOTAL * FPS)
raw = [0.0] * (int(TOTAL * HZ) + 1); t_ = LEAD
for d, o in segs:
    for i in range(int(t_ * HZ), min(len(raw), int((t_ + d * k) * HZ))): raw[i] = o
    t_ += d * k
def smooth(x, r):
    out = []
    for i in range(len(x)):
        a, b = max(0, i - r), min(len(x), i + r + 1); out.append(sum(x[a:b]) / (b - a))
    return out
raw = smooth(smooth(raw, 7), 7)
OPEN = [raw[min(len(raw) - 1, int((f + 0.5) / FPS * HZ))] for f in range(N + 1)]
SLOW = smooth(OPEN, 5)
REST = 0.10                                   # mouth slightly open at rest (friendly look)
blinks = [int(1.3 * FPS), int((LEAD + VDUR + 0.25) * FPS)]
def lid_at(f):
    a = 12.0
    for b in blinks:
        d = f - b
        if 0 <= d < 6: a = max(a, [50, 92, 95, 80, 45, 20][d])
    return a
for f in range(N + 1):
    t = f / FPS
    end = max(0.0, min(1.0, (t - (LEAD + VDUR)) / 0.4))          # after the line: happy open mouth
    op = max(OPEN[f], REST + 0.35 * end)
    jaw.rotation_euler = (math.radians(20 * op), 0, 0); jaw.keyframe_insert("rotation_euler", frame=f)
    nod = 2.5 * SLOW[f] + 1.2 * math.sin(t * 1.3)
    tilt = 4.0 * math.sin(t * 0.9 + 0.5) + 5.0 * end
    yaw = 3.0 * math.sin(t * 0.6)
    head.rotation_euler = (math.radians(nod), math.radians(tilt), math.radians(yaw)); head.keyframe_insert("rotation_euler", frame=f)
    for i, e in enumerate(EARS):
        sx = 1 if i == 0 else -1
        lag = 4.0 * math.sin((t - 0.12) * 0.9 + 0.5) + 5.0 * end      # ears trail the head tilt
        e.rotation_euler = (0, -0.22 * sx - math.radians(0.5 * (tilt - lag) * 2), 0); e.keyframe_insert("rotation_euler", frame=f)
    for l in LIDS:
        l.rotation_euler = (math.radians(lid_at(f)), 0, 0); l.keyframe_insert("rotation_euler", frame=f)
sc.frame_start, sc.frame_end = 0, N
print("FRAMES", N, "DUR", TOTAL)

# ---------------- render ----------------
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = JOB.get("samples", 48); sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.render.resolution_x, sc.render.resolution_y = JOB.get("res", [720, 1280]); sc.render.resolution_percentage = 100
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'PNG'
frames = list(range(N + 1)) if JOB["frames"] == "all" else JOB["frames"]
os.makedirs("cg/out", exist_ok=True)
json.dump({"n": N, "fps": FPS, "lead": LEAD, "total": TOTAL}, open(f"cg/out/meta_{CHUNK}.json", "w"))
for i, f in enumerate(frames):
    if i % NCH != CHUNK or f > N: continue
    t0 = time.time(); sc.frame_set(f)
    sc.render.filepath = os.path.abspath(f"cg/out/f_{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", f, round(time.time() - t0, 1), "s", flush=True)
