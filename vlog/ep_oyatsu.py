"""まめすけの日常②「おやつ交渉、その全記録」 縦リール"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *
import sound as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VO = f"{ROOT}/voices/nichijo_oyatsu"
TXT = {l.split('\t')[0]: l.split('\t')[1] for l in open(f"{ROOT}/scripts_txt/nichijo_oyatsu.tsv", encoding='utf-8') if '\t' in l}
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/out/まめすけの日常_おやつ交渉.mp4"
WORK = f"{SCR}/vlog_oyatsu"; os.makedirs(WORK, exist_ok=True)


def d(i):
    p = f"{VO}/{i}.wav"
    return wav_dur(p) if os.path.exists(p) else len(TXT[i]) * 0.14


TL = Timeline(); narr = []; ses = []; music = []   # music: (kind, t0, t1)
SUBY = 1440            # subtitle centre
TOPY = 430             # main telop centre


def say(i, t, sub=True, y=SUBY):
    narr.append((f"{VO}/{i}.wav", t))
    if sub:
        img = subtitle(TXT[i])
        TL.layer(Pop(t, t + d(i) + 0.15, img, W // 2, y, inn=0.12, out=0.1, style='fade'))


def se(name, t, g=1.0, **kw):
    ses.append((S.SE[name](**kw), t, g))


def tel(text, t0, t1, y=TOPY, style='pop', **kw):
    img = telop(text, maxw=980, **kw)
    return TL.layer(Pop(t0, t1, img, W // 2, y, style=style))


# ---------------------------------------------------------------- 1. hook: the stare
L = d('N01') + 0.7
t = TL.add(Clip('IMG_2234.MOV', 0.3, L * 0.8, speed=0.8, fy=0.3, zoom=(1.04, 1.22, 0.5, 0.33)))
say('N01', t + 0.25)
tel('この目、', t + 0.5, t + L, y=330, size=130)
tel('断れますか？', t + 1.5, t + L, y=490, size=150, fill=((255, 255, 255), (255, 210, 225)), inner=((220, 30, 90), 12))
for k in range(int(L / 0.9) + 1): se('heart', t + k * 0.9, 0.9)
hook_end = TL.t

# ---------------------------------------------------------------- 2. title
L = max(2.8, d('N02') + 0.7)
t = TL.add(Clip('IMG_1955.MOV', 0.3, L, zoom=(1.15, 1.25, 0.45, 0.4)))
TL.layer(Blur(t, t + L, sigma=22, dark=0.35, fade=0.15))
TL.layer(Flash(t, 0.3))
TL.layer(Pop(t + 0.05, t + L, label_box('特 集', 64, bg=(215, 25, 45), padx=40, pady=14), W // 2, 640, style='stamp', inn=0.18))
TL.layer(Pop(t + 0.2, t + L, telop('おやつ交渉', 190, maxw=1000, fill=((255, 245, 120), (255, 150, 20)), inner=((110, 30, 0), 14), outer=((255, 255, 255), 16)), W // 2, 860, style='stamp', inn=0.2))
TL.layer(Pop(t + 0.55, t + L, telop('その全記録', 110, fill=(255, 255, 255), inner=((20, 30, 70), 12), outer=None), W // 2, 1060, style='slide', from_dx=-700, inn=0.3))
TL.layer(Pop(t + 0.7, t + L, emoji_img('🍖', 150), 860, 600, rot=-12, inn=0.25))
se('don', t, 1.0); se('kira', t + 0.25, 0.7); se('whoosh', t + 0.5, 0.5)
say('N02', t + 0.35, sub=False)
music.append(('intro', t, t + L))

# ---------------------------------------------------------------- header (from here to the end card)
head_t0 = TL.t
hdr = label_box('まめすけNEWS', 38, bg=(215, 25, 45))
hdr2 = label_box('特集｜おやつ交渉', 38, bg=(18, 32, 78))
note = telop('※実況はフィクションです', 26, fill=(255, 255, 255), inner=((0, 0, 0), 4), outer=None, shadow=0.5, black=False)
credit = telop('VOICEVOX:ずんだもん', 26, fill=(255, 255, 255), inner=((0, 0, 0), 4), outer=None, shadow=0.5, black=False)

# ---------------------------------------------------------------- 3. silent pressure + meter
t = TL.t
a, b = d('N03'), d('N04')
L = min(7.2, a + b + 1.2)
TL.add(Clip('IMG_2234.MOV', 5.0, L, fy=0.35, zoom=(1.0, 1.5, 0.48, 0.42)), whip=True)
se('whoosh', t - 0.15, 0.6)
say('N03', t + 0.2)
tel('無言の圧力', t + 0.35, t + 0.2 + a + 0.2, size=140, fill=((235, 225, 255), (170, 130, 255)), inner=((40, 10, 90), 12))
t4 = t + 0.2 + a + 0.25
say('N04', t4)
TL.layer(Meter(t4 - 0.3, t + L, t4, t4 + 1.5))
se('meter', t4, 0.7, d=1.5); se('kira', t4 + 1.5, 0.8)
music.append(('tense', t, None))

# ---------------------------------------------------------------- 4. the offer: still not moving
t = TL.t
L = d('N05') + 0.7
TL.add(Clip('IMG_1716.MOV', 4.9, L, fx=0.5, zoom=(1.0, 1.18, 0.5, 0.55)))
say('N05', t + 0.2)
tel('まだ動かない…', t + 0.2 + d('N05') * 0.5, t + L, size=120, fill=((220, 245, 255), (120, 200, 255)), inner=((0, 40, 90), 11))
for k in range(int((L - d('N05') * 0.5) / 0.5)):
    se('tick', t + 0.2 + d('N05') * 0.5 + k * 0.5, 0.8)
music[-1] = ('tense', music[-1][1], TL.t)

# ---------------------------------------------------------------- 5. the moment (slow-mo bite → stamp)
t = TL.t
TL.add(Clip('IMG_1131.MOV', 2.7, 1.5, zoom=(1.0, 1.1, 0.35, 0.45)))
say('N06', t + 0.05)
se('roll', t, 0.9, d=1.5 + 1.0)
t5 = TL.t
slow = Clip('IMG_1131.MOV', 4.2, 1.1, speed=0.33, zoom=(1.1, 1.38, 0.3, 0.45), hold=0.35)
TL.add(slow)
se('slow', t5, 0.7)
TL.layer(SpeedLines(t5, t5 + 1.1, 330, 820, inner=380))
tb = t5 + (4.62 - 4.2) / 0.33          # bite moment on the output timeline
TL.layer(Flash(tb, 0.3))
TL.layer(Pop(tb, TL.t + 3.2, telop('交渉成立！', 170, maxw=1000, fill=((255, 255, 255), (255, 225, 230)), inner=((210, 20, 45), 14), outer=((255, 255, 255), 12)), W // 2, 420, style='stamp', inn=0.16))
se('don', tb, 1.0); se('applause', tb + 0.1, 0.5, d=2.0)
say('N07', tb + 0.15)
music.append(('main', tb, None))

# ---------------------------------------------------------------- 6. replay: the tongue
t = TL.t
L = max(3.0, d('N08') + 0.5)
TL.add(Clip('IMG_1131.MOV', 8.85, 1.6, speed=1.6 / L, fx=0.5, zoom=(1.25, 1.55, 0.5, 0.52)), whip=True)
se('whoosh', t - 0.15, 0.6); se('slow', t, 0.5)
TL.layer(Replay(t, t + L))
say('N08', t + 0.2)
TL.layer(Pop(t + L * 0.45, t + L, telop('満足の舌ぺろ', 120, fill=((255, 230, 240), (255, 120, 170)), inner=((150, 0, 60), 11)), W // 2, TOPY + 40, wobble=0.03))
TL.layer(Pop(t + L * 0.5, t + L, emoji_img('😋', 130), 880, TOPY - 110, rot=10))
se('pon', t + L * 0.45, 0.8)

# ---------------------------------------------------------------- 7. every time, a serious match
t = TL.t
L = d('N09') + 0.6
TL.add(Clip('IMG_1735.MOV', 1.3, L, zoom=(1.05, 1.2, 0.55, 0.45)), whip=True)
se('whoosh', t - 0.15, 0.6)
say('N09', t + 0.15)
tel('真剣勝負', t + 0.35, t + L, size=170, fill=((255, 255, 200), (255, 90, 30)), inner=((120, 10, 0), 14))
TL.layer(Pop(t + 0.5, t + L, emoji_img('🔥', 120), 860, TOPY - 120, wobble=0.06))
se('don', t + 0.35, 0.6)

# ---------------------------------------------------------------- 8. ...and the next round starts
t = TL.t
L = min(4.0, d('N10') + 0.5)
TL.add(Clip('IMG_1735.MOV', 13.0, L, zoom=(1.0, 1.12, 0.5, 0.4)))
say('N10', t + 0.15)
tel('おかわり交渉\n開始', t + L * 0.55, t + L, size=110, fill=((255, 255, 255), (200, 255, 210)), inner=((0, 110, 50), 11))
se('pon', t + L * 0.55, 0.8)

# ---------------------------------------------------------------- 9. the sit strategy
t = TL.t
L = min(4.6, d('N11') + 0.8)
TL.add(Clip('IMG_1955.MOV', 6.85 - L, L, zoom=(1.0, 1.25, 0.4, 0.42)))
say('N11', t + 0.15)
TL.layer(Pop(t + 0.3, t + L, label_box('作戦：おすわり', 58, bg=(255, 205, 40), fg=(40, 25, 0), padx=34, pady=14), W // 2, TOPY, style='slide', from_dx=-800, inn=0.3))
se('whoosh', t + 0.3, 0.5)

# ---------------------------------------------------------------- 10. the grab (slow) → 決まったー
t = TL.t
TL.add(Clip('IMG_1955.MOV', 6.85, 0.95, speed=0.3, zoom=(1.0, 1.3, 0.38, 0.4)))
se('slow', t, 0.6); se('roll', t, 0.7, d=0.9)
TL.layer(SpeedLines(t, t + 0.95 / 0.3, 380, 760, inner=420))
tg = t + (7.2 - 6.85) / 0.3
TL.layer(Flash(tg, 0.3))
say('N12', tg - 0.1)
TL.layer(Pop(tg, TL.t + 1.3, telop('決まったー！', 170, maxw=1000, fill=((255, 255, 140), (255, 120, 0)), inner=((140, 20, 0), 14)), W // 2, 420, style='stamp', inn=0.16, rot=-4))
se('don', tg, 1.0); se('applause', tg + 0.1, 0.6, d=2.4)

# ---------------------------------------------------------------- 11. the lick
t = TL.t
TL.add(Clip('IMG_1955.MOV', 9.95, 0.5, speed=0.4, zoom=(1.3, 1.5, 0.45, 0.5)))
TL.layer(Pop(t + 0.1, TL.t, telop('ぺろり', 120, fill=((255, 230, 240), (255, 130, 180)), inner=((150, 0, 60), 11)), 300, 1100, rot=8))
se('pon', t + 0.1, 0.8)

# ---------------------------------------------------------------- 12. celebration ice
t = TL.t
L = d('N13') + 1.2
TL.add(Clip('IMG_3209.MOV', 8.2, L, fy=0.45, zoom=(1.05, 1.2, 0.5, 0.45)), whip=True)
se('whoosh', t - 0.15, 0.6)
say('N13', t + 0.3)
tel('祝杯', t + 0.5, t + L, size=160, fill=((255, 255, 255), (200, 235, 255)), inner=((20, 80, 160), 13))
TL.layer(Pop(t + 0.7, t + L, emoji_img('🍦', 130), 800, TOPY - 100, wobble=0.05))
se('kira', t + 0.5, 0.7)
music[-1] = ('main', music[-1][1], t)
music.append(('calm', t, None))

# ---------------------------------------------------------------- 13. result board + end
t = TL.t
L = d('N14') + 3.2
TL.add(Clip('IMG_3209.MOV', 8.2 + d('N13') + 1.2, min(L, 18.3 - 8.2 - d('N13') - 1.2), fy=0.45, zoom=(1.2, 1.3, 0.5, 0.45),
            hold=max(0, L - (18.3 - 8.2 - d('N13') - 1.2))))
TL.layer(Blur(t + 0.2, t + L + 1, sigma=16, dark=0.5, fade=0.3))
say('N14', t + 0.4, sub=False)
board = rounded_box(900, 760, 40, (255, 255, 255), 238)
TL.layer(Pop(t + 0.3, t + L, board, W // 2, 900, inn=0.25))
TL.layer(Pop(t + 0.35, t + L, label_box('本日の交渉結果', 60, bg=(18, 32, 78), padx=40, pady=14), W // 2, 560, inn=0.25))
rows = ['第1交渉　舌ぺろで成立', '第2交渉　おかわり成立', '第3交渉　おすわり成立']
for k, r in enumerate(rows):
    tk = t + 0.9 + k * 0.45
    TL.layer(Pop(tk, t + L, telop(r, 52, fill=(30, 30, 40), inner=None, outer=None, shadow=0, black=False), W // 2 + 40, 700 + k * 120, style='slide', from_dx=400, inn=0.25))
    TL.layer(Pop(tk + 0.1, t + L, telop('○', 90, fill=(225, 30, 50), inner=None, outer=None, shadow=0), 185, 700 + k * 120, style='stamp', inn=0.15))
    se('pon', tk + 0.1, 0.8)
tw = t + 0.9 + 3 * 0.45 + 0.25
TL.layer(Pop(tw, t + L, telop('全戦全勝', 170, maxw=820, fill=((255, 250, 150), (255, 150, 0)), inner=((150, 30, 0), 14), outer=((255, 255, 255), 14)), W // 2, 1110, style='stamp', inn=0.18, rot=-6))
TL.layer(Flash(tw, 0.25)); se('don', tw, 1.0); se('chime', tw + 0.1, 0.8); se('applause', tw + 0.1, 0.6, d=2.5)
TL.layer(Pop(t + L - 1.6, t + L + 0.01, telop('次回もお楽しみに！', 80, fill=(255, 255, 255), inner=((215, 25, 45), 10), outer=None), W // 2, 1420, inn=0.25))
music[-1] = ('calm', music[-1][1], TL.t)

# header / note / credit layers (added last so they draw on top)
TL.layer(Static(head_t0, t + 0.3, hdr, 40, 140))
TL.layer(Static(head_t0, t + 0.3, hdr2, 40 + hdr.shape[1] + 8, 140))
TL.layer(Static(head_t0, TL.t, note, 44, 140 + hdr.shape[0] + 8))
TL.layer(Static(0, TL.t, credit, W - credit.shape[1] - 30, 1860 - credit.shape[0], fade=0))

# ---------------------------------------------------------------- music
total = TL.t
bgm = np.zeros(int((total + 3) * S.SR))
for kind, a, b in music:
    if b is None: b = total
    bars = int(math.ceil((b - a) / (4 * 60 / 112))) + 1
    sec = S.bgm_section(kind, bars, 112)
    n = int((b - a) * S.SR); sec = sec[:n + int(0.6 * S.SR)]
    fo = int(0.5 * S.SR); sec[-fo:] *= np.linspace(1, 0, fo)
    S.place(bgm, sec * (0.85 if kind == 'tense' else 1.0), a)
bgm = S.norm(bgm, 0.8)

print(f"timeline {total:.1f}s, clips {len(TL.clips)}, layers {len(TL.layers)}")
if '--plan' in sys.argv: sys.exit()
mix(total, narr, ses, bgm, bgm_gain=0.5, duck=0.42, out=f"{WORK}/mix.wav")
loudnorm(f"{WORK}/mix.wav", f"{WORK}/mix_ln.wav", I=-14)
TL.render(OUT, f"{WORK}/mix_ln.wav")
print("done", OUT)
