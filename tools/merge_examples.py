#!/usr/bin/env python3
"""Merge example batches (word|chinese sentence|mongolian) into data/examples.json.
Usage: python3 tools/merge_examples.py tools/ex_batchN.txt
Existing entries are never overwritten."""
import json, sys, io
p = 'data/examples.json'
raw = open(p, encoding='utf8').read()
d = json.loads(raw)
added = 0
for f in sys.argv[1:]:
    for ln in open(f, encoding='utf8'):
        ln = ln.strip()
        if not ln: continue
        a = ln.split('|')
        assert len(a) == 3 and a[0] in a[1], ('bad line', ln)
        if a[0] not in d:
            d[a[0]] = [a[1], a[2]]; added += 1
compact = raw.count('\n') < 5
open(p, 'w', encoding='utf8').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')) if compact else json.dumps(d, ensure_ascii=False, indent=1))
print('added', added, 'total', len(d))
