"""まめすけ日常動画用: BGMと効果音をコードで合成する（著作権フリーのオリジナル音源）。
すべて 48kHz mono float32（-1..1）で返す。"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
RNG = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def lp(x, f, o=2):
    return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def env(n, a=0.005, d=0.2, s=0.0, r=0.05, hold=None):
    """simple attack / exp-decay envelope over n samples"""
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0)
    e *= np.exp(-np.maximum(t - a, 0) / max(d, 1e-4)) * (1 - s) + s
    if r and n > int(r * SR):
        e[-int(r * SR):] *= np.linspace(1, 0, int(r * SR))
    return e


def hz(note):
    """'A4' / 'F#3' / midi int -> Hz"""
    if isinstance(note, (int, float)):
        return 440.0 * 2 ** ((note - 69) / 12)
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n = names[note[0]]; i = 1
    if note[1] == '#': n += 1; i = 2
    elif note[1] == 'b': n -= 1; i = 2
    return 440.0 * 2 ** ((n + 12 * (int(note[i:]) + 1) - 69) / 12)


def reverb(x, size=1.2, mix=0.22, damp=5000):
    n = int(size * SR)
    ir = RNG.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.0 / size)
    ir = lp(ir, damp); ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    wet = fftconvolve(x, ir)[:len(x)]
    return x * (1 - mix) + wet * mix * 1.0


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


# ---------------------------------------------------------------- instruments
def pluck(f, d=0.9, bright=0.5):
    """Karplus-Strong plucked string (ukulele-ish)"""
    n = int(d * SR); p = max(2, int(SR / f))
    buf = RNG.uniform(-1, 1, p) * 0.8
    buf = lp(np.concatenate([buf, buf]), 2000 + 6000 * bright)[:p]
    out = np.zeros(n); b = buf.copy(); k = 0
    decay = 0.996
    for i in range(n):
        v = b[k]
        nk = (k + 1) % p
        b[k] = decay * 0.5 * (v + b[nk])
        out[i] = v; k = nk
    return out * env(n, a=0.001, d=d * 0.6, r=0.02)


_pcache = {}


def pluck_c(f, d=0.9, bright=0.5):
    key = (round(f, 2), d, bright)
    if key not in _pcache:
        _pcache[key] = pluck(f, d, bright)
    return _pcache[key]


def glock(f, d=1.2):
    t = t_(d)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)
         + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 14))
    return x * env(len(t), a=0.002, d=0.45, r=0.05)


def bass(f, d=0.4):
    t = t_(d)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sign(np.sin(2 * np.pi * f * t))
    return lp(x, 900) * env(len(t), a=0.004, d=0.25, s=0.35, r=0.04)


def kick(d=0.32, tone=1.0):
    t = t_(d)
    f = 48 + 120 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 9) + 0.25 * lp(RNG.standard_normal(len(t)), 3000) * np.exp(-t * 120)) * tone


def clap(d=0.25):
    t = t_(d); n = RNG.standard_normal(len(t))
    e = np.zeros(len(t))
    for o in (0, 0.009, 0.018):
        i = int(o * SR); e[i:] += np.exp(-np.arange(len(t) - i) / SR * (60 if o < 0.018 else 18))
    return bp(n, 900, 3500) * e * 0.8


def shaker(d=0.07):
    t = t_(d)
    return hp(RNG.standard_normal(len(t)), 6000) * np.exp(-t * 60) * 0.25


def pizz(f, d=0.35):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 for k in range(1, 7))
    return lp(x, 2500) * env(len(t), a=0.003, d=0.09, r=0.03)


def pad(fs, d):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.3 * t)) + 0.4 * np.sin(2 * np.pi * f * 1.003 * t) for f in fs)
    a = np.minimum(t / 0.6, 1) * np.minimum((d - t) / 0.6, 1)
    return lp(x, 1600) * np.clip(a, 0, 1) / len(fs)


def place(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf): return
    e = min(len(buf), i + len(x)); buf[i:e] += x[:e - i] * g


# ---------------------------------------------------------------- BGM
CHORDS = {  # F major, cheerful pet-vlog progression
    'F': ['F3', 'A3', 'C4', 'F4'], 'C': ['E3', 'G3', 'C4', 'E4'], 'Dm': ['D3', 'F3', 'A3', 'D4'],
    'Bb': ['D3', 'F3', 'Bb3', 'D4'], 'Gm': ['D3', 'G3', 'Bb3', 'D4'], 'C7': ['E3', 'Bb3', 'C4', 'E4'],
    'Am': ['E3', 'A3', 'C4', 'E4']}
ROOT = {'F': 'F2', 'C': 'C2', 'Dm': 'D2', 'Bb': 'Bb1', 'Gm': 'G1', 'C7': 'C2', 'Am': 'A1'}
PROG = ['F', 'C', 'Dm', 'Bb', 'F', 'C', 'Bb', 'C7']
# melody per bar: (beat, note, len)
MEL = [[(0, 'C5', 1), (1, 'A4', .5), (1.5, 'C5', .5), (2, 'F5', 1.5)],
       [(0, 'E5', 1), (1, 'D5', .5), (1.5, 'C5', .5), (2, 'G4', 1.5)],
       [(0, 'A4', .5), (.5, 'D5', .5), (1, 'F5', 1), (2, 'E5', .5), (2.5, 'D5', .5), (3, 'C5', 1)],
       [(0, 'D5', 1.5), (2, 'Bb4', .5), (2.5, 'C5', .5), (3, 'D5', 1)],
       [(0, 'C5', 1), (1, 'A4', .5), (1.5, 'C5', .5), (2, 'F5', 1), (3, 'G5', 1)],
       [(0, 'E5', 1), (1, 'G5', .5), (1.5, 'E5', .5), (2, 'C5', 1.5)],
       [(0, 'D5', .5), (.5, 'F5', .5), (1, 'Bb5', 1), (2, 'A5', .5), (2.5, 'G5', .5), (3, 'F5', 1)],
       [(0, 'E5', 1), (1, 'G5', 1), (2, 'C5', 2)]]


def bgm_section(kind, bars, bpm=112, start_bar=0):
    """kind: 'intro' (pluck+glock), 'main' (full band), 'tense' (pizz pulse + heartbeat kick), 'calm' (pad + soft pluck)"""
    beat = 60 / bpm; bar = 4 * beat
    out = np.zeros(int((bars * bar + 2.5) * SR))
    for b in range(bars):
        cb = (start_bar + b) % len(PROG); c = PROG[cb]; t0 = b * bar
        if kind in ('main', 'intro', 'calm'):
            # strum pattern: D . D U . U D U  (8ths)
            pat = [0, 1, 1.5, 2.5, 3, 3.5] if kind != 'calm' else [0, 2]
            for k, bt in enumerate(pat):
                down = k % 2 == 0
                notes = CHORDS[c] if down else CHORDS[c][::-1]
                for j, nn in enumerate(notes):
                    place(out, pluck_c(hz(nn), 0.8 if kind != 'calm' else 1.6, 0.55 if kind != 'calm' else 0.3),
                          t0 + bt * beat + j * 0.011, (0.16 if kind != 'calm' else 0.13) * (1 if down else 0.75))
        if kind == 'calm':
            place(out, pad([hz(n) for n in CHORDS[c][:3]], bar + 0.6), t0, 0.22)
        if kind in ('main', 'intro', 'calm'):
            for bt, nn, ln in MEL[cb]:
                g = 0.30 if kind == 'main' else (0.22 if kind == 'intro' else 0.14)
                if kind == 'calm' and bt % 1: continue
                place(out, glock(hz(nn), max(0.5, ln * beat * 1.6)), t0 + bt * beat, g)
        if kind == 'main':
            for bt in (0, 1.5, 2, 3.5) if b % 2 else (0, 2, 2.5):
                place(out, kick(), t0 + bt * beat, 0.55)
            for bt in (1, 3):
                place(out, clap(), t0 + bt * beat, 0.32)
            for k in range(8):
                place(out, shaker(), t0 + k * beat / 2, 0.5 if k % 2 else 0.3)
            for bt, mul in ((0, 1), (1.5, 1), (2, 1), (3, 2)):
                place(out, bass(hz(ROOT[c]) * mul, beat * 0.9), t0 + bt * beat, 0.42)
        if kind == 'tense':
            root = hz(ROOT[c]) * 2
            for k in range(8):
                place(out, pizz(root if k % 4 != 3 else root * 1.5), t0 + k * beat / 2, 0.30 if k % 2 == 0 else 0.18)
            for bt in (0, 0.33, 2, 2.33):
                place(out, kick(0.25, 0.8), t0 + bt * beat, 0.45 if bt in (0, 2) else 0.3)
            place(out, pad([hz(ROOT[c]) * 4, hz(ROOT[c]) * 6], bar + 0.4), t0, 0.07)
    return reverb(out, 1.0, 0.18)


def bgm(plan, bpm=112):
    """plan: list of (kind, bars). Returns the stitched track and the start time of each section."""
    beat = 60 / bpm; bar = 4 * beat
    total = sum(b for _, b in plan) * bar + 3
    out = np.zeros(int(total * SR)); starts = []; t = 0; sb = 0
    for kind, bars in plan:
        sec = bgm_section(kind, bars, bpm, sb)
        place(out, sec, t, 1.0); starts.append(t)
        t += bars * bar; sb += bars
    # final ring-out chord
    for j, nn in enumerate(CHORDS['F']):
        place(out, pluck(hz(nn), 2.0, 0.5), t + j * 0.02, 0.2)
    place(out, glock(hz('F5'), 2.0), t, 0.3); place(out, glock(hz('C6'), 2.0), t + 0.12, 0.2)
    return norm(out, 0.8), starts


# ---------------------------------------------------------------- sound effects
def se_pop():
    t = t_(0.09); f = 500 + 1400 * (t / 0.09) ** 0.5
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * 0.8


def se_pon():  # cute "ぽん"
    t = t_(0.25); f = 900 * np.exp(-t * 6) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)


def se_whoosh(d=0.45, up=True):
    t = t_(d); n = RNG.standard_normal(len(t)); out = np.zeros(len(t))
    seg = 256
    for i in range(0, len(t), seg):
        p = i / len(t); fc = (400 + 5000 * p) if up else (5400 - 5000 * p)
        out[i:i + seg] = bp(n[max(0, i - 2048):i + seg], max(80, fc * 0.6), min(20000, fc * 1.4))[-len(n[i:i + seg]):]
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return out * e * 1.6


def se_don():  # taiko hit
    t = t_(0.9); f = 70 + 60 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    skin = bp(RNG.standard_normal(len(t)), 150, 900) * np.exp(-t * 30) * 0.6
    return reverb(body + skin, 1.4, 0.3)


def se_kira():
    out = np.zeros(int(1.0 * SR))
    for k, f in enumerate([2093, 2637, 3136, 4186, 3520, 5274]):
        place(out, glock(f, 0.6), k * 0.045, 0.35)
    return reverb(out, 1.2, 0.35)


def se_chime():
    out = np.zeros(int(1.6 * SR))
    for k, n in enumerate(['C6', 'E6', 'G6', 'C7']):
        place(out, glock(hz(n), 1.2), k * 0.09, 0.45)
    return reverb(out, 1.4, 0.3)


def se_roll(d=1.3):
    out = np.zeros(int((d + 0.4) * SR)); t = 0
    while t < d:
        gap = 0.07 - 0.045 * (t / d)
        x = bp(RNG.standard_normal(int(0.08 * SR)), 1500, 6000) * np.exp(-t_(0.08) * 45)
        place(out, x, t, 0.35 + 0.5 * t / d); t += gap
    return out


def se_heart():
    out = np.zeros(int(0.9 * SR))
    place(out, kick(0.3, 1.0), 0, 0.8); place(out, kick(0.3, 1.0), 0.22, 0.55)
    return lp(out, 300)


def se_meter(d=1.4):
    out = np.zeros(int((d + 0.3) * SR)); k = 0; t = 0
    while t < d:
        f = 700 * 2 ** (k / 8)
        x = np.sign(np.sin(2 * np.pi * f * t_(0.05))) * np.exp(-t_(0.05) * 40) * 0.25
        place(out, lp(x, 6000), t, 1.0); t += 0.085; k += 1
    return out


def se_slow():  # "しゅわーん" pitch-down for slow motion
    t = t_(0.7); f = 1600 * np.exp(-t * 3.5) + 120
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bp(RNG.standard_normal(len(t)), 300, 3000) * 0.25
    return reverb(x * np.exp(-t * 2.5) * np.minimum(t / 0.03, 1), 1.0, 0.4)


def se_applause(d=2.2):
    out = np.zeros(int((d + 0.5) * SR))
    for _ in range(int(d * 90)):
        tt = RNG.uniform(0, d)
        x = bp(RNG.standard_normal(int(0.03 * SR)), RNG.uniform(800, 1600), RNG.uniform(2500, 6000)) * np.exp(-t_(0.03) * 120)
        place(out, x, tt, RNG.uniform(0.1, 0.3) * min(1, (d - tt) / 0.8 + 0.2))
    return reverb(out, 1.0, 0.3)


def se_tick():
    t = t_(0.03)
    return hp(RNG.standard_normal(len(t)), 3000) * np.exp(-t * 200) * 0.6


def se_shutter():
    out = np.zeros(int(0.25 * SR))
    place(out, se_tick(), 0, 1.0); place(out, bp(RNG.standard_normal(int(0.06 * SR)), 1500, 7000) * np.exp(-t_(0.06) * 60), 0.06, 0.6)
    return out


SE = {'pop': se_pop, 'pon': se_pon, 'whoosh': se_whoosh, 'don': se_don, 'kira': se_kira, 'chime': se_chime,
      'roll': se_roll, 'heart': se_heart, 'meter': se_meter, 'slow': se_slow, 'applause': se_applause,
      'tick': se_tick, 'shutter': se_shutter}


def write_wav(path, x, sr=SR):
    import wave
    y = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


if __name__ == '__main__':
    import time
    t0 = time.time()
    x, st = bgm([('intro', 2), ('tense', 4), ('main', 8), ('calm', 4)])
    print('bgm', len(x) / SR, 's', st, round(time.time() - t0, 1), 's to build')
    write_wav('/tmp/claude-0/-home-claude/f9d7791f-8b10-5d2c-984e-107435ad121f/scratchpad/bgm_test.wav', x)


def se_whistle(d=0.55):
    t = t_(d); f = 2900 + 120 * np.sin(2 * np.pi * 28 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6 + bp(RNG.standard_normal(len(t)), 2500, 3500) * 0.15
    return x * np.minimum(t / 0.01, 1) * np.minimum((d - t) / 0.05, 1)


def brass(f, d):
    t = t_(d); ph = 2 * np.pi * f * t
    x = sum(np.sin(k * ph) / k for k in range(1, 9))
    return lp(x, 3000) * env(len(t), a=0.03, d=0.8, s=0.6, r=0.08)


def se_fanfare():
    out = np.zeros(int(2.4 * SR)); bt = 0.13
    for k, (n, l) in enumerate([('C5', 1), ('C5', 1), ('C5', 1), ('G5', 4)]):
        tt = sum([1, 1, 1, 4][:k]) * bt
        for m in (0, 4, 7):
            place(out, brass(hz(n) * 2 ** (m / 12) if l > 1 else hz(n), l * bt * 1.4 + (0.6 if l > 1 else 0)), tt, 0.22 if l > 1 else 0.3)
    return reverb(out, 1.2, 0.25)


def se_boing():
    t = t_(0.4); f = 180 + 90 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)


def se_sparkle_up():
    out = np.zeros(int(1.6 * SR))
    for k in range(14):
        place(out, glock(hz(72 + k * 2), 0.5), k * 0.06, 0.25)
    return reverb(out, 1.3, 0.35)


SE.update({'whistle': se_whistle, 'fanfare': se_fanfare, 'boing': se_boing, 'sparkle_up': se_sparkle_up})
