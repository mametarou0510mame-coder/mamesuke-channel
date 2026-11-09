# 台本(scripts_txt/*.tsv: ID<TAB>セリフ)を VOICEVOX で音声にして voices/<台本名>/<ID>.wav に保存する
import glob, json, os, urllib.parse, urllib.request

ENGINE = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "3"))  # 3 = ずんだもん（ノーマル）
SPEED = float(os.environ.get("VOICEVOX_SPEED", "1.05"))
PITCH = float(os.environ.get("VOICEVOX_PITCH", "0.03"))


def post(path, params, body=None):
    url = f"{ENGINE}{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def synth(text, out):
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    q["speedScale"] = SPEED
    q["pitchScale"] = PITCH
    q["prePhonemeLength"] = 0.05
    q["postPhonemeLength"] = 0.15
    with open(out, "wb") as f:
        f.write(post("/synthesis", {"speaker": SPEAKER}, q))
    # 口パク用: 音素ごとのタイミングを保存
    with open(out[:-4] + ".json", "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False)


for tsv in sorted(glob.glob("scripts_txt/*.tsv")):
    name = os.path.splitext(os.path.basename(tsv))[0]
    os.makedirs(f"voices/{name}", exist_ok=True)
    for line in open(tsv, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or "\t" not in line:
            continue
        lid, text = line.split("\t", 1)
        out = f"voices/{name}/{lid}.wav"
        synth(text, out)
        print("ok", out, text)
