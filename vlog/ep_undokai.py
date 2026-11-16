"""まめすけの日常③「おへや大運動会」 スポーツ中継風"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epkit import *

E = Ep('nichijo_undokai'); TL = E.TL; d = E.d
OUT = next((a for a in sys.argv[1:] if not a.startswith('--')), "/home/claude/out/まめすけの日常_おへや大運動会.mp4")
NAVY, RED, GOLD = (18, 32, 78), (215, 25, 45), (255, 205, 40)


def event_label(t0, t1, no, name):
    a = label_box(no, 40, bg=GOLD, fg=(30, 20, 0), padx=22, pady=10)
    b = label_box(name, 46, bg=NAVY, padx=26, pady=10)
    img = np.zeros((max(a.shape[0], b.shape[0]), a.shape[1] + b.shape[1], 4), np.uint8)
    img[:a.shape[0], :a.shape[1]] = a; img[:b.shape[0], a.shape[1]:] = b
    TL.layer(Pop(t0, t1, img, 60 + img.shape[1] // 2, 1220, style='slide', from_dx=-900, inn=0.3))
    E.se('whoosh', t0, 0.5)


# ---------------------------------------------------------------- 1. hook + title over a slow-mo dash
L = max(3.2, d('R01') + 0.8)
t = TL.add(Clip('IMG_1624.MOV', 2.0, L * 0.5, speed=0.5, fx=0.45, zoom=(1.0, 1.15, 0.45, 0.5)))
TL.layer(SpeedLines(t, t + L, 520, 1000, inner=420))
E.se('whistle', t + 0.05, 0.7)
E.say('R01', t + 0.5, sub=False)
TL.layer(Flash(t + 0.5, 0.25))
TL.layer(Pop(t + 0.5, t + L, label_box('LIVE', 44, bg=RED, padx=24, pady=8), W // 2, 600, style='stamp', inn=0.15))
TL.layer(Pop(t + 0.6, t + L, telop('おへや', 120, fill=(255, 255, 255), inner=(NAVY, 12), outer=None), W // 2, 720, style='slide', from_dx=-700, inn=0.25))
TL.layer(Pop(t + 0.8, t + L, telop('大運動会', 190, maxw=1000, fill=((255, 245, 120), (255, 140, 0)), inner=((120, 30, 0), 14), outer=((255, 255, 255), 16)), W // 2, 900, style='stamp', inn=0.2))
TL.layer(Pop(t + 1.1, t + L, emoji_img('🏃', 130), 880, 610, rot=-8))
E.se('don', t + 0.8, 1.0); E.se('kira', t + 1.0, 0.6)
E.music.append(('main', t + 0.8, None))
head_t0 = TL.t

# ---------------------------------------------------------------- 2. event 1: living-room laps
t = TL.t
a, b = d('R02'), d('R03')
L = min(5.6, a + b + 0.8)
TL.add(Clip('IMG_1624.MOV', 6.8, L, fx=0.5, zoom=(1.0, 1.12, 0.5, 0.5)), whip=True)
E.se('whoosh', t - 0.15, 0.6)
event_label(t + 0.1, t + L, '第1種目', 'リビング周回走')
E.say('R02', t + 0.15)
t3 = t + 0.15 + a + 0.1
E.say('R03', t3)
TL.layer(SpeedLines(t3, t + L, 540, 900, inner=480))
E.tel('時速 ??? km', t3 + 0.2, t + L, size=110, fill=((255, 255, 255), (180, 235, 255)), inner=((0, 60, 140), 11), wobble=0.03)
for k in range(3): E.se('whoosh', t3 + k * 0.55, 0.35)

# ---------------------------------------------------------------- 3. event 2: sofa landing (slow) + judges
t = TL.t
TL.add(Clip('IMG_1624.MOV', 15.4, 0.8, fx=0.5, zoom=(1.0, 1.06, 0.5, 0.5)), whip=True)
E.se('whoosh', t - 0.15, 0.6)
event_label(t + 0.1, t + 0.8 + 2.2, '第2種目', 'ソファー着地')
E.say('R04', t + 0.15)
ts = TL.t
TL.add(Clip('IMG_1624.MOV', 16.2, 1.0, speed=0.5, fx=0.5, zoom=(1.05, 1.15, 0.55, 0.6), hold=0.3))
E.se('slow', ts, 0.6); E.se('roll', ts, 0.6, d=1.3)
tl = ts + (16.78 - 16.2) / 0.5          # landing
TL.layer(Flash(tl, 0.25)); E.se('boing', tl, 0.8)
t = TL.t
L = d('R05') + 1.6
TL.add(Clip('IMG_1624.MOV', 17.2, min(L, 2.2), fx=0.5, hold=max(0, L - 2.2), zoom=(1.0, 1.05, 0.5, 0.6)))
TL.layer(Pop(t, t + L, label_box('判定', 52, bg=NAVY, padx=34, pady=12), W // 2, 470, style='stamp', inn=0.15))
for k, c in enumerate(judge_cards()):
    TL.layer(Pop(t + 0.25 + k * 0.22, t + L, c, W // 2 + (k - 1) * 290, 660, style='stamp', inn=0.15))
    E.se('pon', t + 0.25 + k * 0.22, 0.9)
E.say('R05', t + 0.25 + 3 * 0.22)
E.tel('満点！', t + 0.25 + 3 * 0.22, t + L, y=880, size=150, fill=((255, 255, 140), (255, 120, 0)), inner=((140, 20, 0), 13), style='stamp')
E.se('applause', t + 0.9, 0.6, d=2.0)

# ---------------------------------------------------------------- 4. feint (play bow)
t = TL.t
L = max(2.8, d('R06') + 0.6)
TL.add(Clip('IMG_1712.MOV', 3.3, L, fx=0.4, zoom=(1.1, 1.3, 0.35, 0.4), shake=6), whip=True)
E.se('whoosh', t - 0.15, 0.6)
E.say('R06', t + 0.15)
E.tel('フェイント！', t + 0.2, t + L, size=150, fill=((255, 230, 255), (220, 110, 255)), inner=((70, 0, 110), 13), rot=-5, wobble=0.04)
E.se('boing', t + 0.2, 0.7); E.se('boing', t + 1.1, 0.5)

# ---------------------------------------------------------------- 5. event 3: ball dribble
t = TL.t
L = min(4.8, d('R07') + 0.7)
TL.add(Clip('IMG_1412.MOV', 0.0, L, fx=0.4, zoom=(1.0, 1.1, 0.4, 0.55)), whip=True)
E.se('whoosh', t - 0.15, 0.6)
event_label(t + 0.1, t + L, '第3種目', 'ボールドリブル')
E.say('R07', t + 0.15)
TL.layer(Pop(t + L * 0.5, t + L, emoji_img('⚽', 110), 820, E.TOPY, wobble=0.06))
E.se('pon', t + L * 0.5, 0.6)

# ---------------------------------------------------------------- 6. final: outdoor fetch
t = TL.t
L = d('R08') + 0.5
TL.add(Clip('IMG_2022.MOV', 2.9, min(3.4, L), fx=0.5, hold=max(0, L - 3.4), zoom=(1.0, 1.7, 0.5, 0.48)), whip=True)
E.se('whoosh', t - 0.15, 0.6)
event_label(t + 0.1, t + L, '最終種目', '屋外ボール回収')
E.say('R08', t + 0.15)
E.music[-1] = ('main', E.music[-1][1], t)
E.music.append(('tense', t, None))
t = TL.t
L = max(2.4, d('R09') + 1.2)
TL.add(Clip('IMG_2022.MOV', 15.5, 2.4, speed=2.4 / L, fx=0.5, zoom=(2.2, 1.0, 0.47, 0.5, ease_in_c)))
E.say('R09', t + L - d('R09') - 0.5)
TL.layer(SpeedLines(t + L - 1.0, t + L, 540, 1000, inner=480))
E.tel('ボール回収 成功！', t + L - 0.9, t + L + 1.0, size=120, fill=((255, 255, 140), (255, 120, 0)), inner=((140, 20, 0), 12), style='stamp')
E.se('don', t + L - 0.9, 0.8)
E.music[-1] = ('tense', E.music[-1][1], t + L - 0.9)

# ---------------------------------------------------------------- 7. victory
t = TL.t
L = d('R10') + 2.4
TL.add(Clip('IMG_1624.MOV', 20.6, min(L, 3.6), fx=0.5, hold=max(0, L - 3.6), zoom=(1.1, 1.25, 0.5, 0.45)))
TL.layer(Confetti(t + 0.3, t + L + 0.1))
TL.layer(Pop(t + 0.3, t + L, emoji_img('🥇', 210), W // 2, 640, style='stamp', inn=0.2))
E.tel('優 勝', t + 0.45, t + L, y=880, size=180, fill=((255, 250, 150), (255, 160, 0)), inner=((150, 30, 0), 14), outer=((255, 255, 255), 16), style='stamp')
E.say('R10', t + 0.5)
E.se('fanfare', t + 0.3, 0.8); E.se('applause', t + 0.4, 0.6, d=3.0)
E.music.append(('main', t + 0.3, None))

# ---------------------------------------------------------------- persistent graphics
hdr = label_box('まめすけNEWS', 38, bg=RED)
hdr2 = label_box('おへや大運動会', 38, bg=NAVY)
live = label_box('● LIVE', 32, bg=(30, 30, 30))
note = small_note('※実況はフィクションです')
TL.layer(Static(head_t0, TL.t, hdr, 40, 140))
TL.layer(Static(head_t0, TL.t, hdr2, 40 + hdr.shape[1] + 8, 140))
TL.layer(Static(head_t0, TL.t, live, W - live.shape[1] - 40, 144))
TL.layer(Static(head_t0, TL.t, note, 44, 140 + hdr.shape[0] + 8))
TL.layer(Static(0, TL.t, credit_img(), 44, 236, fade=0))

E.finish(OUT, sys.argv, bpm=124, bgm_gain=0.5, duck=0.4, gains={'tense': 0.85})
