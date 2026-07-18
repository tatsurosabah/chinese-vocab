import json

words = json.load(open('/Users/tatsuro/Documents/Playground/ChineseVocab/words_base.json'))

# normalize category: fullwidth parens -> halfwidth (merges 副詞（時間系）into 副詞(時間系))
for w in words:
    w['cat'] = w['cat'].replace('（','(').replace('）',')')

# compact objects
out = json.dumps(words, ensure_ascii=False, separators=(',',':'))
js = "// 中国語単語アプリ 初期データ（自動生成・編集しない）\nconst SEED_WORDS=" + out + ";\n"
open('/Users/tatsuro/Documents/Playground/ChineseVocab/data.js','w',encoding='utf-8').write(js)

from collections import Counter
cats = Counter(w['cat'] for w in words)
print("words:", len(words), " categories:", len(cats))
print("bytes:", len(js))
