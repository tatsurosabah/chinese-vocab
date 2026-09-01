"""精査結果（意味の日本語化・修正 + 場面タグ）を words_full.json / data.js に反映する。
   - hanzi で突合（インデックスずれに強い）
   - 元の意味は en_old に退避、新しい日本語を en に入れる
   - scene フィールドを追加（品詞カテゴリ cat は温存）
   使い方: python3 apply_review.py  （/tmp/cv_review_done.json と /tmp/cv_review_rest.json を読む）
"""
import json, os, collections

BASE = '/Users/tatsuro/Documents/Playground/ChineseVocab'
words = json.load(open(f'{BASE}/words_full.json'))

rev = {}
for p in ['/tmp/cv_review_done.json', '/tmp/cv_review_rest.json']:
    if not os.path.exists(p):
        print(f'  (skip {p})'); continue
    d = json.load(open(p))
    if isinstance(d, dict):
        rev.update(d)
    else:
        for x in d:
            if x.get('hanzi') and x.get('ja'):
                rev[x['hanzi']] = x
print(f'精査データ: {len(rev)} 語')

applied = fixed = 0
missing = []
for w in words:
    r = rev.get(w['hanzi'])
    if not r:
        missing.append(w['hanzi'])
        w.setdefault('scene', '未分類')
        continue
    w['en_old'] = w['en']          # 元の意味を退避（比較用）
    w['en'] = r['ja']              # 日本語の意味に置き換え
    w['scene'] = r.get('scene') or '未分類'
    if r.get('fixed'):
        fixed += 1
    applied += 1

print(f'反映: {applied} 語 / 実質修正: {fixed} 語 / 未処理: {len(missing)} 語')
if missing:
    print('  未処理例:', missing[:10])

sc = collections.Counter(w.get('scene', '未分類') for w in words)
print('\n場面カテゴリ:')
for k, v in sc.most_common():
    print(f'  {k}: {v}')

json.dump(words, open(f'{BASE}/words_full.json', 'w'), ensure_ascii=False, indent=1)
data = json.dumps(words, ensure_ascii=False, separators=(',', ':'))
open(f'{BASE}/data.js', 'w', encoding='utf-8').write(
    '// 中国語単語アプリ 初期データ（自動生成・編集しない）\nconst SEED_WORDS=' + data + ';\n')
print(f'\nwrote data.js ({len(data)} bytes)')
