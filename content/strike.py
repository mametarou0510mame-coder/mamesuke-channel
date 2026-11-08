# フェイクニュース「全国のシーズー、ちゅーるストライキ」
# (id, 表情, 映像, 字幕, 読み上げ or None)
# 表情: neutral / concern / puzzled / smile / wink
# 映像: anchor / anchor:カード名 / broll:素材名
STRIKE = [
    ("K01", "concern", "anchor:sokuho", "速報です。全国のシーズーたちが、一斉にストライキに突入しました。", None),
    ("K02", "concern", "anchor:sokuho", "原因は、飼い主がちゅーるをくれないことへの不満とみられています。", None),
    ("K03", "neutral", "broll:otete", "ストライキの内容は、「お手」「おすわり」の全面拒否。", "ストライキの内容は、おて、おすわり、の全面拒否。"),
    ("K04", "neutral", "broll:suwarikomi", "さらに一部の地域では、散歩中に突然寝そべる「動かない作戦」も確認されています。", None),
    ("K05", "concern", "anchor:yokyu", "シーズー労働組合は、「ちゅーるを1日3本に増やすこと」を要求しています。", "シーズー労働組合は、ちゅーるを、いちにち、さんぼんに増やすことを、要求しています。"),
    ("K06", "puzzled", "anchor:kosho", "これに対し飼い主側は「あげすぎは体に良くない」と主張。交渉は難航しています。", "これに対し、飼い主側は、あげすぎは体に良くない、と主張。交渉は、難航しています。"),
    ("K07", "neutral", "broll:fukki", "なお、ちゅーるの袋を開ける音がしたとたん、全員が職場に復帰したとの情報が入っています。", None),
    ("K08", "puzzled", "anchor:shuketsu", "……ストライキは、わずか3秒で終わったもようです。", "……ストライキは、わずか、さんびょうで、終わったもようです。"),
    ("K09", "smile", "anchor", "以上、まめすけニュースでした。", None),
    ("K10", "wink", "anchor:bokumo", "……ちなみに、ぼくもストライキ中です。ちゅーる、まだですか？", None),
]

if __name__ == "__main__":
    with open("scripts_txt/strike.tsv", "w", encoding="utf-8") as f:
        for lid, _, _, cap, voice in STRIKE:
            f.write(f"{lid}\t{voice or cap}\n")
    print(len(STRIKE))
