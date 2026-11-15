"""まめすけの日常①「密着 まめすけアナ オフの1日」 ドキュメンタリー風リール"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *
import sound as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VO = f"{ROOT}/voices/nichijo_off"
TXT = {l.split('\t')[0]: l.split('\t')[1] for l in open(f"{ROOT}/scripts_txt/nichijo_off.tsv", encoding='utf-8') if '\t' in l}
OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else "/home/claude/out/まめすけの日常_オフの1日.mp4"
WORK = f"{SCR}/vlog_off"; os.makedirs(WORK, exist_ok=True)
ANCHOR = "/home/claude/out/まめすけNEWS_床と一体化.mp4"


def d(i):
    p = f"{VO}/{i}.wav"
    return wav_dur(p) if os.path.exists(p) else len(TXT[i]) * 0.15


TL = Timeline(); narr = []; ses = []; music = []
SUBY = 1450
G = 'doc'


def say(i, t, sub=True):
    narr.append((f"{VO}/{i}.wav", t))
    if sub:
        img = subtitle(TXT[i], 56, face=FS, inner=((10, 10, 15), 7))
        TL.layer(Pop(t, t + d(i) + 0.25, img, W // 2, SUBY, inn=0.25, out=0.2, style='fade'))


def se(name, t, g=1.0, **kw):
    ses.append((S.SE[name](**kw), t, g))


def shot(src, ss, L, **kw):
    kw.setdefault('grade', G)
    return TL.add(Clip(src, ss, L * kw.get('speed', 1.0), **kw))


def beat(i, src, ss, extra=0.7, maxsrc=None, **kw):
    """one narrated shot: length follows the narration"""
    L = d(i) + extra
    sp = kw.get('speed', 1.0)
    if maxsrc is not None and L * sp > maxsrc:
        kw['hold'] = L - maxsrc / sp; L = maxsrc / sp
    t = shot(src, ss, L, **kw)
    say(i, t + 0.3)
    return t


# ---------------------------------------------------------------- cold open
t = beat('D01', 'IMG_1132.MOV', 9.6, extra=0.9, maxsrc=11, zoom=(1.0, 1.12, 0.5, 0.55))
music.append(('calm', 0, None))

# ---------------------------------------------------------------- title
L = d('D02') + 2.0
t = shot('IMG_1122.MOV', 7.0, L, fx=0.45, zoom=(1.0, 1.1, 0.5, 0.5))
TL.layer(Blur(t, t + L, sigma=10, dark=0.45, fade=0.4))
TL.layer(Pop(t + 0.3, t + L, telop('密着', 70, fill=(255, 255, 255), inner=None, outer=None, shadow=0.6, face=FS), W // 2, 700, style='fade', inn=0.6, out=0.4))
TL.layer(Pop(t + 0.7, t + L, telop('まめすけアナ', 130, fill=(255, 255, 255), inner=None, outer=None, shadow=0.75, face=FSB), W // 2, 850, style='fade', inn=0.7, out=0.4))
TL.layer(Pop(t + 1.1, t + L, telop('オフの1日', 96, fill=(255, 232, 170), inner=None, outer=None, shadow=0.75, face=FSB), W // 2, 1000, style='fade', inn=0.7, out=0.4))
say('D02', t + 1.2, sub=False)
se('chime', t + 0.6, 0.35)

# ---------------------------------------------------------------- chapter 1: ごはん
t = beat('D03', 'IMG_1790.MOV', 0.0, extra=0.4, maxsrc=1.38, speed=0.5, fx=0.5, zoom=(1.05, 1.25, 0.45, 0.6))
TL.layer(Chapter(t + 0.1, t + 2.6, 'ごはん', 'MEAL TIME'))
se('whoosh', t, 0.35)
beat('D04', 'IMG_1831.MOV', 23.0, extra=0.9, zoom=(1.0, 1.15, 0.5, 0.55))
beat('D05', 'IMG_1831.MOV', 45.0, extra=0.8, zoom=(1.15, 1.05, 0.5, 0.55))

# ---------------------------------------------------------------- chapter 2: ひとやすみ・あそび
t = beat('D06', 'IMG_1132.MOV', 0.5, extra=1.0, maxsrc=3.4, zoom=(1.0, 1.1, 0.5, 0.5))
TL.layer(Chapter(t + 0.1, t + 2.6, 'ひとやすみ', 'BREAK'))
music[-1] = ('calm', music[-1][1], t)
music.append(('intro', t + 1.0, None))
beat('D07', 'IMG_1412.MOV', 0.0, extra=0.6, maxsrc=7.0, zoom=(1.0, 1.08, 0.5, 0.5))
t = beat('D08', 'IMG_1198.MOV', 1.9, extra=0.6, maxsrc=2.7, zoom=(1.0, 1.1, 0.5, 0.5))
se('pon', t + (2.35 - 1.9) + 0.0, 0.5)

# ---------------------------------------------------------------- chapter 3: おさんぽ
t = beat('D09', 'IMG_1350.MOV', 0.2, extra=1.2, maxsrc=5.5, zoom=(1.0, 1.08, 0.5, 0.5))
TL.layer(Chapter(t + 0.1, t + 2.8, 'おさんぽ', 'WALK'))
beat('D10', 'IMG_1350.MOV', 6.0, extra=0.7, maxsrc=3.6, zoom=(1.08, 1.18, 0.5, 0.55))
beat('D11', 'IMG_1342.MOV', 1.0, extra=0.6, maxsrc=5.5, zoom=(1.0, 1.06, 0.5, 0.5))
t = beat('D12', 'IMG_3750.MOV', 15.5, extra=0.8, maxsrc=6.0, zoom=(1.0, 1.06, 0.5, 0.5))
beat('D13', 'IMG_3732.MOV', 0.0, extra=0.5, maxsrc=3.3, zoom=(1.0, 1.1, 0.5, 0.45))
music[-1] = ('intro', music[-1][1], TL.t)

# ---------------------------------------------------------------- chapter 4: おやすみ
t = beat('D14', 'IMG_1364.MOV', 5.0, extra=1.2, maxsrc=9.0, zoom=(1.0, 1.1, 0.5, 0.5))
TL.layer(Chapter(t + 0.1, t + 2.8, 'おやすみ', 'GOOD NIGHT'))
music.append(('calm', t, None))
t = beat('D15', 'IMG_1360.MOV', 12.0, extra=2.2, maxsrc=20, zoom=(1.0, 1.18, 0.55, 0.45))
TL.layer(Flash(TL.t - 0.6, 0.6, color=(0, 0, 0), peak=0.0))

# ---------------------------------------------------------------- ending: back to the studio
L = d('D16') + 2.6
t = TL.add(Clip(ANCHOR, 40.0, 0.2, z=1.5, fy=0.12, grade='none', hold=L - 0.2, zoom=(1.0, 1.06, 0.5, 0.45)))
TL.layer(Flash(t, 0.35, color=(255, 255, 255), peak=0.7))
say('D16', t + 0.4)
TL.layer(Pop(t + 0.5, t + L, label_box('まめすけNEWS', 54, bg=(215, 25, 45), padx=34, pady=12), W // 2, 1200, inn=0.3))
TL.layer(Pop(t + 0.8, t + L, telop('密着 まめすけアナ オフの1日　おわり', 44, fill=(255, 255, 255), inner=((20, 20, 30), 6), outer=None, face=FS), W // 2, 1290, style='fade', inn=0.4))
se('chime', t + 0.5, 0.5)
music[-1] = ('calm', music[-1][1], TL.t)

# overlays across the whole piece
TL.layer(Grain(0, t, amt=6))
credit = telop('VOICEVOX:ずんだもん', 26, fill=(255, 255, 255), inner=((0, 0, 0), 4), outer=None, shadow=0.5, black=False)
TL.layer(Static(0, TL.t, credit, W - credit.shape[1] - 36, 146, fade=0))
doc = telop('DOCUMENT', 30, fill=(255, 255, 255), inner=None, outer=None, shadow=0.6, face=FS)
TL.layer(Static(d('D01') + 0.9, t, doc, 44, 146, fade=0.5))

# ---------------------------------------------------------------- music
total = TL.t
BPM = 96
bgm = np.zeros(int((total + 3) * S.SR))
for kind, a, b in music:
    if b is None: b = total
    bars = int(math.ceil((b - a) / (4 * 60 / BPM))) + 1
    sec = S.bgm_section(kind, bars, BPM)
    n = int((b - a) * S.SR); sec = sec[:n + int(1.0 * S.SR)]
    fi = int(0.6 * S.SR); sec[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.0 * S.SR); sec[-fo:] *= np.linspace(1, 0, fo)
    S.place(bgm, sec, a)
bgm = S.norm(bgm, 0.8)

print(f"timeline {total:.1f}s, clips {len(TL.clips)}, layers {len(TL.layers)}")
if '--plan' in sys.argv: sys.exit()
mix(total, narr, ses, bgm, bgm_gain=0.55, duck=0.5, out=f"{WORK}/mix.wav")
loudnorm(f"{WORK}/mix.wav", f"{WORK}/mix_ln.wav", I=-14)
TL.render(OUT, f"{WORK}/mix_ln.wav")
print("done", OUT)
