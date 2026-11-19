#!/usr/bin/env python3
"""Daily fresh Chinese news -> data/news.json (stdlib only, no API key).
Sources: chinanews.com.cn RSS (world + scroll). Items are filtered for
topic (world / science&space / tech) and for gentle content, then merged
with the previous file (newest first, max KEEP items)."""
import json, re, sys, hashlib, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

OUT = sys.argv[1] if len(sys.argv) > 1 else 'data/news.json'
KEEP = 60
PER_RUN = {'newsw': 4, 'newss': 4, 'newst': 4}
FEEDS = [('https://www.chinanews.com.cn/rss/world.xml', 'newsw'),
         ('https://www.chinanews.com.cn/rss/scroll-news.xml', None)]
SCI = ['科学', '航天', '卫星', '火箭', '太空', '月球', '火星', '天文', '望远镜', '宇航', '空间站', '发现', '研究', '恐龙', '考古', '海洋', '地球', '气候', '动物', '植物', '大熊猫', '生物', '医学']
TECH = ['人工智能', 'AI', '机器人', '芯片', '手机', '科技', '无人机', '新能源', '电动车', '量子', '互联网', '软件', '算法', '高铁', '飞机', '造车']
BAD = ['战争', '袭击', '打击', '空袭', '军事', '军队', '以军', '哈马斯', '胡塞', '死亡', '遇难', '身亡', '伤亡', '失踪', '爆炸', '枪', '杀', '制裁', '导弹', '冲突', '停火', '核', '台湾', '地震', '谴责', '抗议', '逮捕', '诈骗', '丑闻']
DATELINE = re.compile(r'^(?:[一-龥]{2,6}[社网][^电]{0,24}电|综合[^：:]{0,10}[：:])\s*(?:[（(][^）)]{0,30}[）)])?\s*')

def get(u):
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 hsk-news'})
    return urllib.request.urlopen(r, timeout=30).read()

def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    for it in root.iter('item'):
        g = lambda k: (it.findtext(k) or '').strip()
        yield g('title'), g('link'), g('description'), g('pubDate')

def clean(desc, title):
    d = re.sub(r'<[^>]+>', '', desc).replace('　', '').replace('\r', '').strip()
    d = re.sub(r'\s+', ' ', d)
    d = DATELINE.sub('', d).strip()
    m = re.match(r'^(.*?[。！？])', d)
    s = m.group(1) if m else d
    s = s.strip()
    if len(s) < 8 or len(s) > 70:
        s = title.strip()
    return s

def classify(title, feedcat):
    if feedcat:
        return feedcat
    if any(w in title for w in TECH):
        return 'newst'
    if any(w in title for w in SCI):
        return 'newss'
    return None

def ok(text):
    return len(text) <= 80 and not any(b in text for b in BAD)

def collect(fetch=get):
    got, cnt, ids = [], {k: 0 for k in PER_RUN}, set()
    for url, fc in FEEDS:
        try:
            items = list(parse(fetch(url)))
        except Exception as e:
            print('feed fail', url, e); continue
        for title, link, desc, pub in items:
            c = classify(title, fc)
            if not c or cnt[c] >= PER_RUN[c] or not link or hashlib.md5(link.encode()).hexdigest()[:8] in ids:
                continue
            zh = clean(desc, title)
            if not ok(title) or not ok(zh):
                continue
            try:
                d = parsedate_to_datetime(pub).astimezone(timezone(timedelta(hours=8)))
            except Exception:
                d = datetime.now(timezone(timedelta(hours=8)))
            got.append({'id': 'n' + hashlib.md5(link.encode()).hexdigest()[:8], 'cat': c, 'e': {'newsw': '📰', 'newss': '🔭', 'newst': '🤖'}[c],
                        'd': '', 'y': '', 'nd': d.strftime('%m-%d'), 't': title, 'zh': zh, 'mn': '', 'u': link, 'ts': d.isoformat()})
            cnt[c] += 1
            ids.add(got[-1]['id'][1:])
    return got

def main():
    try:
        old = json.load(open(OUT, encoding='utf-8')).get('items', [])
    except Exception:
        old = []
    new = collect()
    seen = {x['id'] for x in new}
    allit = new + [x for x in old if x['id'] not in seen]
    allit.sort(key=lambda x: x.get('ts', ''), reverse=True)
    allit = allit[:KEEP]
    json.dump({'updated': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'items': allit},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('new', len(new), 'total', len(allit))

if __name__ == '__main__':
    main()
