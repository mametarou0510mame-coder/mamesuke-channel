"""共通: エピソード台本からタイムラインを組むための小道具"""
import os, math
import numpy as np
from engine import *
import sound as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Ep:
    def __init__(self, name, suby=1440, topy=430, sub_kw=None):
        self.name = name; self.VO = f"{ROOT}/voices/{name}"
        self.TXT = {l.split('\t')[0]: l.split('\t')[1] for l in open(f"{ROOT}/scripts_txt/{name}.tsv", encoding='utf-8') if '\t' in l}
        self.TL = Timeline(); self.narr = []; self.ses = []; self.music = []
        self.SUBY, self.TOPY = suby, topy; self.sub_kw = sub_kw or {}
        self.WORK = f"{SCR}/vlog_{name}"; os.makedirs(self.WORK, exist_ok=True)

    def d(self, i):
        p = f"{self.VO}/{i}.wav"
        return wav_dur(p) if os.path.exists(p) else len(self.TXT[i]) * 0.14

    def say(self, i, t, sub=True, y=None):
        self.narr.append((f"{self.VO}/{i}.wav", t))
        if sub:
            img = subtitle(self.TXT[i], **self.sub_kw)
            self.TL.layer(Pop(t, t + self.d(i) + 0.2, img, W // 2, y or self.SUBY, inn=0.12, out=0.12, style='fade')).is_sub = True

    def se(self, name, t, g=1.0, **kw):
        self.ses.append((S.SE[name](**kw), t, g))

    def tel(self, text, t0, t1, y=None, style='pop', cx=None, rot=0.0, wobble=0.0, **kw):
        kw.setdefault('maxw', 980)
        return self.TL.layer(Pop(t0, t1, telop(text, **kw), cx or W // 2, y or self.TOPY, style=style, rot=rot, wobble=wobble))

    def build_music(self, bpm=112, gains=None):
        total = self.TL.t; gains = gains or {}
        bgm = np.zeros(int((total + 3) * S.SR))
        for kind, a, b in self.music:
            if b is None: b = total
            bars = int(math.ceil((b - a) / (4 * 60 / bpm))) + 1
            sec = S.bgm_section(kind, bars, bpm)
            n = int((b - a) * S.SR); sec = sec[:n + int(0.6 * S.SR)]
            fi = int(0.05 * S.SR); sec[:fi] *= np.linspace(0, 1, fi)
            fo = int(0.5 * S.SR); sec[-fo:] *= np.linspace(1, 0, fo)
            S.place(bgm, sec * gains.get(kind, 1.0), a)
        return S.norm(bgm, 0.8)

    def finish(self, out, argv, bpm=112, bgm_gain=0.5, duck=0.42, gains=None):
        trim_subs(self.TL.layers)
        total = self.TL.t
        print(f"timeline {total:.1f}s, clips {len(self.TL.clips)}, layers {len(self.TL.layers)}")
        if '--plan' in argv: return
        bgm = self.build_music(bpm, gains)
        mix(total, self.narr, self.ses, bgm, bgm_gain=bgm_gain, duck=duck, out=f"{self.WORK}/mix.wav")
        loudnorm(f"{self.WORK}/mix.wav", f"{self.WORK}/mix_ln.wav", I=-14)
        self.TL.render(out, f"{self.WORK}/mix_ln.wav")
        print("done", out)


def credit_img():
    return telop('VOICEVOX:ずんだもん', 26, fill=(255, 255, 255), inner=((0, 0, 0), 4), outer=None, shadow=0.5, black=False)


def small_note(text):
    return telop(text, 26, fill=(255, 255, 255), inner=((0, 0, 0), 4), outer=None, shadow=0.5, black=False)
