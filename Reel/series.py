#!/usr/bin/env python3
"""Цуврал: бүх видеог #1, #2, #3 … гэж дугаарлаж, үг / энгийн үг / дүрэм / яриа / тон / шалгалтыг хооронд нь холбоно.

Дугаарлалт
  Төрөл бүр өөрийн #1, #2, #3 … дугаартай (файлын нэр, дэлгэцийн баруун дээд булан, тайлбар дээр):
    word (Үг) · group (Энгийн үг, 5-аар) · grammar (Дүрэм) · scene (Яриа)
  Дугаар нь `reels` салбар дахь `series.json`-д хадгалагдана; видео АМЖИЛТТАЙ үүссэний дараа л нэмэгдэнэ.
  Анх удаа ажиллахад хуучин state файлуудаас (state.json, grammar-state.json …) дугаараа үргэлжлүүлнэ.

Холболт
  level = сүүлд гарсан «Үг» видеоны HSK түвшин. Дүрэм, яриа, энгийн үг, шалгалт тэр түвшнийхээс эхэлж сонгогдоно
  (түвшинд үлдсэн зүйл дуусвал хамгийн ойрын түвшнээс). Шалгалт нь зөвхөн аль хэдийн заасан үгээс асууна.
  Видео бүрийн тайлбарт бусад төрлийн одоогийн дугаарыг «Цуврал» мөрөөр харуулна.

Үгийн хуваалт
  «Хэрэгтэй үг» — олон үсэгт үг: нэг үг = нэг видео (жишээ өгүүлбэртэй).
  «Энгийн үг»  — нэг үсэгт үг (SIMPLE_MAX_LEN): 5-аар нэг видеонд, жишээгүй, зөвхөн хятад + пиньинь + орчуулга.
  Гараар засахдаа `Reel/word_overrides.json` дотор simple / needed / skip жагсаалт ашигла.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def out_dir(): return os.environ.get('REEL_OUT') or os.path.join(ROOT, 'reels')

# төрөл: (файлын угтвар, нэр, дэлгэцийн булангийн өнгө)
KINDS = {
    'word':    ('reel',    'Үг',        '#38bdf8'),
    'group':   ('words5',  'Шинэ үгс',  '#a78bfa'),
    'grammar': ('grammar', 'Дүрэм',     '#4ade80'),
    'scene':   ('scene',   'Яриа',      '#fb923c'),
}
ORDER = ('word', 'group', 'grammar', 'scene')
OLD_STATE = {'word': 'state.json', 'grammar': 'grammar-state.json', 'scene': 'scene-state.json'}
GROUP_SIZE = 5
SIMPLE_MAX_LEN = 99         # бүх үг «энгийн» → 5-аар нэг видеонд (олон үсэгт үг ч орно)


def overrides():
    try: d = json.load(open(os.path.join(HERE, 'word_overrides.json'), encoding='utf8'))
    except Exception: d = {}
    return {k: set(d.get(k) or []) for k in ('simple', 'needed', 'skip')}


# ---------- төлөв ----------
def _old(out, kind, field):
    try: return int(json.load(open(os.path.join(out, OLD_STATE[kind]), encoding='utf8')).get(field, 0))
    except Exception: return 0


def load(out=None):
    """series.json-ийг уншина. Байхгүй бол хуучин state файлуудаас дугаарыг нь авч шинээр үүсгэнэ
    (`seed` = хуучин систем хэдэн ширхэг гаргасан). Хуучин «үг»-ийн жагсаалтыг `seed_done`-оор нэг удаа шилжүүлнэ."""
    out = out or out_dir()
    try: st = json.load(open(os.path.join(out, 'series.json'), encoding='utf8'))
    except Exception: st = None
    if not st:
        seed = {k: _old(out, k, 'next') for k in OLD_STATE}
        st = {'v': 2, 'n': {k: seed.get(k, 0) for k in KINDS}, 'seed': seed, 'seeded': [], 'level': 1,
              'done': {}, 'last': {k: _old(out, k, 'last') for k in KINDS if k in OLD_STATE}}
    for k in KINDS: st['n'].setdefault(k, 0); st['last'].setdefault(k, 0)
    st.setdefault('done', {}); st.setdefault('seeded', []); st.setdefault('seed', {})
    return st


def save(st, out=None):
    out = out or out_dir(); os.makedirs(out, exist_ok=True)
    st['updated'] = int(time.time())
    tmp = os.path.join(out, 'series.json.tmp')
    json.dump(st, open(tmp, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(out, 'series.json'))


def seed_done(st, key, ids_in_old_order, count):
    """Хуучин систем (түвшингүй, дарааллаар) эхний `count`-ийг аль хэдийн гаргасан тул `done[key]`-д нэг удаа нэмнэ."""
    if key in st['seeded']: return
    d = st['done'].setdefault(key, [])
    for i in ids_in_old_order[:max(0, int(count))]:
        if i not in d: d.append(i)
    st['seeded'].append(key)


def done(st, key): return set(st['done'].get(key, []))


def init(st, seq):
    """Скрипт бүрийн эхэнд: хуучин «үг»-ийн төлвийг нэг удаа шилжүүлж, одоогийн түвшинг (сүүлд заасан үгийн HSK) тодорхойлно."""
    first = 'word' not in st['seeded']
    seed_done(st, 'word', [w[0] for _, w in seq], st['seed'].get('word', 0))
    if first:
        dn = done(st, 'word'); lv = [l for l, w in seq if w[0] in dn]
        if lv: st['level'] = max(lv)


def mark(st, key, ident, kind=None, level=None, cap=4000):
    d = st['done'].setdefault(key, [])
    if ident not in d: d.append(ident)
    if len(d) > cap: del d[:len(d) - cap]
    if kind and level is not None and kind == 'word': st['level'] = level


def finish(st, kind, key=None, ident=None, level=None):
    """Видео амжилттай үүссэний дараа: дугаар нэмж, заасан зүйлийг тэмдэглэнэ. Түвшин зөвхөн «Үг» видеогоор шилжинэ."""
    st['n'][kind] += 1; st['last'][kind] = int(time.time())
    if key and ident is not None: mark(st, key, ident)
    if kind == 'word' and level is not None: st['level'] = level


# ---------- сонголт ----------
def level_order(levels, L):
    """L түвшнээс эхэлж: L, L-1, L-2 … дараа нь L+1, L+2 …"""
    lvs = sorted(set(levels))
    return [x for x in reversed(lvs) if x <= L] + [x for x in lvs if x > L]


def pick(st, key, items, level_of, id_of, L=None):
    """items-аас `done[key]`-д ороогүй, L түвшинд хамгийн ойр эхний зүйлийг буцаана.
    Бүгд дууссан бол (key-ийн) жагсаалтыг цэвэрлэж дахин эхэлнэ. → (зүйл, дахин_эхэлсэн_эсэх)"""
    L = st.get('level', 1) if L is None else L
    dn = done(st, key); reset = False
    rem = [x for x in items if id_of(x) not in dn]
    if not rem:
        st['done'][key] = []; rem = list(items); reset = True
    for lv in level_order([level_of(x) for x in rem], L):
        for x in rem:
            if level_of(x) == lv: return x, reset
    return rem[0], reset


# ---------- үгийн хуваалт ----------
def split_words(seq, st):
    """seq = [(түвшин, (үг, пиньинь, монгол))] → (needed, simple). Аль хэдийн заасан (done['word']) үгийг алгасна."""
    ov = overrides(); dn = done(st, 'word')
    needed, simple = [], []
    for lv, w in seq:
        h = w[0]
        if h in dn or h in ov['skip']: continue
        is_simple = h in ov['simple'] or (len(h) <= SIMPLE_MAX_LEN and h not in ov['needed'])
        (simple if is_simple else needed).append((lv, w))
    return needed, simple


def next_group(simple, L, size=GROUP_SIZE):
    """Энгийн үгсээс L түвшинд хамгийн ойрын түвшнээс size ширхэг (нэг түвшний дотор) → (түвшин, [үг, ...]) | None"""
    if not simple: return None
    for lv in level_order([l for l, _ in simple], L):
        ws = [w for l, w in simple if l == lv][:size]
        if ws: return lv, ws
    return None


def taught(seq, st):
    """Аль хэдийн заасан үгс (шалгалтад): done['word'] дахь үгс, seq-ийн дарааллаар."""
    dn = done(st, 'word')
    return [(lv, w) for lv, w in seq if w[0] in dn]


# ---------- дугаар, тайлбар ----------
def num(st, kind): return st['n'][kind] + 1          # одоо үүсгэж буй видеоны дугаар
def file_name(kind, n, ext='mp4'): return f'{KINDS[kind][0]}-{n:04d}.{ext}'


def series_line(st, kind, n):
    """Тайлбарын «Цуврал» мөр: энэ видео + бусад төрлийн сүүлд гарсан дугаар.
    Жишээ: 📚 Цуврал · HSK 2 — Үг №109 · Дүрэм №7 · Яриа №32"""
    bits = []
    for k in ORDER:
        c = n if k == kind else st['n'].get(k, 0)
        if c: bits.append(f'{KINDS[k][1]} №{c}')
    return f"📚 Цуврал · HSK {st.get('level', 1)} — " + ' · '.join(bits)


def status():
    sys.path.insert(0, HERE)
    import make_reel as M
    words, _ = M.load(); seq = M.ordered(words)
    st = load()
    seed_done(st, 'word', [w[0] for _, w in seq], st['seed'].get('word', 0))
    needed, simple = split_words(seq, st)
    cnt = lambda L: {lv: sum(1 for l, _ in L if l == lv) for lv in sorted({l for l, _ in L})}
    print('Бүх үг:', len(seq), '| хуучин системээр гарсан:', len(done(st, 'word')))
    print('Хэрэгтэй үг (тус бүр 1 видео):', len(needed), cnt(needed))
    print('Энгийн үг:', len(simple), cnt(simple), f'→ ~{-(-len(simple) // GROUP_SIZE)} видео ({GROUP_SIZE}-аар)')
    print('Дугаарууд:', st['n'], '| түвшин:', st['level'])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'status': status()
    else: print(__doc__)


def too_soon(st, kind, min_gap):
    """min_gap минут болоогүй бол True (workflow-ийн хүснэгт үүнийг хэтэрхий олон видео гаргахаас хамгаална)."""
    return bool(min_gap) and time.time() - st['last'].get(kind, 0) < min_gap * 60


def skip_out():
    go = os.environ.get('GITHUB_OUTPUT')
    if go: open(go, 'a').write('skipped=true\n')
