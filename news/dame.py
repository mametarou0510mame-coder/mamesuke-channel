import math, subprocess, sys, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

sys.path.insert(0, "/home/claude/mamesuke-channel/content")
from dame_foods import FOODS, ACTIONS, LONG, SHORT

D = "/tmp/claude-0/-home-claude/f9d7791f-8b10-5d2c-984e-107435ad121f/scratchpad/suit"
A = "/mnt/user-data/attachments/f9d7791f-8b10-5d2c-984e-107435ad121f"
VROOT = "/home/claude/mamesuke-channel/voices"
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FE = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
def font(sz, b=True): return ImageFont.truetype(FB if b else FM, sz, index=0)
FPS = 30
NAVY = (14, 30, 72); RED = (205, 32, 50); WHITE = (255, 255, 255); INK = (25, 25, 35); GOLD = (255, 200, 50)
rng = np.random.default_rng(5)

# ---------------- emoji / icons ----------------
EFONT = ImageFont.truetype(FE, 109)
def emoji(ch, size):
    if ch == "MAC":  # macadamia: round cream nuts (🥜 would be a peanut)
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for cx, cy, r in [(110, 170, 78), (200, 150, 70), (165, 225, 62)]:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(222, 196, 150), outline=(170, 130, 80), width=6)
            d.ellipse([cx - r * 0.5, cy - r * 0.6, cx - r * 0.1, cy - r * 0.25], fill=(250, 236, 205))
        return im.resize((size, size), Image.LANCZOS)
    im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((70, 70), ch, font=EFONT, embedded_color=True, anchor="mm")
    return im.resize((size, size), Image.LANCZOS)
ICON = {i: ("MAC" if f[1] == "マカダミアナッツ" else f[0]) for i, f in enumerate(FOODS)}

# ---------------- anchor source + mouth rig (source coords) ----------------
SRC = np.asarray(Image.open(f"{A}/03b87551-image.jpg").convert("RGB"), np.float32)
ML, MCX, JCY, RX, RY, MHW = 603.0, 393.0, 632.0, 62.0, 50.0, 34.0
x0, y0, x1, y1 = 293, 540, 493, 720
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
r = np.sqrt(((xx - MCX) / RX) ** 2 + ((yy - JCY) / RY) ** 2)
WJ = cv2.GaussianBlur(((np.clip(1.25 - r, 0, 1) ** 0.8) * (yy >= ML)).astype(np.float32), (0, 0), 1.8) * (yy >= ML)
MW = (np.clip(1 - np.abs(xx - MCX) / MHW, 0, 1) ** 0.7).astype(np.float32)
PATCH = SRC[y0:y1, x0:x1].copy()
def anchor_src(openpx):
    fr = SRC.copy()
    if openpx < 0.3: return fr
    dy = WJ * np.float32(openpx)
    out = cv2.remap(PATCH, (xx - x0).astype(np.float32), (yy - dy - y0).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    gap = cv2.GaussianBlur((((yy >= ML) & (yy - dy < ML)).astype(np.float32) * MW), (0, 0), 1.0)[..., None]
    k = np.clip((yy - ML) / max(openpx, 1), 0, 1)[..., None]
    inner = np.array([40, 16, 20], np.float32) * (1 - k) + np.array([175, 78, 92], np.float32) * k
    fr[y0:y1, x0:x1] = out * (1 - gap) + inner * gap
    return fr

# ---------------- audio timeline ----------------
def timeline(rows, folder, lead=0.12, gap=0.28, tail_end=1.4):
    clips = []
    for lid, *_ in rows:
        w = wave.open(f"{VROOT}/{folder}/{lid}.wav"); SR = w.getframerate()
        clips.append(np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768)
    durs = [lead + len(c) / SR + gap for c in clips]
    durs[-1] += tail_end
    total = sum(durs)
    aud = np.zeros(int(total * SR) + SR, np.float32); starts = []; t = 0
    for c, d in zip(clips, durs):
        s = int((t + lead) * SR); aud[s:s + len(c)] += c; starts.append(t); t += d
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(aud[f*hop:(f+1)*hop] ** 2)) if f * hop < len(aud) else 0 for f in range(int(total * FPS) + 3)])
    env = np.nan_to_num(np.clip(env / (np.percentile(env[env > 0.01], 85) + 1e-6), 0, 1.15))
    env = np.convolve(env, [0.2, 0.6, 0.2], mode="same")
    path = f"{D}/{folder}.wav"
    aw = wave.open(path, "wb"); aw.setnchannels(1); aw.setsampwidth(2); aw.setframerate(SR)
    aw.writeframes((np.clip(aud, -1, 1) * 32767).astype(np.int16).tobytes()); aw.close()
    return durs, starts, env, path

def rgba_np(im): a = np.asarray(im, np.float32); return a[..., :3], a[..., 3:] / 255

def wrap(text, f, maxw, d):
    """pack phrases (split after 、。」！？) greedily; split long phrases by character with kinsoku"""
    import re
    W_ = lambda t: d.textlength(t, font=f)
    chunks = [c for c in re.split(r"(?<=[、。」！？])", text) if c]
    lines, cur = [], ""
    def push_chars(seg):
        nonlocal cur
        for ch in seg:
            if W_(cur + ch) > maxw and cur:
                if ch in "、。」）！？…ー":       # kinsoku: carry the last char down with it
                    lines.append(cur[:-1]); cur = cur[-1] + ch
                else:
                    lines.append(cur); cur = ch
            else:
                cur += ch
    for c in chunks:
        if W_(cur + c) <= maxw: cur += c
        elif W_(c) <= maxw:
            if cur: lines.append(cur)
            cur = c
        else:
            push_chars(c)
    if cur: lines.append(cur)
    return lines

def writer(path, W, H, audio):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-i", audio, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", path], stdin=subprocess.PIPE)

def photo_fit(path, W, H, box, focus=(0.5, 0.45)):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    bg = np.asarray(ImageOps.fit(im, (W // 12, H // 12)).resize((W, H), Image.BICUBIC), np.float32) * 0.45
    bx, by, bw, bh = box
    fg = np.asarray(ImageOps.fit(im, (bw, bh), centering=focus), np.float32)
    return bg, fg, box

def photo_frame(pl, t, dur, push=0.08):
    bg, fg, (bx, by, bw, bh) = pl
    z = 1 + push * min(1, t / max(dur, 0.1))
    w2, h2 = int(bw * z), int(bh * z)
    f = cv2.resize(fg, (w2, h2)); ox, oy = (w2 - bw) // 2, (h2 - bh) // 2
    out = bg.copy(); out[by:by + bh, bx:bx + bw] = f[oy:oy + bh, ox:ox + bw]
    return out

def scene_spans(rows, starts, durs):
    """group consecutive rows by scene -> {row_index: (scene_start, scene_dur, index_within_scene, n_in_scene)}"""
    info = {}; i = 0
    while i < len(rows):
        j = i
        while j + 1 < len(rows) and rows[j + 1][1] == rows[i][1]: j += 1
        st = starts[i]; du = sum(durs[i:j + 1])
        for k in range(i, j + 1): info[k] = (st, du, k - i, j - i + 1)
        i = j + 1
    return info
