# Anchor animation engine v2: per-face landmarks, shaded jaw drop, head motion on a clean plate,
# blinks that hide expression switches, puzzled head-tilt, wink.
import numpy as np, cv2, math

E = "/tmp/claude-0/-home-claude/f9d7791f-8b10-5d2c-984e-107435ad121f/scratchpad/expr"

# measured landmarks (source coords of the 768x1376 anchor image)
LM = {
    "neutral": dict(eyes=[(335, 525, 18, 15), (446, 529, 19, 17)], mcx=392, ml=612, mhw=33, open=12.0, paint=True),
    "concern": dict(eyes=[(318, 540, 19, 15), (440, 543, 20, 16)], mcx=383, ml=620, mhw=34, open=12.0, paint=True),
    "puzzled": dict(eyes=[(336, 532, 21, 17), (458, 548, 18, 18)], mcx=390, ml=621, mhw=34, open=13.0, paint=True),
    "smile":   dict(eyes=[(337, 525, 19, 13), (446, 524, 17, 11)], mcx=392, ml=612, mhw=44, open=6.0, paint=False),
}
LM["wink"] = LM["smile"]

FACES = {k: np.load(f"{E}/full_{k}.npy") for k in ("neutral", "concern", "puzzled", "smile")}
FACES["wink"] = FACES["smile"]
SH, SW = FACES["neutral"].shape[:2]

# per-face head silhouettes; clean plate = studio with every head removed
SIL = {k: np.load(f"{E}/sil_{k}.npy").astype(np.float32) for k in ("neutral", "concern", "puzzled", "smile")}
SIL["wink"] = SIL["smile"]
U = np.maximum.reduce([SIL[k] for k in ("neutral", "concern", "puzzled", "smile")])
hole = cv2.dilate((U > 0.05).astype(np.uint8), np.ones((17, 17), np.uint8))
hole[668:] = 0
small = cv2.resize(FACES["neutral"].astype(np.uint8), None, fx=0.5, fy=0.5)
cp = cv2.inpaint(small, cv2.resize(hole, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST), 11, cv2.INPAINT_TELEA)
cp = cv2.GaussianBlur(cp, (0, 0), 2)
up = cv2.resize(cp, (SW, SH)).astype(np.float32)
HOLE = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 3)[..., None]
CLEANS = {k: FACES[k] * (1 - HOLE) + up * HOLE for k in FACES}   # body/neck from each face, head area = studio
PIVOT = (393.0, 705.0)

# --------- mouth ---------
RX0, RX1, RY0, RY1 = 280, 510, 560, 720
gy, gx = np.mgrid[RY0:RY1, RX0:RX1].astype(np.float32)
def mouth(img, lm, amt):
    """amt 0..1.2 -> jaw drop with soft shading"""
    o = lm["open"] * amt
    if o < 0.25: return img
    mcx, ml, mhw = lm["mcx"], lm["ml"], lm["mhw"]
    # lower jaw: full drop just under the lip line, fading toward the chin and the cheeks
    rl = np.sqrt(((gx - mcx) / (mhw * 1.9)) ** 2 + ((gy - (ml + 8)) / 62) ** 2)
    wl = np.clip(1.15 - rl, 0, 1) ** 0.9 * (gy >= ml)
    # upper lip: slight lift
    ru = np.sqrt(((gx - mcx) / (mhw * 1.6)) ** 2 + ((gy - ml) / 26) ** 2)
    wu = np.clip(1.0 - ru, 0, 1) * (gy < ml)
    dy = (wl * o - wu * o * 0.22).astype(np.float32)
    dy = cv2.GaussianBlur(dy, (0, 0), 1.5)
    patch = img[RY0:RY1, RX0:RX1]
    out = cv2.remap(patch, gx - RX0, gy - dy - RY0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # opening = output rows whose source crossed the lip line
    srcy = gy - dy
    lipw = np.clip(1 - np.abs(gx - mcx) / mhw, 0, 1) ** 0.6
    gap = ((gy >= ml - o * 0.22) & (srcy < ml) | (gy < ml) & (srcy >= ml)).astype(np.float32) * lipw
    gap = cv2.GaussianBlur(gap, (0, 0), 1.6)[..., None]
    if lm["paint"]:
        top = ml - o * 0.22
        k = np.clip((gy - top) / max(o * 1.2, 1), 0, 1)[..., None]
        inner = np.array([22, 10, 12], np.float32) * (1 - k) + np.array([80, 34, 40], np.float32) * k ** 2
        out = out * (1 - gap * 0.94) + inner * gap * 0.94
    # soft contact shadow under the upper lip and on the stretched chin
    sh = cv2.GaussianBlur(np.clip(dy / max(o, 1), 0, 1) * lipw, (0, 0), 4)[..., None]
    out = out * (1 - 0.18 * sh * min(1, o / 6))
    img = img.copy(); img[RY0:RY1, RX0:RX1] = out
    return img

# --------- eyelids ---------
def lid(img, eye, c):
    if c <= 0.02: return img
    cx, cy, rx, ry = eye
    pad = 8; X0, Y0, X1, Y1 = int(cx - rx - pad), int(cy - ry - 3 * ry), int(cx + rx + pad), int(cy + ry + pad)
    ey, ex = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    inside = (((ex - cx) / (rx + 1)) ** 2 + ((ey - cy) / (ry + 1)) ** 2) <= 1
    edge = cy - ry + c * (2 * ry + 2)
    m = (inside & (ey <= edge + (1 - ((ex - cx) / rx) ** 2) * 3 * c)).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 2.4)[..., None]
    src = img[Y0:Y1, X0:X1]
    fur = cv2.remap(img, ex, (cy - ry - 3 - 0.6 * np.maximum(ey - (cy - ry), 0)).astype(np.float32), cv2.INTER_LINEAR)
    shade = np.clip((ey - (cy - ry)) / (2 * ry), 0, 1)[..., None]
    fur = fur * (0.97 - 0.22 * shade)
    out = src * (1 - m) + fur * m
    lash = np.zeros(src.shape[:2], np.float32)
    ly = cy - ry + c * 1.45 * ry
    pts = [(int(x - X0), int(ly - Y0 + (1 - ((x - cx) / rx) ** 2) * 3 * c)) for x in np.linspace(cx - rx, cx + rx, 24)]
    cv2.polylines(lash, [np.array(pts, np.int32)], False, 1.0, 3, cv2.LINE_AA)
    lash = cv2.GaussianBlur(lash, (0, 0), 0.8)[..., None] * np.clip((c - 0.4) / 0.5, 0, 1)
    out = out * (1 - lash * 0.85) + np.array([35, 25, 20], np.float32) * lash * 0.85
    img = img.copy(); img[Y0:Y1, X0:X1] = out
    return img

# --------- planning ---------
BLINK_CURVE = [0.35, 0.8, 1.0, 1.0, 0.75, 0.4, 0.12]
def plan(expr, env, fps, rng, no_blink=()):
    """expr: list of expression names per frame. Returns per-frame (face, blink_c, wink_c, tilt_deg, nod_px, sway_deg)."""
    n = len(expr)
    env = np.pad(np.asarray(env, np.float64), (0, max(0, n - len(env))))[:n]
    # expression change frames -> blink centred there; face swaps on the closed frame
    blink = np.zeros(n)
    changes = [i for i in range(1, n) if expr[i] != expr[i - 1] and expr[i] != "wink"]
    starts = set()
    for c in changes: starts.add(max(0, c - 2))
    t = int(1.2 * fps)
    while t < n:
        if all(abs(t - s) > int(1.1 * fps) for s in starts): starts.add(t)
        t += int(rng.uniform(2.6, 4.4) * fps)
    for s in sorted(starts):
        for k, c in enumerate(BLINK_CURVE):
            if s + k < n: blink[s + k] = max(blink[s + k], c)
    # displayed face switches only when eyes are closed (or for the wink)
    face = []; cur = expr[0]
    for i in range(n):
        if expr[i] != cur and (blink[i] >= 0.95 or expr[i] == "wink"): cur = expr[i]
        face.append(cur)
    for i in no_blink:
        if i < n: blink[i] = 0
    # wink ramp
    wink = np.zeros(n)
    for i in range(n):
        if face[i] == "wink":
            j = i
            while j > 0 and face[j - 1] == "wink": j -= 1
            wink[i] = min(1, (i - j) / 5)
            blink[i] = 0
    # head motion
    envs = np.convolve(env[:n], np.ones(9) / 9, mode="same")          # slow speech energy
    tilt_target = np.array([6.5 if f == "puzzled" else (-4.5 if f in ("smile", "wink") else (4.0 if f == "concern" else 3.0)) for f in face])
    tilt = np.zeros(n); a = 0.0
    for i in range(n):
        a += (tilt_target[i] - a) * 0.12; tilt[i] = a
    tt = np.arange(n) / fps
    sway = 0.7 * np.sin(2 * np.pi * 0.11 * tt) + 0.45 * np.sin(2 * np.pi * 0.27 * tt + 1.3)
    sway += 1.1 * (env[:n] - envs)                                   # syllable accents
    nod = 3.0 * envs + 1.2 * np.sin(2 * np.pi * 0.19 * tt)           # px, positive = down
    nod += np.array([2.5 if f == "concern" else 0 for f in face])
    return face, blink, wink, tilt, nod, sway

def render_head(face, blink_c, wink_c, mouth_amt, tilt, nod, sway):
    lm = LM[face]
    img = FACES[face]
    img = mouth(img, lm, mouth_amt)
    if wink_c > 0:
        img = lid(img, lm["eyes"][1], wink_c)
    elif blink_c > 0:
        img = lid(lid(img, lm["eyes"][0], blink_c), lm["eyes"][1], blink_c)
    ang = tilt + sway
    M = cv2.getRotationMatrix2D(PIVOT, ang, 1.0 + nod * 0.0012)
    M[1, 2] += nod * 0.6
    hw = cv2.warpAffine(img, M, (SW, SH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mw = cv2.warpAffine(SIL[face], M, (SW, SH), flags=cv2.INTER_LINEAR)[..., None]
    base = CLEANS[face]
    return base * (1 - mw) + hw * mw
