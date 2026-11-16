"""まめすけの日常⑤「もぐもぐ、そしておやすみ」 癒し回"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epkit import *

BROWN = (110, 70, 40)
E = Ep('nichijo_iyashi', suby=1480, sub_kw=dict(size=56, face=FM, inner=(BROWN, 7))); TL = E.TL; d = E.d
OUT = next((a for a in sys.argv[1:] if not a.startswith('--')), "/home/claude/out/まめすけの日常_もぐもぐおやすみ.mp4")


class FadeTo(Layer):
    def __init__(self, t0, t1, color=(0, 0, 0)):
        super().__init__(t0, t1 + 1.0); self.a, self.b, self.color = t0, t1, color

    def draw(self, f, t):
        a = min(1, max(0, (t - self.a) / (self.b - self.a)))
        f[:] = (f.astype(np.float32) * (1 - a) + np.asarray(self.color, np.float32) * a).astype(np.uint8)


def soft(text, size=96, col=(255, 236, 240), edge=(220, 120, 150)):
    return telop(text, size, fill=col, inner=(edge, 9), outer=((255, 255, 255), 6), shadow=0.35)


def sprinkle(t0, t1, words, spots, size=88, col=(255, 236, 240), edge=(220, 120, 150), step=0.7):
    for k, (x, y) in enumerate(spots):
        tk = t0 + k * step
        if tk >= t1 - 0.3: break
        TL.layer(Pop(tk, t1, soft(words[k % len(words)], size, col, edge), x, y, rot=(-8, 7, -5, 9)[k % 4], wobble=0.04, inn=0.3, out=0.3))
        E.se('pon', tk, 0.35)


# ---------------------------------------------------------------- 1. opening
L = d('M01') + 2.2
t = TL.add(Clip('IMG_1132.MOV', 9.4, min(L, 11.5), hold=max(0, L - 11.5), zoom=(1.0, 1.12, 0.5, 0.55)))
TL.layer(Pop(t + 0.4, t + L, telop('まめすけと', 80, fill=(255, 255, 255), inner=(BROWN, 8), outer=None, face=FSB), W // 2, 380, style='fade', inn=0.6, out=0.5))
TL.layer(Pop(t + 0.9, t + L, telop('ゆっくりタイム', 120, fill=(255, 245, 225), inner=(BROWN, 10), outer=None, face=FSB), W // 2, 520, style='fade', inn=0.6, out=0.5))
TL.layer(Pop(t + 1.3, t + L, emoji_img('🍵', 100), 880, 380, inn=0.4))
E.say('M01', t + 1.0)
E.se('chime', t + 0.4, 0.3)
E.music.append(('calm', 0, None))

# ---------------------------------------------------------------- 2. mog-mog
t = TL.t
L = d('M02') + 3.0
TL.add(Clip('IMG_1831.MOV', 4.3, L, zoom=(1.05, 1.15, 0.5, 0.55)))
E.say('M02', t + 0.4)
sprinkle(t + 0.6, t + L, ['もぐもぐ'], [(250, 520), (820, 760), (300, 1100)], step=1.0)

# ---------------------------------------------------------------- 3. pero-pero
t = TL.t
L = d('M03') + 3.0
TL.add(Clip('IMG_3209.MOV', 6.0, L, fy=0.45, zoom=(1.05, 1.18, 0.5, 0.45)))
E.say('M03', t + 0.4)
sprinkle(t + 0.6, t + L, ['ぺろぺろ'], [(820, 520), (240, 820), (800, 1120)], col=(225, 245, 255), edge=(90, 150, 220), step=1.0)

# ---------------------------------------------------------------- 4. rest
t = TL.t
L = d('M04') + 2.2
TL.add(Clip('IMG_1132.MOV', 1.0, min(L, 4.0), hold=max(0, L - 4.0), zoom=(1.0, 1.1, 0.5, 0.55)))
E.say('M04', t + 0.4)
sprinkle(t + 0.8, t + L, ['ふぅ〜'], [(820, 560)], col=(245, 250, 230), edge=(140, 160, 90))

# ---------------------------------------------------------------- 5. petting
t = TL.t
L = d('M05') + 3.2
TL.add(Clip('IMG_1364.MOV', 5.0, min(L, 9.0), hold=max(0, L - 9.0), zoom=(1.0, 1.12, 0.5, 0.5)))
E.say('M05', t + 0.4)
sprinkle(t + 0.8, t + L, ['なでなで', 'うとうと'], [(260, 520), (820, 860)], col=(255, 245, 225), edge=(200, 140, 70), step=1.6)
E.music[-1] = ('calm', E.music[-1][1], t + L)

# ---------------------------------------------------------------- 6. sleep
t = TL.t
L = d('M06') + 6.5
TL.add(Clip('IMG_1360.MOV', 10.0, L, zoom=(1.0, 1.25, 0.55, 0.45)))
for k in range(4):
    TL.layer(Pop(t + 0.8 + k * 1.2, t + L - 0.8, emoji_img('💤', 90 + k * 12), 700 + k * 70, 760 - k * 120, wobble=0.06, inn=0.6, out=0.6))
E.say('M06', t + 2.2)
E.tel('おやすみなさい', t + 2.2, t + L - 0.3, y=500, size=110, fill=(255, 255, 255), inner=((40, 40, 80), 9), outer=None, face=FSB, style='fade')
TL.layer(Pop(t + 2.6, t + L - 0.3, emoji_img('🌙', 110), 870, 360, inn=0.6, wobble=0.03))
E.music.append(('calm', t - 0.5, None))
TL.layer(FadeTo(t + L - 1.6, t + L))

TL.layer(Static(0, TL.t - 1.2, credit_img(), W - credit_img().shape[1] - 40, 124, fade=0))
hdr = label_box('まめすけの日常', 34, bg=(200, 150, 110))
TL.layer(Static(d('M01') + 2.2, TL.t - 1.2, hdr, 40, 120))

E.finish(OUT, sys.argv, bpm=84, bgm_gain=0.55, duck=0.55)
