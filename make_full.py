import json, glob, os

BASE = '/Users/tatsuro/Documents/Playground/ChineseVocab'
words = json.load(open(f'{BASE}/words_base.json'))

# collect batch outputs
ex_by_i = {}
mismatch = []
for fp in glob.glob('/tmp/cv_ex/batch_*.json'):
    try:
        arr = json.load(open(fp))
    except Exception as e:
        print("skip (parse err):", fp, e); continue
    for it in arr:
        i = it.get('i')
        if i is None: continue
        ex_by_i[i] = {
            'ex': (it.get('ex') or '').strip(),
            'exPinyin': (it.get('exPinyin') or '').strip(),
            'exEn': (it.get('exEn') or '').strip(),
        }
        # sanity: hanzi match
        if 0 <= i < len(words) and it.get('hanzi') and it['hanzi'] != words[i]['hanzi']:
            mismatch.append((i, it.get('hanzi'), words[i]['hanzi']))

filled = 0
missing = []
for i, w in enumerate(words):
    e = ex_by_i.get(i)
    if e and e['ex']:
        w['ex'] = e['ex']; w['exPinyin'] = e['exPinyin']; w['exEn'] = e['exEn']
        filled += 1
    else:
        missing.append(i)
    # normalize category parens
    w['cat'] = w['cat'].replace('（','(').replace('）',')')

print(f"total words: {len(words)}")
print(f"filled with examples: {filled}")
print(f"missing: {len(missing)} -> indices: {missing[:60]}{' ...' if len(missing)>60 else ''}")
print(f"hanzi mismatches: {len(mismatch)} (first 10) {mismatch[:10]}")

# write data.js
out = json.dumps(words, ensure_ascii=False, separators=(',',':'))
open(f'{BASE}/data.js','w',encoding='utf-8').write(
    "// 中国語単語アプリ 初期データ（自動生成・編集しない）\nconst SEED_WORDS=" + out + ";\n")
# also save full base for reference
json.dump(words, open(f'{BASE}/words_full.json','w'), ensure_ascii=False, indent=1)

# emit missing ranges to help re-run
if missing:
    json.dump(missing, open('/tmp/cv_ex_missing.json','w'))
print("wrote data.js")
