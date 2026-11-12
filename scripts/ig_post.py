"""Instagram リール自動投稿 (Instagram API with Instagram Login)

posts/<slug>/post.json の publish_at を過ぎた未投稿のリールを投稿し、posts/<slug>/posted.json に結果を書く。
  python scripts/ig_post.py            # 時刻が来たものを投稿
  python scripts/ig_post.py --check    # トークン確認だけ
  python scripts/ig_post.py --now SLUG # 指定の投稿を今すぐ投稿
  python scripts/ig_post.py --refresh  # 長期トークンを更新して標準出力に出す
環境変数: IG_ACCESS_TOKEN (必須), IG_API_VERSION (省略時 v23.0)
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error, datetime, glob

TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
VER = os.environ.get("IG_API_VERSION", "v23.0")
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
# Instagram-login tokens (IGAA...) use graph.instagram.com; Facebook/unified-login tokens (EAA...) use graph.facebook.com
HOST = "graph.facebook.com" if TOKEN.startswith("EAA") else "graph.instagram.com"
G = f"https://{HOST}/{VER}"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(method, url, params=None, data=None, headers=None, timeout=120):
    params = dict(params or {})
    if data is None:                                   # Graph API call: token as a parameter
        params["access_token"] = TOKEN
    q = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(url + "?" + q, headers=headers or {})
    elif data is None:                                 # form POST
        req = urllib.request.Request(url, data=q.encode(), method="POST", headers=headers or {})
    else:                                              # raw upload (token in the Authorization header)
        req = urllib.request.Request(url, data=data, method="POST", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        msg = msg.replace(TOKEN, "***") if TOKEN else msg
        raise SystemExit(f"API error {e.code} on {url.split('?')[0]}: {msg}")


def me():
    if HOST == "graph.facebook.com":
        if not IG_USER_ID:
            raise SystemExit("IG_USER_ID が未設定です")
        r = call("GET", f"{G}/{IG_USER_ID}", {"fields": "id,username"})
        return {"user_id": r["id"], "username": r.get("username")}
    return call("GET", f"{G}/me", {"fields": "user_id,username,account_type"})


def publish(slug):
    d = os.path.join(ROOT, "posts", slug)
    meta = json.load(open(os.path.join(d, "post.json"), encoding="utf-8"))
    caption = open(os.path.join(d, meta.get("caption", "caption.txt")), encoding="utf-8").read().strip()
    video = os.path.join(d, meta.get("video", "video.mp4"))
    ig = me()["user_id"]
    # 1) resumable container
    c = call("POST", f"{G}/{ig}/media", {"media_type": "REELS", "upload_type": "resumable",
                                         "caption": caption, "share_to_feed": "true"})
    cid = c["id"]
    # 2) upload the local file
    size = os.path.getsize(video)
    with open(video, "rb") as f:
        call("POST", f"https://rupload.facebook.com/ig-api-upload/{VER}/{cid}", data=f.read(), timeout=600,
             headers={"Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(size)})
    # 3) wait for processing
    for _ in range(90):
        st = call("GET", f"{G}/{cid}", {"fields": "status_code,status"})
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise SystemExit(f"{slug}: processing failed: {st}")
        time.sleep(10)
    else:
        raise SystemExit(f"{slug}: processing timed out")
    # 4) publish
    mid = call("POST", f"{G}/{ig}/media_publish", {"creation_id": cid})["id"]
    link = call("GET", f"{G}/{mid}", {"fields": "permalink"}).get("permalink", "")
    res = {"media_id": mid, "permalink": link, "posted_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    json.dump(res, open(os.path.join(d, "posted.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"posted {slug}: {link}")
    return res


def due():
    now = datetime.datetime.now(datetime.timezone.utc)
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "posts", "*", "post.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.exists(os.path.join(os.path.dirname(p), "posted.json")):
            continue
        meta = json.load(open(p, encoding="utf-8"))
        if meta.get("hold"):
            continue
        if datetime.datetime.fromisoformat(meta["publish_at"]) <= now:
            out.append(slug)
    return out


if __name__ == "__main__":
    if not TOKEN:
        print("IG_ACCESS_TOKEN が未設定のため何もしません。"); sys.exit(0)
    a = sys.argv[1:]
    if a[:1] == ["--diag"]:
        print("token prefix:", TOKEN[:4], "len", len(TOKEN))
        tries = [("fb /me", "https://graph.facebook.com/v23.0/me", {"fields": "id,name"}),
                 ("fb /me/accounts", "https://graph.facebook.com/v23.0/me/accounts", {"fields": "name,instagram_business_account{id,username}"}),
                 ("fb ig user", f"https://graph.facebook.com/v23.0/{IG_USER_ID}", {"fields": "id,username"}),
                 ("ig /me", "https://graph.instagram.com/v23.0/me", {"fields": "user_id,username,account_type"}),
                 ("fb permissions", "https://graph.facebook.com/v23.0/me/permissions", {}),
                 ("fb debug", "https://graph.facebook.com/v23.0/debug_token", {"input_token": TOKEN}),
                 ("fb me ids", "https://graph.facebook.com/v23.0/me", {"fields": "id,name,instagram_accounts{id,username}"})]
        for name, url, prm in tries:
            try:
                out = json.dumps(call("GET", url, prm), ensure_ascii=False)
                print(name, "->", out.replace(TOKEN, "***")[:1500])
            except SystemExit as e:
                print(name, "-> ERR", str(e)[:400])
    elif a[:1] == ["--check"]:
        m = me(); print(json.dumps(m, ensure_ascii=False))
        lim = call("GET", f"{G}/{m['user_id']}/content_publishing_limit", {"fields": "quota_usage,config"})
        print("publishing limit:", json.dumps(lim, ensure_ascii=False))
    elif a[:1] == ["--refresh"]:
        if HOST == "graph.facebook.com":
            print(TOKEN)   # system-user tokens from unified login do not expire
        else:
            r = call("GET", "https://graph.instagram.com/refresh_access_token", {"grant_type": "ig_refresh_token"})
            print(r["access_token"])
    elif a[:1] == ["--now"]:
        publish(a[1])
    else:
        todo = due()
        print("due:", todo or "なし")
        for s in todo[:3]:          # 1回の実行で最大3本
            publish(s)
