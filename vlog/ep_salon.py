"""まめすけの日常④「サロンの日、変身ビフォーアフター」"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epkit import *

E = Ep('nichijo_salon', suby=1730); TL = E.TL; d = E.d
OUT = next((a for a in sys.argv[1:] if not a.startswith('--')), "/home/claude/out/まめすけの日常_サロン変身.mp4")
NAVY, RED, PINK = (18, 32, 78), (215, 25, 45), (255, 110, 160)
BA = f"{SCR}/assets/comp/beforeafter.mp4"
IN = 0.72; ICY = 0.465          # inset card scale / centre (cards sit between the top telop and the subtitle)


def badge(text, bg):
    return label_box(text, 50, bg=bg, padx=30, pady=10)


# ---------------------------------------------------------------- 1. hook: who is this?
L = d('A01') + 1.0
t = TL.add(Clip('LSXR7440.MP4', 7.1, min(L, 1.45), hold=max(0, L - 1.45), inset=IN, inset_cy=ICY, zoom=(1.0, 1.08, 0.5, 0.35)))
E.say('A01', t + 0.3)
E.tel('誰…？', t + 0.4, t + L, y=250, size=150, fill=((235, 245, 255), (150, 200, 255)), inner=((0, 40, 100), 12), wobble=0.03)
for k, (x, y) in enumerate([(170, 520), (900, 640), (200, 1220)]):
    TL.layer(Pop(t + 0.6 + k * 0.15, t + L, telop('?', 120, fill=(255, 255, 255), inner=((0, 40, 100), 10), outer=None), x, y, rot=(-15, 12, -8)[k]))
    E.se('pon', t + 0.6 + k * 0.15, 0.5)
E.music.append(('intro', t, None))

# ---------------------------------------------------------------- 2-3. before: shampoo
t = TL.t
L = d('A02') + 0.5
TL.add(Clip('LSXR7440.MP4', 0.2, min(L, 3.4), hold=max(0, L - 3.4), inset=IN, inset_cy=ICY, zoom=(1.0, 1.06, 0.5, 0.4)))
TL.layer(Pop(t + 0.1, t + 0.1 + 6.5, badge('BEFORE', (60, 70, 90)), W // 2, 250, style='stamp', inn=0.15))
E.se('pon', t + 0.1, 0.7)
E.say('A02', t + 0.2)
t = TL.t
L = d('A03') + 0.5
TL.add(Clip('LSXR7440.MP4', 3.6, min(L, 3.4), hold=max(0, L - 3.4), inset=IN, inset_cy=ICY, zoom=(1.0, 1.1, 0.5, 0.35)))
E.say('A03', t + 0.15)
E.tel('ぺたんこ', t + 0.3, t + L, y=1380, size=120, fill=((235, 245, 255), (150, 200, 255)), inner=((0, 40, 100), 11), rot=-4)
E.se('boing', t + 0.3, 0.6)

# ---------------------------------------------------------------- 4. the transformation
t = TL.t
L = d('A04') + 0.6
TL.add(Clip('LSXR7440.MP4', 7.0, min(L * 0.5, 1.5), speed=0.5, hold=max(0, L - 3.0), inset=IN, inset_cy=ICY, zoom=(1.0, 1.3, 0.5, 0.35)))
E.say('A04', t + 0.1)
E.se('roll', t + L - 1.4, 0.7, d=1.4)
E.music[-1] = ('intro', E.music[-1][1], t)
E.music.append(('tense', t, t + L))
tf = TL.t
TL.layer(Flash(tf - 0.05, 0.6, peak=1.0))
E.se('sparkle_up', tf - 0.3, 0.8); E.se('kira', tf, 0.8); E.se('don', tf, 0.7)

# ---------------------------------------------------------------- 5. after: fluffy
t = TL.t
L = max(3.6, d('A05') + 1.6)
TL.add(Clip('UOMB2949.MP4', 0.9, min(L, 4.3), hold=max(0, L - 4.3), inset=IN, inset_cy=ICY, zoom=(1.0, 1.06, 0.5, 0.45)))
TL.layer(Pop(t + 0.05, t + L + 6, badge('AFTER', RED), W // 2, 250, style='stamp', inn=0.15))
E.say('A05', t + 0.25)
E.tel('ふわっふわ', t + 0.3, t + L, y=1390, size=150, fill=((255, 240, 250), PINK), inner=((150, 0, 70), 13), style='stamp', rot=-3)
for k, (x, y) in enumerate([(150, 470), (930, 560), (140, 1100), (940, 1150)]):
    TL.layer(Pop(t + 0.35 + k * 0.12, t + L, emoji_img('✨', 110), x, y, wobble=0.08))
E.music.append(('main', t, None))
t = TL.t
TL.add(Clip('UOMB2949.MP4', 5.3, 1.2, inset=IN, inset_cy=ICY, zoom=(1.0, 1.12, 0.5, 0.45)))
E.tel('ちかい', t + 0.3, t + 1.2, y=1390, size=100, fill=(255, 255, 255), inner=((150, 0, 70), 10))
E.se('pon', t + 0.3, 0.6)

# ---------------------------------------------------------------- 6. shampoo-commercial hair flip
t = TL.t
L = max(3.2, d('A06') + 0.6)
TL.add(Clip('KDRV4602.MP4', 12.0, 1.6, speed=1.6 / L, inset=IN, inset_cy=ICY, zoom=(1.0, 1.08, 0.5, 0.45)), whip=True)
E.se('slow', t, 0.5); E.se('kira', t + 0.6, 0.6)
E.say('A06', t + 0.2)
E.tel('サラッ…', t + 0.5, t + L, y=1390, size=120, fill=(255, 255, 255), inner=((120, 90, 20), 8), outer=None, face=FSB, style='fade')
for k, (x, y) in enumerate([(160, 620), (920, 520), (900, 1180)]):
    TL.layer(Pop(t + 0.7 + k * 0.25, t + L, emoji_img('✨', 90), x, y, wobble=0.1))

# ---------------------------------------------------------------- 7. photo shoots
t = TL.t
L1 = 1.6
TL.add(Clip('KDRV4602.MP4', 0.0, L1, inset=IN, inset_cy=ICY, zoom=(1.0, 1.06, 0.5, 0.45)), whip=True)
E.se('shutter', t + 0.2, 0.8)
t2 = TL.t
L2 = max(1.6, d('A07') + 0.8 - L1)
TL.add(Clip('KSWZ3270.MP4', 3.3, min(L2, 2.4), hold=max(0, L2 - 2.4), inset=IN, inset_cy=ICY, zoom=(1.0, 1.08, 0.5, 0.45)))
E.se('shutter', t2 + 0.1, 0.8)
E.say('A07', t + 0.3)
E.tel('満面の笑み', t + 0.4, t2 + L2, y=1390, size=120, fill=((255, 250, 170), (255, 160, 20)), inner=((130, 50, 0), 11))
TL.layer(Flash(t2, 0.15, peak=0.6))

# ---------------------------------------------------------------- 8. before / after side by side
t = TL.t
L = d('A08') + 1.8
TL.add(Clip(BA, 0.0, 1.55, grade='none', hold=max(0, L - 1.55)), whip=True)
TL.layer(Pop(t + 0.1, t + L, badge('BEFORE', (60, 70, 90)), 40 + 242, 460, style='stamp', inn=0.15))
TL.layer(Pop(t + 0.35, t + L, badge('AFTER', RED), 556 + 242, 460, style='stamp', inn=0.15))
E.se('pon', t + 0.1, 0.7); E.se('pon', t + 0.35, 0.7)
E.say('A08', t + 0.4)
tw = t + 0.4 + d('A08') * 0.62
E.tel('同じ犬です', tw, t + L, y=1520, size=140, fill=((255, 255, 255), (255, 225, 230)), inner=(RED, 13), style='stamp')
TL.layer(Flash(tw, 0.2, peak=0.5)); E.se('don', tw, 0.8)

# ---------------------------------------------------------------- 9. thanks
t = TL.t
L = d('A09') + 2.0
TL.add(Clip('KDRV4602.MP4', 9.4, min(L, 2.6), hold=max(0, L - 2.6), inset=IN, inset_cy=ICY, zoom=(1.0, 1.08, 0.5, 0.45)))
E.say('A09', t + 0.3)
E.tel('トリマーさん\nいつもありがとう', t + 0.5, t + L, y=1380, size=86, fill=(255, 255, 255), inner=(PINK, 10), outer=None)
TL.layer(Pop(t + 0.8, t + L, emoji_img('💐', 120), 930, 1230, wobble=0.05))
E.se('chime', t + 0.5, 0.6)

# ---------------------------------------------------------------- persistent graphics
hdr = label_box('まめすけの日常', 34, bg=PINK)
TL.layer(Static(d('A01') + 1.0, TL.t, hdr, 40, 120))
TL.layer(Static(0, TL.t, credit_img(), W - credit_img().shape[1] - 40, 124, fade=0))

E.finish(OUT, sys.argv, bpm=112, bgm_gain=0.5, duck=0.42, gains={'tense': 0.8})
