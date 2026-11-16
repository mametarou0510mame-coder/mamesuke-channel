"""YouTube長尺（横 1920x1080）: 縦動画をコーナーとしてつなぎ、左右にぼかし背景とコーナー表示を置く。
python3 longform.py  → /home/claude/out/YouTube_まめすけアナの日常スペシャル.mp4 + サムネイル + チャプター"""
import os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import telop, label_box, emoji_img, font, FS, FSB, SCR
import sound as S

O = "/home/claude/out"
WORK = f"{SCR}/longform"; os.makedirs(WORK, exist_ok=True)
LW, LH = 1920, 1080
NAVY, RED, GOLD = (18, 32, 78), (215, 25, 45), (255, 205, 40)

SEGS = [  # (file, corner no, title, sub, emoji)
    (f"{O}/special_intro.mp4", None, "まめすけアナの", "日常スペシャル", "📺"),
    (f"{O}/まめすけの日常_おやつ交渉.mp4", 1, "おやつ交渉", "その全記録", "🍖"),
    (f"{O}/まめすけの日常_オフの1日.mp4", 2, "密着", "オフの1日", "📹"),
    (f"{O}/まめすけの日常_おへや大運動会.mp4", 3, "おへや", "大運動会", "🏃"),
    (f"{O}/まめすけの日常_サロン変身.mp4", 4, "サロンの日", "変身ビフォーアフター", "✨"),
    (f"{O}/まめすけの日常_もぐもぐおやすみ.mp4", 5, "もぐもぐ", "そして おやすみ", "💤"),
    (f"{O}/special_outro.mp4", None, "まめすけアナの", "日常スペシャル", "📺"),
]


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))


def paste(dst, rgba, cx, cy):
    im = Image.fromarray(rgba); dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def side_panel(no, title, sub, emo):
    """transparent 1920x1080 overlay: corner info on the left, show logo on the right"""
    im = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))
    cx = (LW - 608) // 4                      # centre of the left side area
    if no:
        paste(im, label_box(f'CORNER {no}', 44, bg=GOLD, fg=(30, 20, 0), padx=30, pady=10), cx, 300)
    paste(im, emoji_img(emo, 130), cx, 440)
    paste(im, telop(title, 74, fill=(255, 255, 255), inner=(NAVY, 9), outer=None, maxw=560), cx, 580)
    paste(im, telop(sub, 64, fill=((255, 245, 150), (255, 170, 30)), inner=((110, 40, 0), 9), outer=None, maxw=560), cx, 690)
    rx = LW - cx
    paste(im, label_box('まめすけNEWS', 56, bg=RED, padx=34, pady=12), rx, 420)
    paste(im, telop('特別編', 60, fill=(255, 255, 255), inner=(NAVY, 8), outer=None), rx, 530)
    paste(im, telop('まめすけアナの日常SP', 44, fill=(255, 255, 255), inner=(NAVY, 7), outer=None), rx, 610)
    return im


def bumper(no, title, sub, emo, d=2.2):
    """corner title card (navy background, slide-in text) as a short mp4 with a whoosh+pon"""
    png = f"{WORK}/bump{no}.png"
    im = Image.new('RGBA', (LW, LH), NAVY + (255,)); dr = ImageDraw.Draw(im)
    for k in range(0, LW + LH, 60):
        dr.line([(k, 0), (k - LH, LH)], fill=(28, 46, 100, 255), width=22)
    paste(im, label_box(f'CORNER {no}', 64, bg=GOLD, fg=(30, 20, 0), padx=40, pady=14), LW // 2, 330)
    paste(im, telop(f'{title}　{sub}', 120, fill=((255, 255, 255), (255, 235, 200)), inner=(RED, 12), outer=((255, 255, 255), 10), maxw=1700), LW // 2, 560)
    paste(im, emoji_img(emo, 170), LW // 2, 790)
    im.convert('RGB').save(png)
    wav = f"{WORK}/bump{no}.wav"
    a = np.zeros(int(d * S.SR)); S.place(a, S.se_whoosh(), 0.0, 0.7); S.place(a, S.se_don(), 0.25, 0.6); S.place(a, S.se_kira(), 0.35, 0.4)
    S.write_wav(wav, S.norm(a, 0.5))
    out = f"{WORK}/bump{no}.mp4"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-t', str(d), '-i', png, '-i', wav,
                    '-filter_complex', f"[0:v]scale={LW}:{LH},zoompan=z='1+0.04*on/{int(d * 30)}':d=1:s={LW}x{LH}:fps=30,fade=in:0:6,fade=out:{int(d * 30) - 6}:6,format=yuv420p[v];[1:a]aresample=48000,aformat=channel_layouts=stereo[a]",
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
    return out


def wide(src, k, no, title, sub, emo):
    png = f"{WORK}/panel{k}.png"; side_panel(no, title, sub, emo).save(png)
    out = f"{WORK}/seg{k}.mp4"
    fc = ("[0:v]split[a][b];[a]scale=1920:-2,crop=1920:1080,gblur=sigma=40,eq=brightness=-0.18:saturation=0.8[bg];"
          "[b]scale=608:1080[fg];[bg][fg]overlay=656:0[m];[m][1:v]overlay=0:0,fps=30,format=yuv420p[v];"
          "[0:a]aresample=48000,aformat=channel_layouts=stereo[a]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', png, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', out], check=True)
    return out


def thumbnail():
    """1280x720 thumbnail: big smiling face + bold title"""
    from engine import Clip
    fr = next(Clip('IMG_1132.MOV', 11.2, 0.2).frames())          # smiling, tongue out (vertical 1080x1920)
    face = Image.fromarray(fr).crop((0, 300, 1080, 1500)).resize((760, 845))
    im = Image.new('RGBA', (1280, 720), (255, 214, 60, 255)); dr = ImageDraw.Draw(im)
    for k in range(0, 2200, 70):
        dr.line([(k, 0), (k - 720, 720)], fill=(255, 196, 30, 255), width=30)
    im.paste(face, (560, -40))
    paste(im, label_box('まめすけNEWS 特別編', 44, bg=RED, padx=24, pady=8), 300, 70)
    paste(im, telop('シーズーの', 96, fill=(255, 255, 255), inner=(NAVY, 12), outer=None, maxw=600), 300, 210)
    paste(im, telop('日常SP', 170, fill=((255, 255, 255), (255, 230, 230)), inner=(RED, 16), outer=((255, 255, 255), 10), maxw=640), 300, 380)
    paste(im, telop('おやつ交渉・運動会\nサロン変身', 50, fill=(255, 255, 255), inner=(NAVY, 8), outer=None, maxw=560), 300, 580)
    p = f"{O}/YouTube_サムネイル_まめすけアナの日常SP.jpg"; im.convert('RGB').save(p, quality=92)
    return p


if __name__ == '__main__':
    parts = []; chapters = []; t = 0.0
    for k, (src, no, title, sub, emo) in enumerate(SEGS):
        if no:
            b = bumper(no, title, sub, emo); chapters.append((t, f"{no}. {title} {sub}")); parts.append(b); t += dur(b)
        elif k == 0:
            chapters.append((0.0, "オープニング"))
        else:
            chapters.append((t, "エンディング"))
        s = wide(src, k, no, title, sub, emo); parts.append(s); t += dur(s)
        print(f"  {os.path.basename(src)} -> {t:.1f}s", flush=True)
    lst = f"{WORK}/list.txt"
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    out = f"{O}/YouTube_まめすけアナの日常スペシャル.mp4"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', out], check=True)
    th = thumbnail()
    ch = '\n'.join(f"{int(a // 60)}:{int(a % 60):02d} {n}" for a, n in chapters)
    json.dump({'duration': dur(out), 'chapters': ch}, open(f"{WORK}/chapters.json", 'w'), ensure_ascii=False, indent=2)
    print(out, th); print(ch)
