# -*- coding: utf-8 -*-
"""每個場景的動畫。函式名稱對應 script.md 的「## S1」等代號；c[k] 是第 k 句旁白開始的秒數。"""
from vidkit import *


def s1(sc):
    c = sc.cues
    sc.add(Title(text='停止過戶是什麼？', xy=(MARGIN, 110), at=0))
    sc.add(Box(rect=(MARGIN, 300, W // 2 - 40, 640), color='blue', at=c[0]),
           Text(text='股東會之前\n停止辦理過戶', xy=(W // 4 + 30, 470), anchor='mm', size=SIZE['h2'], at=c[0] + 0.2))
    sc.add(Box(rect=(W // 2 + 40, 300, W - MARGIN, 470), color='green', fill=True, at=c[1]),
           Text(text='○ 可以買賣', xy=(W * 3 // 4 - 30, 385), anchor='mm', size=SIZE['h2'], at=c[1] + 0.2))
    sc.add(Box(rect=(W // 2 + 40, 490, W - MARGIN, 640), color='red', fill=True, at=c[1] + 1.2),
           Text(text='× 這次不能投票', xy=(W * 3 // 4 - 30, 565), anchor='mm', size=SIZE['h2'], at=c[1] + 1.4))


def s2(sc):
    c = sc.cues
    sc.add(Title(text='期間長短（公司法§165）', xy=(MARGIN, 110), at=0))
    cols = [('公開發行', 'yellow', 60, 30, c[0]), ('非公開發行', 'blue', 30, 15, c[1])]
    for i, (name, col, reg, extra, at) in enumerate(cols):
        x = MARGIN + 60 + i * 860
        sc.add(Text(text=name, xy=(x, 290), size=SIZE['h2'], weight='bold', color=col, at=at))
        sc.add(Text(text='股東常會', xy=(x, 400), color='muted', at=at + 0.3))
        sc.add(Counter(a=0, b=reg, fmt='{:.0f}日', xy=(x + 480, 430), size=96, color=col, at=at + 0.3, dur=1.2))
        sc.add(Text(text='股東臨時會', xy=(x, 560), color='muted', at=at + 0.8))
        sc.add(Counter(a=0, b=extra, fmt='{:.0f}日', xy=(x + 480, 590), size=96, color=col, at=at + 0.8, dur=1.2))


def s3(sc):
    c = sc.cues
    sc.add(Title(text='實例：從開會日往前倒數', xy=(MARGIN, 110), at=0))
    # 時間軸：8月31日到10月15日，共45天
    span = 45   # 8月31日到10月15日
    def u(m, d):
        return ((d if m == 9 else 30 + d) + 0) / span
    tl = sc.add(Timeline(at=c[0], ticks=[(u(9, 9), '', '9月9日', 'r'), (u(9, 10), '', '9月10日', 'l'),
                                          (u(10, 9), '', '10月9日')]))
    x = tl.xpos
    sc.add(Dot(xy=(x(u(10, 9)), tl.y), color='yellow', at=c[0] + 1.0))
    sc.add(Text(text='股東臨時會', xy=(x(u(10, 9)), tl.y - 150), anchor='ma', color='yellow', weight='bold', at=c[0] + 1.0))
    sc.add(Span(xa=x(u(9, 10)), xb=x(u(10, 9)), y=tl.y - 4, label='停止過戶30日', color='red', at=c[1], dur=2.0))
    sc.add(Arrow(p0=(x(u(9, 9)) - 260, tl.y + 220), p1=(x(u(9, 9)) - 60, tl.y + 95), color='green', at=c[2]))
    sc.add(Text(text='最晚過戶日', xy=(x(u(9, 9)) - 270, tl.y + 230), anchor='ma', color='green', weight='bold', at=c[2]))


SCENES = {'S1': s1, 'S2': s2, 'S3': s3}
