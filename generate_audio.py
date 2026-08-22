#!/usr/bin/env python3
"""
単語・例文の音声(MP3)を edge-tts で事前生成する。
- ファイル名は本文のハッシュ: audio/<md5(text)[:12]>.mp3
- 既に存在するものはスキップ（= 後から単語を追加しても再実行すれば差分だけ生成）
使い方: python3 generate_audio.py
"""
import asyncio, hashlib, json, os, sys
import edge_tts

BASE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(BASE, 'audio')
VOICE = 'zh-CN-XiaoxiaoNeural'
RATE = '-10%'
CONCURRENCY = 8

def key(text: str) -> str:
    return hashlib.md5(text.strip().encode('utf-8')).hexdigest()[:12]

def collect_texts():
    """data.js の SEED_WORDS から、音声にすべきテキストを集める"""
    src = os.path.join(BASE, 'words_full.json')
    words = json.load(open(src, encoding='utf-8'))
    texts = []
    for w in words:
        for t in (w.get('hanzi'), w.get('ex')):
            if t and t.strip():
                texts.append(t.strip())
    # 重複除去（順序保持）
    seen, out = set(), []
    for t in texts:
        if t not in seen:
            seen.add(t); out.append(t)
    return out

async def synth(text, sem, stats):
    path = os.path.join(AUDIO, f'{key(text)}.mp3')
    if os.path.exists(path) and os.path.getsize(path) > 500:
        stats['skip'] += 1
        return
    async with sem:
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, VOICE, rate=RATE)
                await c.save(path)
                if os.path.getsize(path) > 500:
                    stats['ok'] += 1
                    return
            except Exception as e:
                if attempt == 2:
                    stats['fail'] += 1
                    stats['failed_texts'].append(text)
                    if os.path.exists(path):
                        os.remove(path)
                else:
                    await asyncio.sleep(1.5 * (attempt + 1))

async def main():
    os.makedirs(AUDIO, exist_ok=True)
    texts = collect_texts()
    print(f'対象テキスト: {len(texts)} 件', flush=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    stats = {'ok': 0, 'skip': 0, 'fail': 0, 'failed_texts': []}
    tasks = [synth(t, sem, stats) for t in texts]
    done = 0
    for chunk_start in range(0, len(tasks), 100):
        await asyncio.gather(*tasks[chunk_start:chunk_start + 100])
        done = min(chunk_start + 100, len(tasks))
        print(f'  進捗 {done}/{len(texts)}  生成{stats["ok"]} スキップ{stats["skip"]} 失敗{stats["fail"]}', flush=True)
    print(f'\n完了: 生成{stats["ok"]} スキップ{stats["skip"]} 失敗{stats["fail"]}')
    if stats['failed_texts']:
        json.dump(stats['failed_texts'], open('/tmp/tts_failed.json', 'w'), ensure_ascii=False)
        print('失敗分: /tmp/tts_failed.json')
    # マニフェスト（アプリが存在チェックに使う）
    manifest = sorted({key(t) for t in texts
                       if os.path.exists(os.path.join(AUDIO, f'{key(t)}.mp3'))})
    with open(os.path.join(BASE, 'audio.js'), 'w', encoding='utf-8') as f:
        f.write('// 音声ファイルの一覧（自動生成）\nconst AUDIO_KEYS=' +
                json.dumps(manifest, separators=(',', ':')) + ';\n')
    print(f'audio.js に {len(manifest)} 件を記録')

if __name__ == '__main__':
    asyncio.run(main())
