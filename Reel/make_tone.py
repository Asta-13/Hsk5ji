#!/usr/bin/env python3
"""Тоны дасгал reel (9:16 mp4): нэг үе (ma, shi, ji ...) — 4 тон — 4 өөр үг. Монгол хүнд хамгийн хэцүү хэсэг.
Хэрэглээ: python3 Reel/make_tone.py [--silent] [--min-gap МИНУТ] [--index N]"""
import argparse, json, os, subprocess, sys, tempfile, time
import make_reel as M
import make_quiz as Q
from make_reel import W, H, cfont, font, bg, center, say, join, probe, silence, SITE, ZH_VOICE, MN_VOICE, MN_RATE

OUT = M.OUT
STATE = os.path.join(OUT, 'tone-state.json')
# (үе, [(тон, үсэг, монгол утга)])  — аль ч олон дуудлагатай (多音字) үсгийг зориудаар оруулаагүй
SETS = [
    ('ma', [(1, '妈', 'ээж'), (2, '麻', 'олсны ургамал, мөн мэдээ алдах'), (3, '马', 'морь'), (4, '骂', 'загнах')]),
    ('shi', [(1, '诗', 'шүлэг'), (2, '十', 'арав'), (3, '史', 'түүх'), (4, '是', 'байх (тийм)')]),
    ('ji', [(1, '鸡', 'тахиа'), (2, '极', 'туйлын'), (3, '几', 'хэдэн'), (4, '记', 'санах')]),
    ('wen', [(1, '温', 'дулаан'), (2, '文', 'бичиг, соёл'), (3, '吻', 'үнсэх'), (4, '问', 'асуух')]),
    ('tang', [(1, '汤', 'шөл'), (2, '糖', 'чихэр'), (3, '躺', 'хэвтэх'), (4, '烫', 'халуун, түлэгдэх')]),
    ('qi', [(1, '七', 'долоо'), (2, '骑', 'унах'), (3, '起', 'босох'), (4, '气', 'уур, хий')]),
    ('ba', [(1, '八', 'найм'), (2, '拔', 'татах'), (3, '把', 'барих'), (4, '爸', 'аав')]),
    ('guo', [(1, '锅', 'тогоо'), (2, '国', 'улс'), (3, '果', 'жимс'), (4, '过', 'өнгөрөх')]),
    ('bao', [(1, '包', 'цүнх'), (2, '雹', 'мөндөр'), (3, '饱', 'цатсан'), (4, '抱', 'тэвэрэх')]),
    ('shu', [(1, '书', 'ном'), (3, '鼠', 'хулгана'), (4, '树', 'мод')]),
    ('xiao', [(1, '消', 'арилах'), (3, '小', 'жижиг'), (4, '笑', 'инээх')]),
    ('yu', [(2, '鱼', 'загас'), (3, '雨', 'бороо'), (4, '玉', 'хаш чулуу')]),
    ('mai', [(3, '买', 'худалдан авах'), (4, '卖', 'зарах')]),
    ('fu', [(1, '夫', 'нөхөр, эр хүн'), (2, '福', 'аз жаргал'), (3, '府', 'ордон, засгийн газар'), (4, '父', 'эцэг')]),
    ('gong', [(1, '工', 'ажил'), (3, '巩', 'бэхжүүлэх'), (4, '共', 'нийт')]),
    ('lu', [(2, '炉', 'зуух'), (3, '卤', 'давстай шөлөнд чанах'), (4, '路', 'зам')]),
    ('zhi', [(1, '知', 'мэдэх'), (2, '直', 'шулуун'), (3, '纸', 'цаас'), (4, '志', 'зорилго')]),
    ('yi', [(1, '一', 'нэг'), (2, '姨', 'нагац эгч'), (3, '椅', 'сандал'), (4, '意', 'санаа, утга')]),
    ('hao', [(2, '毫', 'тун багахан'), (3, '好', 'сайн'), (4, '耗', 'үрэх')]),
    ('li', [(2, '梨', 'лийр'), (3, '里', 'дотор'), (4, '力', 'хүч')]),
    ('xi', [(1, '西', 'баруун'), (2, '习', 'дадал, сурах'), (3, '洗', 'угаах'), (4, '细', 'нарийн')]),
    ('yan', [(1, '烟', 'утаа'), (2, '盐', 'давс'), (3, '眼', 'нүд'), (4, '验', 'шалгах')]),
    ('dian', [(3, '点', 'цэг'), (4, '电', 'цахилгаан')]),
    ('tong', [(1, '通', 'дамжих'), (2, '同', 'адил'), (3, '桶', 'хувин'), (4, '痛', 'өвдөх')]),
    ('zhong', [(1, '终', 'төгсгөл'), (3, '肿', 'хавдах'), (4, '众', 'олон')]),
    ('fei', [(1, '飞', 'нисэх'), (2, '肥', 'тарган'), (3, '匪', 'дээрэмчин'), (4, '费', 'зардал')]),
    ('bai', [(2, '白', 'цагаан'), (3, '百', 'зуу'), (4, '拜', 'мөргөх')]),
    ('ting', [(1, '听', 'сонсох'), (2, '停', 'зогсох'), (3, '挺', 'нэлээд')]),
    ('jiao', [(1, '交', 'өгөх, харилцах'), (3, '脚', 'хөл'), (4, '叫', 'дуудах, нэрлэх')]),
    ('gao', [(1, '高', 'өндөр'), (3, '搞', 'хийх'), (4, '告', 'хэлэх, мэдэгдэх')]),
    ('shan', [(1, '山', 'уул'), (3, '闪', 'гялалзах'), (4, '善', 'сайн сэтгэлтэй')]),
    ('huo', [(2, '活', 'амьд, амьдрах'), (3, '火', 'гал'), (4, '货', 'бараа')]),
    ('dou', [(1, '兜', 'халаас'), (3, '抖', 'чичрэх'), (4, '豆', 'буурцаг')]),
    ('pao', [(1, '抛', 'шидэх'), (2, '袍', 'дээл'), (3, '跑', 'гүйх'), (4, '炮', 'их буу')]),
    ('fan', [(1, '翻', 'эргүүлэх'), (2, '烦', 'зовлон, санаа зовох'), (3, '反', 'эсрэг'), (4, '饭', 'хоол')]),
    ('mi', [(2, '迷', 'төөрөх, дурлах'), (3, '米', 'будаа'), (4, '密', 'нууц')]),
    ('yao', [(1, '腰', 'бэлхүүс'), (2, '摇', 'сэгсрэх'), (3, '咬', 'хазах'), (4, '药', 'эм')]),
    ('wan', [(1, '弯', 'муруй'), (2, '玩', 'тоглох'), (3, '晚', 'орой'), (4, '万', 'түм')]),
    ('chi', [(1, '吃', 'идэх'), (2, '迟', 'хоцрох'), (3, '尺', 'шугам, хэмжүүр'), (4, '赤', 'улаан')]),
    ('ren', [(2, '人', 'хүн'), (3, '忍', 'тэвчих'), (4, '认', 'таних')]),
    ('lan', [(2, '蓝', 'цэнхэр'), (3, '懒', 'залхуу'), (4, '烂', 'ялзрах, муудах')]),
    ('chuan', [(1, '穿', 'өмсөх'), (2, '船', 'завь'), (3, '喘', 'амьсгаадах'), (4, '串', 'зүүлт, цуваа')]),
    ('hua', [(1, '花', 'цэцэг'), (2, '滑', 'гулгамтгай'), (4, '话', 'үг, яриа')]),
    ('jian', [(1, '尖', 'үзүүртэй'), (3, '剪', 'хайчлах'), (4, '见', 'уулзах, харах')]),
    ('tou', [(1, '偷', 'хулгайлах'), (2, '头', 'толгой'), (4, '透', 'нэвт, тунгалаг')]),
    ('shui', [(2, '谁', 'хэн'), (3, '水', 'ус'), (4, '睡', 'унтах')]),
    ('hu', [(1, '呼', 'дуудах, амьсгалах'), (2, '湖', 'нуур'), (3, '虎', 'бар'), (4, '户', 'айл өрх')]),
    ('ye', [(1, '椰', 'наргил'), (2, '爷', 'өвөө'), (3, '也', 'бас'), (4, '夜', 'шөнө')]),
    ('you', [(1, '优', 'онц, давуу'), (2, '油', 'тос'), (3, '有', 'байх'), (4, '右', 'баруун тал')]),
]
TONE_NAME = {1: '1-р тон (өндөр, тэгш)', 2: '2-р тон (дээш өгсөх)', 3: '3-р тон (доош дээш)', 4: '4-р тон (огцом буух)'}
TCOL = {1: '#f472b6', 2: '#38bdf8', 3: '#4ade80', 4: '#facc15'}

def py(syl, t): return Q.put_tone(syl, t)

def panel(path, syl, rows, upto, cur):
    """rows: [(tone, char, mn)]; upto: хэдэн мөр харагдах; cur: яг одоо дуугарч буй мөр (1 эсвэл -1)"""
    im, d = bg()
    center(d, 'ТОНЫ ДАСГАЛ', 100, cfont(56), '#93c5fd')
    center(d, syl, 230, cfont(190), '#facc15')
    center(d, 'Ижил үе — өөр тон — өөр утга', 480, cfont(46), '#bfdbfe')
    n = len(rows); h = 250 if n <= 3 else 235; y = 600
    for i, (t, ch, mn) in enumerate(rows):
        if i >= upto: break
        on = i == cur
        d.rounded_rectangle([60, y, W - 60, y + h - 20], 44, fill='white' if on else '#1e3a8a', outline=TCOL[t], width=10 if on else 6)
        d.ellipse([90, y + 55, 90 + 110, y + 165], fill=TCOL[t])
        nf = cfont(70); nw = d.textlength(str(t), font=nf); d.text((145 - nw / 2, y + 62), str(t), font=nf, fill='#0f172a')
        d.text((240, y + 8), ch, font=font(100), fill='#0f172a' if on else 'white')
        d.text((420, y + 38), py(syl, t), font=cfont(78), fill='#2563eb' if on else '#fde68a')
        mf = cfont(40); m = mn if len(mn) <= 28 else mn[:27] + '…'
        d.text((240, y + 148), m, font=mf, fill='#475569' if on else '#bae6fd')
        y += h
    center(d, SITE, 1775, cfont(42), '#facc15'); im.save(path)

def cta(path):
    im, d = bg()
    for i, l in enumerate(['Аль тон танд', 'хамгийн хэцүү вэ?']): center(d, l, 600 + i * 100, cfont(66), '#bfdbfe')
    center(d, 'Комментд 1, 2, 3, 4 гэж бич!', 900, cfont(56), '#facc15')
    center(d, 'Өдөр бүр шинэ хичээл', 1150, cfont(56), 'white'); center(d, SITE, 1775, cfont(42), '#facc15'); im.save(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--silent', action='store_true'); ap.add_argument('--min-gap', type=int, default=0); ap.add_argument('--index', type=int)
    a = ap.parse_args(); M.start_watchdog()
    try: st = json.load(open(STATE))
    except Exception: st = {}
    if a.min_gap and time.time() - st.get('last', 0) < a.min_gap * 60:
        print('Алгасав'); go = os.environ.get('GITHUB_OUTPUT')
        if go: open(go, 'a').write('skipped=true\n')
        return
    idx = a.index if a.index is not None else st.get('next', 0)
    syl, rows = SETS[idx % len(SETS)]
    print('Тон:', syl, [py(syl, t) for t, _, _ in rows])
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        P = lambda n: os.path.join(tmp, n)
        c = lambda t, v, r, i: say(t, v, r, tmp, i, a.silent)
        zs = [c(ch, ZH_VOICE, '-20%', 10 + i) for i, (t, ch, mn) in enumerate(rows)]
        ms = [c(mn.split(',')[0], MN_VOICE, MN_RATE, 20 + i) for i, (t, ch, mn) in enumerate(rows)]
        if M.TTS_FAIL and not a.silent: sys.exit('Дуу үүсгэж чадсангүй: ' + ', '.join(M.TTS_FAIL))
        gap = P('g.wav'); silence(gap, 0.45); segs = []
        for i in range(len(rows)):
            aud = P(f'a{i}.wav'); join([zs[i], gap, zs[i], gap, ms[i]], 0, aud); k = int(probe(aud)) + 1; imgs = []
            for j in range(k): panel(P(f'p{i}_{j}.png'), syl, rows, i + 1, i); imgs.append(P(f'p{i}_{j}.png'))
            segs.append(Q.segment(tmp, f's{i}', imgs, aud))
        # давталт: бүх тоныг дараалан хурдан (хариуг мэдэх)
        gp2 = P('g2.wav'); silence(gp2, 0.35); aud = P('rep.wav'); join(zs, 0, aud)
        # үсэг тус бүрийн хооронд богино зай
        parts = []
        for i, z in enumerate(zs): parts += [z] + ([gp2] if i < len(zs) - 1 else [])
        join(parts, 0, aud); k = int(probe(aud)) + 1; imgs = []
        for j in range(k): panel(P(f'r{j}.png'), syl, rows, len(rows), -1); imgs.append(P(f'r{j}.png'))
        segs.append(Q.segment(tmp, 'rep', imgs, aud))
        cta(P('cta.png')); ac = P('ac.wav'); silence(ac, 3); segs.append(Q.segment(tmp, 'cta', [P('cta.png')], ac))
        lst = P('l.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
        out = os.path.join(OUT, f'tone-{idx % len(SETS) + 1:04d}.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'copy', '-af', M.LOUDNORM,
                        '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-movflags', '+faststart', out], check=True)
    lines = '\n'.join(f'{t}-р тон: {py(syl, t)} {ch} — {mn}' for t, ch, mn in rows)
    cap = (f'🎵 Тоны дасгал: "{syl}"\n\nИжил үе, өөр тон — өөр утга!\n\n{lines}\n\n'
           f'🎯 Аль тон танд хамгийн хэцүү вэ? Комментд бичээрэй!\n💾 Хадгалаад давтаарай ❤️ Найздаа илгээгээрэй\n👉 Үнэгүй сурах сайт: {SITE}\n\n'
           f'{M.TAGS[0]} #тон #pinyin #tones ' + ' '.join(M.TAGS[1:]))
    open(out[:-4] + '.txt', 'w', encoding='utf8').write(cap)
    if not a.silent and a.index is None:
        json.dump({'next': idx + 1, 'last': int(time.time())}, open(STATE, 'w'))
    print('Бэлэн:', out, round(probe(out), 1), 'сек')

if __name__ == '__main__': main()
