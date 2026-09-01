#!/usr/bin/env python3
"""
おすすめ動画(suggest.js)を、厳選チャンネルのRSSから自動生成する。
APIキー不要。既存の「厳選リスト」(curated)は常に残し、新着を上に足す。
使い方: python3 gen_suggest.py
"""
import json, os, re, subprocess, xml.etree.ElementTree as ET
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015',
      'media': 'http://search.yahoo.com/mrss/'}

# チャンネル: (channel_id, 表示分類)
CHANNELS = [
    # ユーザーのプレイリストにあったチャンネル（好みに一致）
    ('UCktwSjzwR09UGVcXed_SwNQ', '会話・インタビュー'),   # Y&K中国語会話
    ('UCLB2Q4jedIYzM5e1VB1HvGA', '会話・インタビュー'),   # WABIKONG 挖金（サバ/マレーシア）
    ('UC0WuM8a8tZd2LZwbxZ-UWxQ', '会話・インタビュー'),   # Irdina Hani
    ('UCWIjH9_kdpKZNM3amX-2Xgg', '会話・インタビュー'),   # Nicole Lee
    ('UCf4Y2w2yFRbSPoRy6SJquGw', 'ニュース・ドキュメンタリー'),  # 小杰不到一百六（街頭インタビュー）
    # 学習・聞き流し系
    ('UC1UH7byhS8TqAHAL0L8IJSA', '学習・聞き流し'),  # 毎日中国語のかね
    ('UCCkyXN56x3AAHR6ApGQhJfA', '学習・聞き流し'),  # 毎日中国語の阿波連
    ('UCI8Liuxdz6UPv5rgMskfwPg', '学習・聞き流し'),  # Learn Chinese Through Podcast
    ('UCyYT-HdG1FXua6_vwyXNqhg', '学習・聞き流し'),  # Chinese Daily Podcast
    ('UCYpxIgKThC92PT3OfrFErQg', '学習・聞き流し'),  # Say Mandarin
    ('UCYqtl651AtrH3Ys5OK-DbbA', '学習・聞き流し'),  # Learn Chinese Online
]
PER_CHANNEL = 6      # 1チャンネルあたり最大何本を採用するか
MAX_TOTAL   = 120    # 全体の上限

def fetch(url):
    # 環境によっては Python の SSL 検証が通らないため curl を使う
    return subprocess.run(['curl', '-sSL', '--max-time', '25',
                           '-A', 'Mozilla/5.0', url],
                          capture_output=True, check=True).stdout

def from_rss():
    out = []
    for cid, kind in CHANNELS:
        try:
            xml = fetch(f'https://www.youtube.com/feeds/videos.xml?channel_id={cid}')
            root = ET.fromstring(xml)
        except Exception as e:
            print(f'  ! {cid} 取得失敗: {e}')
            continue
        author = (root.findtext('a:author/a:name', default='', namespaces=NS) or '').strip()
        n = 0
        for e in root.findall('a:entry', NS):
            vid = e.findtext('yt:videoId', default='', namespaces=NS)
            title = (e.findtext('a:title', default='', namespaces=NS) or '').strip()
            pub = (e.findtext('a:published', default='', namespaces=NS) or '')[:10]
            if not vid or not title:
                continue
            out.append({'vid': vid, 'title': title, 'author': author,
                        'date': pub, 'dur': '', 'kind': kind})
            n += 1
            if n >= PER_CHANNEL:
                break
        print(f'  {author[:22]:24} {n}本  [{kind}]')
    return out

def main():
    print('チャンネルRSSから新着を取得中...')
    fresh = from_rss()

    # 既存の厳選リスト（人手で選んだ良質なもの）は残す
    curated = []
    p = os.path.join(BASE, 'suggest.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8').read()
        m = re.search(r'const SUGGESTED_VIDEOS\s*=\s*(\[.*\])\s*;', s, re.S)
        if m:
            try:
                for v in json.loads(m.group(1)):
                    v.setdefault('date', '')
                    v['curated'] = True
                    curated.append(v)
            except Exception as e:
                print('  ! 既存リストの読み込み失敗:', e)
    print(f'新着 {len(fresh)} 本 / 既存の厳選 {len(curated)} 本')

    # 新着を日付降順、そのあとに厳選。vidで重複除去
    fresh.sort(key=lambda v: v.get('date', ''), reverse=True)
    seen, merged = set(), []
    for v in fresh + curated:
        if v['vid'] in seen:
            continue
        seen.add(v['vid'])
        merged.append(v)
        if len(merged) >= MAX_TOTAL:
            break

    body = json.dumps(merged, ensure_ascii=False, separators=(',', ':'))
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(f'// おすすめ動画（自動生成 {stamp}）\nconst SUGGESTED_VIDEOS={body};\n')
    kinds = {}
    for v in merged:
        kinds[v['kind']] = kinds.get(v['kind'], 0) + 1
    print(f'\nsuggest.js を更新: 合計 {len(merged)} 本  {kinds}')

if __name__ == '__main__':
    main()
