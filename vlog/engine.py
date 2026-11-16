"""まめすけ日常動画の編集エンジン（縦 1080x1920 / 30fps）。
クリップ読み込み(ffmpeg) → Pythonで1フレームずつ ズーム/揺れ/色/テロップ/演出 → ffmpegで書き出し。
音は sound.py で BGM・効果音を合成し、ナレーション(VOICEVOX)と一緒にミックスする。"""
import json, math, os, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SCR = "/tmp/claude-0/-home-claude/f9d7791f-8b10-5d2c-984e-107435ad121f/scratchpad"
VID = f"{SCR}/assets/videos"
CAT = json.load(open(f"{SCR}/assets/catalog.json"))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FE = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
HDR_VF = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=400,format=gbrpf32le,zscale=p=bt709,"
          "tonemap=mobius:param=0.5,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


FS = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FSB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"


def font(sz, black=True, face=None):
    return ImageFont.truetype(face or (FB if black else FM), sz, index=0)


def ease_out_back(x, k=1.7):
    x = min(max(x, 0), 1); return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def ease_io(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def ease_in_c(x):
    x = min(max(x, 0), 1); return x ** 2.2


def ease_out(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3


# ============================================================ clips
class Clip:
    """src: file in videos/, ss: source start, dur: source seconds, speed: <1 slow motion (frame interpolated).
    fx/fy: crop focus 0..1, z: base zoom (crop tighter in ffmpeg), zoom: (z0, z1, cx, cy) dynamic zoom over the clip,
    hold: seconds to freeze the last frame, shake: px amplitude, grade: 'warm'|'cool'|'none'."""

    def __init__(self, src, ss, dur, speed=1.0, fx=0.5, fy=0.5, z=1.0, zoom=None, hold=0.0, shake=0.0,
                 grade='warm', blur=0, deshake=False, ramp=None, inset=None, inset_cy=0.47):
        self.src, self.ss, self.dur, self.speed = src, ss, dur, speed
        self.fx, self.fy, self.z, self.zoom, self.hold, self.shake = fx, fy, z, zoom, hold, shake
        self.grade, self.blur, self.deshake, self.ramp = grade, blur, deshake, ramp
        self.inset, self.inset_cy = inset, inset_cy
        self.n = int(round(dur / speed * FPS)); self.nh = int(round(hold * FPS))

    @property
    def length(self):
        return (self.n + self.nh) / FPS

    def frames(self):
        meta = CAT.get(self.src, {})
        vf = HDR_VF if meta.get('hdr') else ''
        if self.deshake:
            vf += 'deshake=rx=24:ry=24,'
        cw = f"min(iw\\,ih*9/16)/{self.z}"; ch = f"min(ih\\,iw*16/9)/{self.z}"
        vf += f"crop={cw}:{ch}:(iw-{cw})*{self.fx}:(ih-{ch})*{self.fy},scale={W}:{H}:flags=lanczos,setsar=1"
        if meta.get('w', 9999) < 720 or meta.get('h', 9999) < 720:
            vf += ",hqdn3d=1.5:1.5:3:3,unsharp=7:7:1.1:5:5:0.0"
        if self.speed < 0.999:
            vf += (f",minterpolate=fps={FPS / self.speed:.3f}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
                   f",setpts=PTS/{self.speed},fps={FPS}")
        elif self.speed > 1.001:
            vf += f",setpts=PTS/{self.speed},fps={FPS}"
        else:
            vf += f",fps={FPS}"
        path = self.src if self.src.startswith('/') else f'{VID}/{self.src}'
        cmd = ['ffmpeg', '-v', 'error', '-ss', f'{self.ss:.3f}', '-t', f'{self.dur + 0.4:.3f}', '-i', path,
               '-vf', vf, '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
        last = None
        for i in range(self.n):
            b = p.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                if last is None: raise RuntimeError(f'no frames from {self.src}')
                yield last.copy(); continue
            last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
            yield last
        p.stdout.close(); p.kill()
        for i in range(self.nh):
            yield last


# ============================================================ grading & frame fx
def _lut(kind):
    x = np.arange(256) / 255.0
    s = x + 0.10 * np.sin(2 * np.pi * x) * -1 * 0.5   # gentle S-curve
    s = np.clip(0.5 + (s - 0.5) * 1.06, 0, 1)
    if kind == 'warm':
        r, g, b = s ** 0.97, s, np.clip(s ** 1.04 * 0.98, 0, 1)
    elif kind == 'cool':
        r, g, b = np.clip(s ** 1.03 * 0.98, 0, 1), s, s ** 0.97
    elif kind == 'doc':   # soft, slightly lifted blacks, a touch of teal in the shadows
        s2 = 0.04 + 0.94 * x ** 1.02; r, g, b = s2 ** 1.01, s2, np.clip(s2 ** 0.99 + 0.01, 0, 1)
    else:
        r = g = b = x
    return [(np.clip(c, 0, 1) * 255).astype(np.uint8) for c in (r, g, b)]


LUTS = {k: _lut(k) for k in ('warm', 'cool', 'doc', 'none')}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.28 * np.clip(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2, 0, 1) ** 1.3)[..., None]


def grade(f, kind='warm', sat=1.12, vignette=True):
    if kind != 'none':
        l = LUTS[kind]
        f = np.dstack([cv2.LUT(f[..., i], l[i]) for i in range(3)])
        if sat != 1:
            hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
            f = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    if vignette:
        f = (f.astype(np.float32) * VIGNETTE).astype(np.uint8)
    return f


def zoom_frame(f, z, cx=0.5, cy=0.5, dx=0.0, dy=0.0, rot=0.0):
    if abs(z - 1) < 1e-3 and not dx and not dy and not rot:
        return f
    M = cv2.getRotationMatrix2D((cx * W, cy * H), rot, z)
    M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def blend(dst, rgba, x, y, alpha=1.0):
    """alpha-blend an RGBA uint8 image onto dst (RGB uint8) at top-left x,y"""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0: return dst
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    a = src[..., 3:4] / 255.0 * alpha
    reg = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (reg * (1 - a) + src[..., :3] * a).astype(np.uint8)
    return dst


def scaled(rgba, s):
    if abs(s - 1) < 1e-3: return rgba
    h, w = rgba.shape[:2]
    return cv2.resize(rgba, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)


# ============================================================ text graphics
EMO = ImageFont.truetype(FE, 109)


def emoji_img(ch, size):
    im = Image.new('RGBA', (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 4), ch, font=EMO, embedded_color=True)
    bb = im.getbbox(); im = im.crop(bb) if bb else im
    return np.array(im.resize((size, int(size * im.height / im.width)), Image.LANCZOS))


def text_mask(lines, fnt, spacing=1.12):
    asc, desc = fnt.getmetrics(); lh = int((asc + desc) * spacing)
    ws = [fnt.getbbox(l)[2] for l in lines]
    w = max(ws) + 20; h = lh * len(lines) + 20
    m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
    for i, l in enumerate(lines):
        d.text(((w - ws[i]) // 2, 10 + i * lh), l, font=fnt, fill=255)
    return np.array(m)


def telop(text, size=120, fill=((255, 240, 60), (255, 150, 0)), inner=((90, 30, 0), 10), outer=((255, 255, 255), 14),
          shadow=0.55, black=True, maxw=None, spacing=1.12, face=None):
    """Japanese variety-show style caption → RGBA numpy. fill: color or (top, bottom) gradient."""
    lines = text.split('\n')
    fnt = font(size, black, face)
    if maxw:
        while max(fnt.getbbox(l)[2] for l in lines) > maxw and size > 30:
            size -= 4; fnt = font(size, black, face)
    m = text_mask(lines, fnt, spacing).astype(np.float32) / 255
    ri, ro = (inner[1] if inner else 0), (outer[1] if outer else 0)
    pad = ri + ro + 24
    m = np.pad(m, pad)
    h, w = m.shape

    def dil(r):
        if r <= 0: return m
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        return cv2.GaussianBlur(cv2.dilate(m, k), (0, 0), 0.8)
    mi = dil(ri); mo = dil(ri + ro)
    out = np.zeros((h, w, 4), np.float32)

    def over(rgb, a):
        a = a[..., None]
        out[..., :3] = out[..., :3] * (1 - a) + np.asarray(rgb, np.float32) * a
        out[..., 3:4] = out[..., 3:4] * (1 - a) + 255 * a
    if shadow:
        sh = np.roll(np.roll(cv2.GaussianBlur(mo, (0, 0), 6), 8, 0), 6, 1)
        out[..., 3] = sh * 255 * shadow
    if outer: over(outer[0], mo)
    if inner: over(inner[0], mi)
    if isinstance(fill[0], (tuple, list)):
        g = np.linspace(0, 1, h)[:, None, None]
        top, bot = np.asarray(fill[0], np.float32), np.asarray(fill[1], np.float32)
        col = top * (1 - g) + bot * g
        a = m[..., None]
        out[..., :3] = out[..., :3] * (1 - a) + col * a
        out[..., 3:4] = out[..., 3:4] * (1 - a) + 255 * a
    else:
        over(fill, m)
    return np.clip(out, 0, 255).astype(np.uint8)


def subtitle(text, size=62, maxw=960, face=None, inner=((25, 25, 35), 9)):
    """narration subtitle: white text, dark outline, soft shadow; wraps into ≤2 lines"""
    fnt = font(size, False, face)
    if fnt.getbbox(text)[2] > maxw:
        # split near the middle at a punctuation mark
        cands = [i for i, c in enumerate(text) if c in '、。！？'] or [len(text) // 2]
        mid = min(cands, key=lambda i: abs(i - len(text) / 2)) + 1
        text = text[:mid] + '\n' + text[mid:]
    return telop(text.strip('\n'), size, fill=(255, 255, 255), inner=inner, outer=None, shadow=0.7,
                 black=False, maxw=maxw, face=face)


def rounded_box(w, h, r, color, alpha=255):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=tuple(color) + (alpha,))
    return np.array(im)


def label_box(text, size=40, bg=(220, 30, 50), fg=(255, 255, 255), padx=26, pady=10, r=12, black=True):
    fnt = font(size, black); bb = fnt.getbbox(text)
    w, h = bb[2] + 2 * padx, (bb[3] - bb[1]) + 2 * pady + 6
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=tuple(bg) + (255,))
    d.text((padx, pady - bb[1] + 2), text, font=fnt, fill=fg)
    return np.array(im)


def speed_lines(seed, cx, cy, n=90, inner=330):
    rng = np.random.default_rng(seed)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    R = 2400
    for _ in range(n):
        a = rng.uniform(0, 2 * np.pi); wdt = rng.uniform(0.004, 0.016); r0 = inner + rng.uniform(0, 260)
        p = [(cx + math.cos(a - wdt) * R, cy + math.sin(a - wdt) * R), (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
             (cx + math.cos(a + wdt) * R, cy + math.sin(a + wdt) * R)]
        d.polygon(p, fill=(255, 255, 255, int(rng.uniform(120, 220))))
    return np.array(im)


# ============================================================ overlay layers
class Layer:
    """t0..t1 in seconds on the output timeline. kind-specific drawing in draw()."""
    pre = False   # True: applied to the frame before other overlays (e.g. blur)

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1

    def active(self, t):
        return self.t0 <= t < self.t1


class Pop(Layer):
    """image that pops in (overshoot), optionally wobbles, and pops out. anchor = center (cx, cy) in px"""

    def __init__(self, t0, t1, img, cx, cy, inn=0.22, out=0.14, rot=0.0, wobble=0.0, style='pop', from_dx=0):
        super().__init__(t0, t1); self.img, self.cx, self.cy = img, cx, cy
        self.inn, self.out, self.rot, self.wobble, self.style, self.from_dx = inn, out, rot, wobble, style, from_dx

    def draw(self, f, t):
        a = 1.0; s = 1.0; dx = 0
        u = (t - self.t0) / self.inn
        if self.style == 'pop':
            s = 0.3 + 0.7 * ease_out_back(u, 2.2) if u < 1 else 1.0; a = min(1, u * 3)
        elif self.style == 'stamp':
            s = 2.6 - 1.6 * ease_out(u) if u < 1 else 1.0; a = min(1, u * 2.5)
        elif self.style == 'slide':
            dx = (1 - ease_out(u)) * self.from_dx if u < 1 else 0; a = min(1, u * 2)
        elif self.style == 'fade':
            a = min(1, u)
        v = (self.t1 - t) / self.out
        if v < 1:
            a *= max(0, v)
            if self.style in ('pop', 'stamp'): s *= 0.85 + 0.15 * v
        if self.wobble:
            s *= 1 + self.wobble * math.sin((t - self.t0) * 2 * math.pi * 1.6)
        img = scaled(self.img, s)
        if self.rot:
            h, w = img.shape[:2]; c, s_ = abs(math.cos(math.radians(self.rot))), abs(math.sin(math.radians(self.rot)))
            nw, nh = int(w * c + h * s_) + 2, int(w * s_ + h * c) + 2
            M = cv2.getRotationMatrix2D((w / 2, h / 2), self.rot, 1.0); M[0, 2] += (nw - w) / 2; M[1, 2] += (nh - h) / 2
            img = cv2.warpAffine(img, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        h, w = img.shape[:2]
        blend(f, img, int(self.cx - w / 2 + dx), int(self.cy - h / 2), a)


class Static(Layer):
    def __init__(self, t0, t1, img, x, y, fade=0.2):
        super().__init__(t0, t1); self.img, self.x, self.y, self.fade = img, x, y, fade

    def draw(self, f, t):
        a = min(1, (t - self.t0) / self.fade, (self.t1 - t) / self.fade) if self.fade else 1
        blend(f, self.img, self.x, self.y, a)


class Flash(Layer):
    def __init__(self, t0, d=0.25, color=(255, 255, 255), peak=0.85):
        super().__init__(t0, t0 + d); self.color, self.peak, self.d = color, peak, d

    def draw(self, f, t):
        a = self.peak * (1 - (t - self.t0) / self.d)
        f[:] = (f.astype(np.float32) * (1 - a) + np.asarray(self.color, np.float32) * a).astype(np.uint8)


class SpeedLines(Layer):
    def __init__(self, t0, t1, cx, cy, inner=330):
        super().__init__(t0, t1); self.v = [speed_lines(i, cx, cy, inner=inner) for i in range(4)]

    def draw(self, f, t):
        k = int((t - self.t0) * FPS) % len(self.v)
        a = min(1, (t - self.t0) / 0.1, (self.t1 - t) / 0.15)
        blend(f, self.v[k], 0, 0, a * 0.85)


class Blur(Layer):
    pre = True

    def __init__(self, t0, t1, sigma=18, dark=0.45, fade=0.25):
        super().__init__(t0, t1); self.sigma, self.dark, self.fade = sigma, dark, fade

    def draw(self, f, t):
        a = min(1, (t - self.t0) / self.fade, (self.t1 - t) / self.fade)
        small = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        b = cv2.resize(cv2.GaussianBlur(small, (0, 0), self.sigma / 4), (W, H)).astype(np.float32) * (1 - self.dark)
        f[:] = (f.astype(np.float32) * (1 - a) + b * a).astype(np.uint8)


class Meter(Layer):
    """'目力メーター': vertical gauge on the left; fills from 0 to 1 between f0 and f1 seconds, then flashes MAX"""

    def __init__(self, t0, t1, f0, f1, label='目力', x=56, y=560, w=96, h=640):
        super().__init__(t0, t1); self.f0, self.f1, self.x, self.y, self.w, self.h = f0, f1, x, y, w, h
        self.lab = telop(label, 52, fill=(255, 255, 255), inner=((200, 20, 60), 7), outer=None, shadow=0.6)
        self.max = telop('MAX!!', 70, fill=((255, 255, 120), (255, 60, 40)), inner=((120, 0, 30), 8), outer=((255, 255, 255), 8))
        self.heart = emoji_img('😍', 110)
        frame = Image.new('RGBA', (w + 16, h + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(frame)
        d.rounded_rectangle([0, 0, w + 15, h + 15], 26, fill=(255, 255, 255, 235))
        d.rounded_rectangle([8, 8, w + 7, h + 7], 20, fill=(30, 30, 50, 235))
        for k in range(1, 10):
            yk = 8 + h - h * k / 10; d.line([w - 14, yk, w + 6, yk], fill=(255, 255, 255, 140), width=3)
        self.frame = np.array(frame)
        g = np.linspace(1, 0, h)[:, None]
        col = np.stack([np.interp(g, [0, .5, 1], [80, 255, 255]), np.interp(g, [0, .5, 1], [220, 210, 40]),
                        np.interp(g, [0, .5, 1], [120, 40, 60])], -1)[:, 0]
        self.grad = np.dstack([np.repeat(col[:, None, :], w - 24, 1), np.full((h, w - 24, 1), 255)]).astype(np.uint8)

    def draw(self, f, t):
        a = min(1, (t - self.t0) / 0.2, (self.t1 - t) / 0.2)
        x, y, w, h = self.x, self.y, self.w, self.h
        u = (t - self.t0) / 0.25; s = 0.5 + 0.5 * ease_out_back(u) if u < 1 else 1
        blend(f, self.frame, x - 8, y - 8, a)
        lv = ease_io((t - self.f0) / max(0.01, self.f1 - self.f0))
        lv = min(1, lv + 0.02 * math.sin(t * 40) * (lv > 0.95))
        fh = int(h * lv)
        if fh > 2:
            blend(f, self.grad[h - fh:], x + 4, y + h - fh, a)
        lab = self.lab; blend(f, lab, x + w // 2 - lab.shape[1] // 2, y - lab.shape[0] - 6, a)
        if lv >= 0.99:
            on = (int((t - self.f1) * 6) % 2 == 0)
            m = scaled(self.max, 1.0 + 0.08 * math.sin((t - self.f1) * 20))
            if on or t - self.f1 < 0.3:
                blend(f, m, x + w // 2 - m.shape[1] // 2 + 60, y + h + 10, a)
            blend(f, self.heart, x + w // 2 - 55, y - 210, a)


class Replay(Layer):
    """REPLAY badge (top-right) + thin letterbox + slight desaturation"""
    pre = True

    def __init__(self, t0, t1):
        super().__init__(t0, t1)
        self.badge = label_box('● リプレイ', 44, bg=(20, 20, 30), fg=(255, 255, 255))
        self.slow = label_box('スロー', 36, bg=(255, 200, 40), fg=(30, 20, 0))

    def draw(self, f, t):
        g = f.mean(2, keepdims=True); f[:] = (f * 0.82 + g * 0.18).astype(np.uint8)
        f[:110] = (f[:110] * 0.25).astype(np.uint8); f[-110:] = (f[-110:] * 0.25).astype(np.uint8)

    def post(self, f, t):
        blink = int((t - self.t0) * 2.5) % 2 == 0
        b = self.badge.copy()
        if not blink: b[:, :70, :3] = b[:, :70, :3]  # dot stays; color the dot red when blinking
        dot = b[:, 18:62]; red = (dot[..., 0] > 200) & (dot[..., 1] > 200)
        if blink: dot[red] = (255, 40, 40, 255)
        blend(f, b, W - b.shape[1] - 40, 150)
        blend(f, self.slow, W - self.slow.shape[1] - 40, 150 + b.shape[0] + 10)


# ============================================================ timeline render
class Timeline:
    def __init__(self):
        self.clips = []        # list of (t_start, Clip)
        self.layers = []
        self.t = 0.0
        self.cut_fx = {}       # clip index -> 'whip'

    def add(self, clip, whip=False):
        self.clips.append((self.t, clip));
        if whip: self.cut_fx[len(self.clips) - 1] = 'whip'
        self.t += clip.length
        return self.clips[-1][0]

    def layer(self, l):
        self.layers.append(l); return l

    def render(self, out_path, audio_path=None, log=True):
        n_total = int(round(self.t * FPS))
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
        if audio_path: cmd += ['-i', audio_path]
        cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high']
        if audio_path: cmd += ['-c:a', 'aac', '-b:a', '192k', '-shortest']
        cmd += ['-movflags', '+faststart', out_path]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        fi = 0
        for ci, (ts, clip) in enumerate(self.clips):
            whip_in = self.cut_fx.get(ci) == 'whip'
            whip_out = self.cut_fx.get(ci + 1) == 'whip'
            nc = clip.n + clip.nh
            for k, fr in enumerate(clip.frames()):
                t = fi / FPS; tl = k / FPS
                f = fr.copy()
                # dynamic zoom / shake
                z, cx, cy = 1.0, 0.5, 0.5
                if clip.zoom:
                    z0, z1, cx, cy = clip.zoom[:4]
                    e = clip.zoom[4] if len(clip.zoom) > 4 else ease_io
                    z = z0 + (z1 - z0) * e(k / max(1, nc - 1))
                dx = dy = 0.0
                if clip.shake:
                    dx = clip.shake * math.sin(t * 37.0) * math.cos(t * 13.0); dy = clip.shake * math.sin(t * 29.0 + 1)
                # whip pan in/out
                rot = 0
                if whip_in and k < 6:
                    p = 1 - k / 6; dx += W * 0.55 * p ** 2
                if whip_out and k >= nc - 6:
                    p = (k - (nc - 6) + 1) / 6; dx -= W * 0.55 * p ** 2
                zz = max(1.0, z) if (dx or dy) else z
                if dx or dy: zz = max(zz, 1.04)
                f = zoom_frame(f, zz, cx, cy, dx, dy, rot)
                if (whip_in and k < 6) or (whip_out and k >= nc - 6):
                    kk = 61; f = cv2.blur(f, (kk, 3))
                f = grade(f, clip.grade, sat={'doc': 0.94, 'none': 1.0}.get(clip.grade, 1.12))
                if clip.inset:
                    f = inset_frame(f, clip.inset, clip.inset_cy)
                for l in self.layers:
                    if l.pre and l.active(t): l.draw(f, t)
                for l in self.layers:
                    if l.active(t):
                        if not l.pre: l.draw(f, t)
                        elif hasattr(l, 'post'): l.post(f, t)
                enc.stdin.write(f.tobytes()); fi += 1
            if log: print(f'  clip {ci + 1}/{len(self.clips)} {clip.src} -> {fi / FPS:.1f}s', flush=True)
        enc.stdin.close(); enc.wait()
        return fi / FPS


# ============================================================ audio mix
def read_wav(path, sr=48000):
    with wave.open(path) as w:
        n = w.getnframes(); ch = w.getnchannels(); r = w.getframerate(); sw = w.getsampwidth()
        x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    if r != sr:
        from scipy.signal import resample_poly
        g = math.gcd(r, sr); x = resample_poly(x, sr // g, r // g)
    return x


def wav_dur(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def mix(total, narr, ses, bgm_track=None, bgm_gain=0.42, duck=0.45, out='mix.wav', sr=48000):
    """narr: [(wav_path, t)], ses: [(np array, t, gain)], bgm_track: np array starting at 0"""
    from sound import write_wav
    n = int((total + 0.5) * sr)
    vo = np.zeros(n); fx = np.zeros(n); mu = np.zeros(n)
    for p, t in narr:
        if not os.path.exists(p): continue
        x = read_wav(p, sr); i = int(t * sr); e = min(n, i + len(x)); vo[i:e] += x[:e - i]
    for x, t, g in ses:
        i = int(t * sr); e = min(n, i + len(x))
        if i < n: fx[i:e] += x[:e - i] * g
    if bgm_track is not None:
        e = min(n, len(bgm_track)); mu[:e] = bgm_track[:e]
        # duck under narration
        act = np.abs(vo) > 0.01
        k = int(0.25 * sr); env = np.convolve(act.astype(np.float32), np.ones(k) / k, 'same')
        env = np.clip(env * 4, 0, 1)
        sm = int(0.08 * sr); env = np.convolve(env, np.ones(sm) / sm, 'same')
        mu *= bgm_gain * (1 - (1 - duck) * env)
        # fade out at the end
        fo = int(1.2 * sr); mu[n - fo:] *= np.linspace(1, 0, fo)
    y = vo * 1.0 + fx * 0.8 + mu
    write_wav(out, np.clip(y / max(1.0, np.abs(y).max() / 0.98), -1, 1), sr)
    return out


def loudnorm(src, dst, I=-14):
    """two-pass loudness normalisation to I LUFS (true peak -1.5 dB)"""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', src, '-af', f'loudnorm=I={I}:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    j = json.loads(r[r.rfind('{'):r.rfind('}') + 1])
    af = (f"loudnorm=I={I}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', af, '-ar', '48000', dst], check=True)


def trim_subs(layers):
    """make consecutive subtitle layers never overlap (each ends when the next begins)"""
    subs = sorted([l for l in layers if getattr(l, 'is_sub', False)], key=lambda l: l.t0)
    for a_, b_ in zip(subs, subs[1:]):
        if a_.t1 > b_.t0 - 0.03: a_.t1 = max(a_.t0 + 0.2, b_.t0 - 0.03)


class Grain(Layer):
    """film grain + slight flicker for a documentary feel"""
    pre = True

    def __init__(self, t0, t1, amt=7):
        super().__init__(t0, t1); rng = np.random.default_rng(3)
        self.tiles = [rng.normal(0, amt, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]

    def draw(self, f, t):
        g = cv2.resize(self.tiles[int(t * FPS) % 6], (W, H))[..., None]
        f[:] = np.clip(f.astype(np.float32) + g, 0, 255).astype(np.uint8)


class Chapter(Layer):
    """documentary chapter card: thin line + serif title sliding in at lower-left"""

    def __init__(self, t0, t1, title, sub='', y=1180):
        super().__init__(t0, t1); self.y = y
        self.title = telop(title, 92, fill=(255, 255, 255), inner=None, outer=None, shadow=0.75, face=FSB)
        self.sub = telop(sub, 38, fill=(235, 235, 235), inner=None, outer=None, shadow=0.7, face=FS) if sub else None

    def draw(self, f, t):
        u = ease_out((t - self.t0) / 0.6); a = min(1, (t - self.t0) / 0.4, (self.t1 - t) / 0.4)
        x = 70; y = self.y
        ln = int(560 * u)
        if ln > 0:
            seg = f[y:y + 4, x:x + ln].astype(np.float32); f[y:y + 4, x:x + ln] = (seg * (1 - 0.9 * a) + 255 * 0.9 * a).astype(np.uint8)
        blend(f, self.title, x - 20 + int(40 * (1 - u)), y - self.title.shape[0] + 14, a)
        if self.sub is not None:
            blend(f, self.sub, x - 20 + int(60 * (1 - u)), y + 10, a * 0.95)


class Confetti(Layer):
    def __init__(self, t0, t1, n=140, seed=5):
        super().__init__(t0, t1); r = np.random.default_rng(seed)
        self.p = [(r.uniform(0, W), r.uniform(-H * 0.6, 0), r.uniform(260, 520), r.uniform(-60, 60), r.uniform(0, 6.3), r.uniform(4, 10),
                   tuple(int(c) for c in r.choice([[255, 70, 90], [255, 210, 40], [60, 200, 255], [120, 230, 120], [255, 140, 220], [255, 255, 255]])),
                   r.uniform(14, 26)) for _ in range(n)]

    def draw(self, f, t):
        u = t - self.t0; a = min(1, (self.t1 - t) / 0.4)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        for x, y, vy, vx, ph, sp, col, sz in self.p:
            yy_ = y + vy * u; xx_ = x + vx * u + 30 * math.sin(ph + u * sp)
            if -40 < yy_ < H + 40:
                w_ = sz * abs(math.cos(ph + u * sp * 1.3)) + 3
                dr.rectangle([xx_ - w_ / 2, yy_ - sz * 0.3, xx_ + w_ / 2, yy_ + sz * 0.3], fill=col + (235,))
        blend(f, np.array(im), 0, 0, a)


def judge_cards(scores=('10.0', '10.0', '10.0')):
    """three judge score cards side by side → RGBA"""
    cards = []
    for sc in scores:
        im = Image.new('RGBA', (250, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, 249, 199], 22, fill=(255, 255, 255, 250), outline=(18, 32, 78, 255), width=8)
        fnt = font(96); bb = fnt.getbbox(sc)
        d.text(((250 - bb[2]) // 2, (200 - bb[3]) // 2 - 8), sc, font=fnt, fill=(215, 25, 45))
        cards.append(np.array(im))
    return cards


_card_mask = {}


def inset_frame(f, sc, cy=0.47, border=10, radius=34):
    """show the frame as a rounded white-bordered card over a blurred, darkened copy of itself"""
    small = cv2.resize(f, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    bg = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H)).astype(np.float32) * 0.62
    cw, ch = int(W * sc), int(H * sc)
    card = cv2.resize(f, (cw, ch), interpolation=cv2.INTER_AREA)
    key = (cw, ch)
    if key not in _card_mask:
        m = Image.new('L', (cw + 2 * border, ch + 2 * border), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, cw + 2 * border - 1, ch + 2 * border - 1], radius + border, fill=255)
        mi = Image.new('L', (cw, ch), 0); ImageDraw.Draw(mi).rounded_rectangle([0, 0, cw - 1, ch - 1], radius, fill=255)
        sh = cv2.GaussianBlur(np.array(m, np.float32) / 255, (0, 0), 18)
        _card_mask[key] = (np.array(m, np.float32)[..., None] / 255, np.array(mi, np.float32)[..., None] / 255, sh[..., None])
    mo, mi, sh = _card_mask[key]
    x0 = (W - cw) // 2 - border; y0 = int(H * cy - ch / 2) - border
    hh, ww = mo.shape[:2]
    reg = bg[y0 + 14:y0 + 14 + hh, x0:x0 + ww]; reg *= (1 - 0.55 * sh[:reg.shape[0], :reg.shape[1]])
    reg = bg[y0:y0 + hh, x0:x0 + ww]
    reg[:] = reg * (1 - mo) + 255 * mo
    inner = bg[y0 + border:y0 + border + ch, x0 + border:x0 + border + cw]
    inner[:] = inner * (1 - mi) + card.astype(np.float32) * mi
    return bg.astype(np.uint8)
