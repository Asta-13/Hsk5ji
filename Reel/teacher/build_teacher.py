#!/usr/bin/env python3
"""Ханзи багш (汉字老师) — аппын сахиусыг (js/hanzi.js) видеонд ашиглах PNG болгож хувиргана.
  python3 Reel/teacher/build_teacher.py   → hi.png, cheer.png, think.png (rsvg-convert шаардлагатай)
Зөвхөн дүрээ өөрчлөх үед ажиллуулна; бэлэн PNG-үүд репод хадгалагдсан."""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
SEAL, DARK, GOLD, SKIN = '#C23B22', '#1B2433', '#F3B63F', '#FFDDBF'
ARM = '#8f2a18'

def svg(mood):
    al = {'cheer': 'rotate(125 17 72)', 'think': '', 'hi': ''}.get(mood, '')
    ar = {'cheer': 'rotate(-125 83 72)', 'think': 'rotate(-70 83 72)', 'hi': ''}.get(mood, '')
    eyes = {'cheer': f'<path d="M31 65Q37 55 43 65M57 65Q63 55 69 65" fill="none" stroke="{DARK}" stroke-width="3.2" stroke-linecap="round"/>'}.get(mood) or (
        f'<g transform="translate({2.6 if mood == "think" else 0} {-2.8 if mood == "think" else 0})" fill="{DARK}"><circle cx="37" cy="63" r="3.8"/><circle cx="63" cy="63" r="3.8"/>'
        '<circle cx="38.4" cy="61.6" r="1.2" fill="#fff"/><circle cx="64.4" cy="61.6" r="1.2" fill="#fff"/></g>')
    brow = f'<path d="M57 45Q64 40 71 44" fill="none" stroke="{DARK}" stroke-width="3" stroke-linecap="round"/>' if mood == 'think' else ''
    mouth = {'cheer': f'<path d="M41 78Q50 95 59 78Z" fill="{DARK}"/>',
             'think': f'<path d="M45 83H55" fill="none" stroke="{DARK}" stroke-width="3.2" stroke-linecap="round"/>'}.get(mood,
             f'<path d="M43 80Q50 87 57 80" fill="none" stroke="{DARK}" stroke-width="3.2" stroke-linecap="round"/>')
    spark = (f'<path fill="#FFC93C" d="M10 38l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/><path fill="#FFC93C" d="M92 30l1.6 4 4 1.6-4 1.6-1.6 4-1.6-4-4-1.6 4-1.6z"/>' if mood == 'cheer' else '')
    q = f'<text x="84" y="22" font-size="17" font-weight="900" fill="#fff" font-family="Noto Sans CJK SC, sans-serif">?</text>' if mood == 'think' else ''
    arm = lambda d, cx, tr: f'<g transform="{tr}"><path d="{d}" fill="none" stroke="{ARM}" stroke-width="5.5" stroke-linecap="round"/><circle cx="{cx}" cy="81" r="6" fill="{SKIN}"/></g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 0 116 114" width="464" height="456">
<ellipse cx="50" cy="107" rx="27" ry="3.6" fill="rgba(10,16,30,.25)"/>
<g fill="{DARK}"><ellipse cx="36" cy="102" rx="9" ry="4.4"/><ellipse cx="64" cy="102" rx="9" ry="4.4"/></g>
{arm('M17 72Q8 74 7 80', 7, al)}{arm('M83 72Q92 74 93 80', 93, ar)}
<g transform="rotate(-3 50 66)">
<rect x="14" y="28" width="72" height="72" rx="21" fill="{SEAL}"/>
<text x="50" y="90" text-anchor="middle" font-size="60" font-weight="900" fill="#fff" opacity=".17" font-family="Noto Sans CJK SC, sans-serif">字</text>
<path d="M22 48Q22 35 36 34L54 34Q31 39 27 60Z" fill="#fff" opacity=".16"/>
<rect x="20" y="34" width="60" height="60" rx="15" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="1.6"/>
<g fill="#FFC4B2" opacity=".85"><circle cx="26" cy="78" r="4.4"/><circle cx="74" cy="78" r="4.4"/></g>
<g fill="rgba(255,255,255,.95)" stroke="{DARK}" stroke-width="2.6"><circle cx="37" cy="62" r="10.5"/><circle cx="63" cy="62" r="10.5"/></g>
<path d="M47.5 61.5Q50 59.5 52.5 61.5M26.5 60L21 57.5M73.5 60L79 57.5" fill="none" stroke="{DARK}" stroke-width="2.4" stroke-linecap="round"/>
{eyes}{brow}{mouth}
<path d="M29 30v7Q50 45 71 37v-7z" fill="#101B47" stroke="#fff" stroke-opacity=".14"/>
<path d="M50 9L91 23L50 37L9 23Z" fill="#1B2D6B" stroke="#fff" stroke-opacity=".2" stroke-width="1.2" stroke-linejoin="round"/><circle cx="50" cy="23" r="2.6" fill="{GOLD}"/>
<path d="M84 25L86 43" stroke="{GOLD}" stroke-width="2" stroke-linecap="round"/><circle cx="86" cy="46" r="3.2" fill="{GOLD}"/>
</g>{spark}{q}</svg>'''

if __name__ == '__main__':
    for m in ('hi', 'cheer', 'think'):
        p = os.path.join(HERE, m + '.svg'); open(p, 'w', encoding='utf8').write(svg(m))
        subprocess.run(['rsvg-convert', '-w', '420', '-o', os.path.join(HERE, m + '.png'), p], check=True); os.remove(p)
        print('OK', m)
