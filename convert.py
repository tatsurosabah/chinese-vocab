import csv, re, json

SRC = "/Users/tatsuro/Desktop/Resolution - Copy of 🏷️.csv"

def clean_pinyin(p):
    # remove katakana/hiragana annotations e.g. "zhì(チー) dù"
    p = re.sub(r'[぀-ヿㇰ-ㇿ]+', '', p)
    p = re.sub(r'[（(]\s*[)）]', '', p)   # empty parens left behind
    p = re.sub(r'\s{2,}', ' ', p).strip()
    return p

rows = []
with open(SRC, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for r in reader:
        rows.append(r)

words = []
seen = set()
dropped = 0
dupes = 0
for r in rows:
    if len(r) < 3:
        dropped += 1; continue
    cn = (r[0] or '').strip()
    py = (r[1] or '').strip()
    ja = (r[2] or '').strip()
    typ = (r[3].strip() if len(r) > 3 else '') or '未分類'
    # skip headers / url / empty
    if not cn or cn in ('CN','中文') or 'http' in cn or cn.startswith('中文'):
        dropped += 1; continue
    key = (cn, ja)
    if key in seen:
        dupes += 1; continue
    seen.add(key)
    words.append({
        'hanzi': cn,
        'pinyin': clean_pinyin(py),
        'en': ja,          # meaning kept as-is (mixed JA/EN per user's choice)
        'ex': '', 'exPinyin': '', 'exEn': '',
        'cat': typ,
        'done': False, 'miss': 0
    })

# stats
from collections import Counter
cats = Counter(w['cat'] for w in words)
print("total valid words:", len(words))
print("dropped rows:", dropped, " exact dupes removed:", dupes)
print("categories:", len(cats))
for c, n in cats.most_common():
    print(f"  {c}: {n}")

# save intermediate (no ids yet; ids assigned when building final backup)
json.dump(words, open('/Users/tatsuro/Documents/Playground/ChineseVocab/words_base.json','w'), ensure_ascii=False, indent=1)
print("\nsaved words_base.json")
