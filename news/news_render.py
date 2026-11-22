import os
from dame import *   # font, emoji, wrap, rgba_np, writer, photo_fit, photo_frame, colours, FPS, A, D
sys.path.insert(0, "/home/claude/mamesuke-channel/content")
import importlib
EP = sys.argv[1]
STRIKE = importlib.import_module(EP).ROWS
from episodes import SPEC
SP = SPEC[EP]

E = "/tmp/claude-0/-home-claude/f9d7791f-8b10-5d2c-984e-107435ad121f/scratchpad/expr"
OUT = SP["out"]
W, H = 1080, 1920
SH, SW = SRC.shape[:2]

# ---------------- audio: chime + voices ----------------
SPEECH = []
def timeline_strike(rows, lead=0.12, gap=0.3, head=1.0, tail_end=1.6):
    clips = []
    for lid_, *_ in rows:
        w = wave.open(f"{VROOT}/{EP}/{lid_}.wav"); SR = w.getframerate()
        clips.append(np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768)
    durs = [lead + len(c) / SR + gap for c in clips]; durs[0] += head; durs[-1] += tail_end
    total = sum(durs); aud = np.zeros(int(total * SR) + SR, np.float32)
    # news chime "pon-pon-pon"
    for i, fq in enumerate([880, 1175, 1568]):
        t = np.arange(int(0.28 * SR)) / SR
        tone = (np.sin(2 * np.pi * fq * t) + 0.3 * np.sin(2 * np.pi * fq * 2 * t)) * np.exp(-t * 7) * 0.28
        s = int((0.05 + i * 0.22) * SR); aud[s:s + len(tone)] += tone
    starts = []; t = 0
    for i, (c, d) in enumerate(zip(clips, durs)):
        s = int((t + lead + (head if i == 0 else 0)) * SR); aud[s:s + len(c)] += c; starts.append(t); t += d; SPEECH.append((s / SR, len(c) / SR))
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(aud[f*hop:(f+1)*hop] ** 2)) if f * hop < len(aud) else 0 for f in range(int(total * FPS) + 3)])
    env[: int((head + lead) * FPS)] = 0  # no lip movement on the chime
    env = np.nan_to_num(np.clip(env / (np.percentile(env[env > 0.01], 85) + 1e-6), 0, 1.15))
    env = np.convolve(env, [0.2, 0.6, 0.2], mode="same")
    path = f"{D}/{EP}.wav"
    aw = wave.open(path, "wb"); aw.setnchannels(1); aw.setsampwidth(2); aw.setframerate(SR)
    aw.writeframes((np.clip(aud, -1, 1) * 32767).astype(np.int16).tobytes()); aw.close()
    return durs, starts, env, path
durs, starts, ENV, AUDIO = timeline_strike(STRIKE)
TOTAL = sum(durs)

# expression timeline (per frame) with crossfades; wink at the very end
NF = int(round(TOTAL * FPS))
expr = []
for ri, (lid_, ex, *_ ) in enumerate(STRIKE):
    n = int(round(durs[ri] * FPS))
    for f in range(n):
        t = f / FPS
        if lid_ == STRIKE[-1][0]:
            ex2 = "smile" if t < durs[ri] - 1.7 else "wink"
        else:
            ex2 = ex
        expr.append(ex2)
expr += [expr[-1]] * (NF + 5 - len(expr))

import anchor2 as AN, json
SH, SW = AN.SH, AN.SW
OPENV = {"a": 1.0, "o": 0.72, "e": 0.6, "i": 0.36, "u": 0.3, "N": 0.12, "cl": 0.04, "pau": 0.0}
WIDV = {"a": 1.0, "o": 0.8, "e": 1.08, "i": 1.14, "u": 0.76, "N": 0.95, "cl": 0.95, "pau": 1.0}
HZ = 240
M_OPEN = np.zeros(int(TOTAL * HZ) + HZ); M_WID = np.ones(len(M_OPEN))
for ri, (lid_, *_r) in enumerate(STRIKE):
    q = json.load(open(f"{VROOT}/{EP}/{lid_}.json", encoding="utf-8"))
    segs = [(q["prePhonemeLength"], 0.0, 1.0)]
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            v = m["vowel"]; red = 0.55 if v in "AIUEO" else 1.0; vl = v.lower() if v in "AIUEO" else v
            o, wd = OPENV.get(vl, 0.4) * red, WIDV.get(vl, 1.0)
            c = m.get("consonant")
            if c:
                co = 0.0 if c in ("m", "b", "p", "my", "by", "py") else (0.15 if c in ("f", "w") else 0.5 * o)
                segs.append((m["consonant_length"], co, wd))
            segs.append((m["vowel_length"], o, wd))
        if ap.get("pause_mora"): segs.append((ap["pause_mora"]["vowel_length"], 0.0, 1.0))
    segs.append((q["postPhonemeLength"], 0.0, 1.0))
    st, ln = SPEECH[ri]; k = ln / sum(x[0] for x in segs); t_ = st
    for dur_, o, wd in segs:
        i0, i1 = int(t_ * HZ), int((t_ + dur_ * k) * HZ); M_OPEN[i0:i1] = o; M_WID[i0:i1] = wd; t_ += dur_ * k
def _smooth(x, sig):
    r = int(sig * 3); g = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); return np.convolve(x, g / g.sum(), mode="same")
M_OPEN = _smooth(M_OPEN, HZ * 0.030); M_WID = _smooth(M_WID, HZ * 0.045)
NFR = len(expr)
F_OPEN = np.array([M_OPEN[min(int((i + 0.5) / FPS * HZ), len(M_OPEN) - 1)] for i in range(NFR)])
F_WID = np.array([M_WID[min(int((i + 0.5) / FPS * HZ), len(M_WID) - 1)] for i in range(NFR)])
_env = np.pad(np.asarray(ENV, float), (0, max(0, NFR - len(ENV))))[:NFR]
_loud = _smooth(_env, 3.0)
F_OPEN = F_OPEN * (0.7 + 0.3 * np.clip(_loud, 0, 1))          # louder syllables open a little more
_rng = np.random.default_rng(11)
P_FACE, P_BLINK, P_WINK, P_TILT, P_NOD, P_SWAY = AN.plan(expr, _loud, FPS, _rng)
def anchor_full(fi, e):
    i = min(fi, NFR - 1); face = P_FACE[i]
    lm = dict(AN.LM[face]); lm["mhw"] = lm["mhw"] * F_WID[i]
    img = AN.mouth(AN.FACES[face], lm, float(F_OPEN[i]))
    if P_WINK[i] > 0: img = AN.lid(img, lm["eyes"][1], P_WINK[i])
    elif P_BLINK[i] > 0: img = AN.lid(AN.lid(img, lm["eyes"][0], P_BLINK[i]), lm["eyes"][1], P_BLINK[i])
    Mx = cv2.getRotationMatrix2D(AN.PIVOT, P_TILT[i] + P_SWAY[i], 1.0 + P_NOD[i] * 0.0012); Mx[1, 2] += P_NOD[i] * 0.6
    hw = cv2.warpAffine(img, Mx, (SW, SH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mw = cv2.warpAffine(AN.SIL[face], Mx, (SW, SH), flags=cv2.INTER_LINEAR)[..., None]
    return AN.CLEANS[face] * (1 - mw) + hw * mw

S = W / SW; OY = (int(SH * S) - H) // 2
def plate(img):
    a = cv2.resize(img, (W, int(SH * S)), interpolation=cv2.INTER_CUBIC)
    return a[OY:OY + H]

# ---------------- graphics ----------------
def overlay_static():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([40, 100, 380, 168], fill=RED); d.text((60, 134), "まめすけNEWS", font=font(42), fill=WHITE, anchor="lm")
    d.text((396, 134), SP["note"], font=font(26, False), fill=(255, 255, 255, 210), anchor="lm")
    d.text((1040, 1885), "VOICEVOX:ずんだもん", font=font(24, False), fill=(255, 255, 255, 160), anchor="rb")
    return rgba_np(im)
STATIC = overlay_static()

CX0, CY0, CX1, CY1 = 40, 190, 1040, 580
def card(kind, flash=True):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([CX0, CY0, CX1, CY1], fill=(12, 24, 58, 238))
    mid = (CX0 + CX1) // 2
    def two(head, hc, ht, emo, l1, l2, l3=None):
        d.rectangle([CX0, CY0, CX1, CY0 + 70], fill=hc); d.text((mid, CY0 + 35), head, font=font(42), fill=ht, anchor="mm")
        im.alpha_composite(emoji(emo, 170), (CX0 + 50, CY0 + 120))
        d.text((CX0 + 250, CY0 + 170), l1, font=font(52), fill=WHITE, anchor="lm")
        d.text((CX0 + 250, CY0 + 255), l2, font=font(66), fill=GOLD, anchor="lm")
        if l3: d.text((CX0 + 250, CY0 + 335), l3, font=font(34, False), fill=(210, 220, 255), anchor="lm")
    spec = SP["cards"][kind]
    if spec[0] == "two": two(*spec[1:])
    elif spec[0] == "table":
        head, hc, ht, rows_ = spec[1:]
        d.rectangle([CX0, CY0, CX1, CY0 + 70], fill=hc); d.text((mid, CY0 + 35), head, font=font(42), fill=ht, anchor="mm")
        rh = (CY1 - CY0 - 90) // len(rows_)
        for k_, (emo, lab, val) in enumerate(rows_):
            y = CY0 + 80 + k_ * rh + rh // 2
            if k_: d.line([CX0 + 30, y - rh // 2, CX1 - 30, y - rh // 2], fill=(80, 100, 160), width=2)
            d.text((CX0 + 50, y), lab, font=font(44), fill=(210, 220, 255), anchor="lm")
            im.alpha_composite(emoji(emo, 64), (CX0 + 300, y - 32))
            d.text((CX0 + 400, y), val, font=font(50), fill=GOLD, anchor="lm")
    return rgba_np(im)

def placard(lines, w=420, h=300, rot=-8):
    im = Image.new("RGBA", (w + 80, h + 360), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([w // 2 + 25, h, w // 2 + 55, h + 350], fill=(160, 115, 70))
    d.rectangle([40, 10, w + 40, h], fill=(252, 250, 242), outline=(60, 60, 60), width=6)
    fs = 74 if max(len(l) for l in lines) <= 5 else 56
    for i, ln in enumerate(lines):
        d.text((w // 2 + 40, 10 + h // 2 + (i - (len(lines) - 1) / 2) * (fs + 14)), ln, font=font(fs), fill=RED if i == len(lines) - 1 else INK, anchor="mm")
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)

def broll_layer(kind):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    num, lab = BLAB[kind]
    f_ = font(46); wl = int(d.textlength(lab, font=f_))
    if num:
        d.rectangle([40, 1240, 140, 1330], fill=GOLD); d.text((90, 1285), num, font=font(60), fill=NAVY, anchor="mm")
        d.rectangle([140, 1240, 200 + wl, 1330], fill=RED); d.text((170, 1285), lab, font=f_, fill=WHITE, anchor="lm")
    else:
        d.rectangle([40, 1240, 100 + wl, 1330], fill=(30, 140, 80)); d.text((70, 1285), lab, font=f_, fill=WHITE, anchor="lm")
    return rgba_np(im)

def pirit(t):  # comic sound effect for the pouch opening
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if t < 1.3:
        s = 1 + 0.25 * max(0, 0.25 - t) * 4
        f = font(int(150 * s))
        d.text((560, 470), "ピリッ…", font=f, fill=GOLD, anchor="mm", stroke_width=10, stroke_fill=INK)
    return rgba_np(im)

def caption(text, y0=1400):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for sz in (50, 46, 42, 39):
        f = font(sz); lines = wrap(text, f, 950, d)
        if len(lines) <= 2: break
    d.rectangle([40, y0, 330, y0 + 56], fill=NAVY); d.text((62, y0 + 28), "まめすけアナ", font=font(34), fill=WHITE, anchor="lm")
    hb = 70 + 70 * (len(lines) - 1) + 40
    d.rectangle([40, y0 + 62, 1040, y0 + 62 + hb], fill=(255, 255, 255, 244)); d.rectangle([40, y0 + 62, 54, y0 + 62 + hb], fill=RED)
    for i, ln in enumerate(lines):
        d.text((76, y0 + 116 + i * 70), ln, font=f, fill=INK, anchor="lm")
    return rgba_np(im)

# b-roll sources
BLAB = {k: (v[2], v[3]) for k, v in SP["broll"].items()}
BSRC = {k: (v[0], v[1]) for k, v in SP["broll"].items()}
_unused = {"uwame": ("1", "上目づかいでおねだり"), "wet": ("2", "濡れると別の犬"), "fluffy": ("", "乾かすと元通り"),
        "tail": ("3", "しっぽがくるん"), "lap": ("4", "人のそばでくつろぐ"), "salon": ("5", "トリミング直後はお上品")}
_unused2 = {"uwame": ("b97ae8c4", (0.5, 0.5)), "wet": ("129bfa89", (0.5, 0.4)), "fluffy": ("c2b1c8d7", (0.5, 0.5)),
        "tail": ("19e940a4", (0.5, 0.5)), "lap": ("88264111", (0.5, 0.55)), "salon": ("39a1c6f1", (0.5, 0.4))}
WORK = "/tmp/claude-0/-home-claude/f9d7791f-8b10-5d2c-984e-107435ad121f/scratchpad/assets/work"
srcp = lambda i: f"{WORK}/{i}.jpg" if i.startswith("IMG_") else f"{A}/{i}-image.jpg"
BROLL = {k: photo_fit(srcp(v[0]), W, H, (0, 150, 1080, 1440), v[1]) for k, v in BSRC.items()}

yv, xv = np.mgrid[0:H, 0:W]
VIG = (1 - 0.28 * (((xv - W / 2) / (W * 0.8)) ** 2 + ((yv - H / 2) / (H * 0.8)) ** 2))[..., None].astype(np.float32)
CARDS = {}; BLAYERS = {}

ff = writer(OUT, W, H, AUDIO)
fi = 0
for ri, (lid_, ex, vis, cap, _) in enumerate(STRIKE):
    c = caption(cap); n = int(round(durs[ri] * FPS))
    for f in range(n):
        t = f / FPS; gt = starts[ri] + t
        e = ENV[min(fi, len(ENV) - 1)]
        layers = []
        if vis.startswith("broll"):
            kind = vis.split(":")[1]
            fr = photo_frame(BROLL[kind], t, durs[ri])
            if kind not in BLAYERS: BLAYERS[kind] = broll_layer(kind)
            layers.append(BLAYERS[kind])
        else:
            img = anchor_full(fi, e)
            fr = plate(img)
            z = 1 + 0.03 * (gt / TOTAL) + 0.004 * math.sin(gt * 1.1)
            M = np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H * 0.4]])
            fr = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            if ":" in vis:
                kind = vis.split(":")[1]
                flash = kind != "sokuho" or int(gt * 2.5) % 2 == 0
                key = (kind, flash)
                if key not in CARDS: CARDS[key] = card(kind, flash)
                cd = CARDS[key]; k = min(1, t / 0.18) if (ri == 0 or STRIKE[ri - 1][2] != vis) else 1
                off = int((1 - k) ** 2 * 300)
                layers.append((np.roll(cd[0], off, axis=1), np.roll(cd[1], off, axis=1) * k) if off else cd)
        layers.append(STATIC)
        if not (ri == 0 and t < 1.0):
            ks = min(1, (t - (1.0 if ri == 0 else 0)) / 0.12); layers.append((c[0], c[1] * max(0, ks)))
        fr = fr * VIG
        for rgb, al in layers: fr = fr * (1 - al) + rgb * al
        fr = fr + rng.normal(0, 2.0, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
        ff.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
        fi += 1
ff.stdin.close(); ff.wait()
print("done", round(TOTAL, 1))
