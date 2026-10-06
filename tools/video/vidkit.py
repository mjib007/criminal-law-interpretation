# -*- coding: utf-8 -*-
"""vidkit：逐格繪製的教學解說影片引擎（3b1b 風格）。

流程：script.md（旁白稿）→ 每句語音 → 依語音長度排時間軸 → scenes.py 依句子時間點放動畫元素
     → Pillow 逐格繪製 → ffmpeg 合成 mp4，另輸出 .srt。
規格說明見 repo 根目錄 VIDEO-SPEC.md。
"""
import math, os, re, shutil, subprocess, sys, tempfile, wave, asyncio
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ───────── 畫面規格 ─────────
W, H, FPS = 1920, 1080, 30
MARGIN = 120                      # 左右安全邊界
SUB_BAND = 190                    # 底部字幕帶高度

THEME = {
    'bg':     (17, 20, 24),       # #111418 背景
    'grid':   (32, 37, 44),       # #20252C 淡格線
    'fg':     (236, 239, 244),    # #ECEFF4 主文字
    'muted':  (138, 147, 163),    # #8A93A3 次要文字
    'blue':   (88, 196, 221),     # #58C4DD 主色（概念、時間軸）
    'yellow': (244, 211, 94),     # #F4D35E 強調（關鍵日期、結論）
    'green':  (131, 193, 103),    # #83C167 合法／可以
    'red':    (252, 98, 85),      # #FC6255 違法／不可以
    'sub_bg': (0, 0, 0, 170),     # 字幕底板（半透明黑）
}

SIZE = {'title': 76, 'h2': 56, 'body': 46, 'label': 36, 'small': 30, 'sub': 44}

FONT_CANDIDATES = {
    'regular': [('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'Noto Sans CJK TC'),
                ('C:/Windows/Fonts/msjh.ttc', None),
                ('/System/Library/Fonts/PingFang.ttc', None)],
    'bold':    [('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 'Noto Sans CJK TC'),
                ('C:/Windows/Fonts/msjhbd.ttc', None),
                ('/System/Library/Fonts/PingFang.ttc', None)],
}
_font_cache = {}


def font(size, weight='regular'):
    key = (size, weight)
    if key in _font_cache:
        return _font_cache[key]
    for path, family in FONT_CANDIDATES[weight]:
        if not os.path.exists(path):
            continue
        for idx in range(10):
            try:
                f = ImageFont.truetype(path, size, index=idx)
            except Exception:
                break
            if family is None or f.getname()[0] == family:
                _font_cache[key] = f
                return f
    raise RuntimeError('找不到中文字型，請安裝 Noto Sans CJK TC 或使用微軟正黑體')


# ───────── 緩動函數 ─────────
def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def lerp(a, b, t):
    return a + (b - a) * t


# ───────── 動畫元素 ─────────
@dataclass
class El:
    at: float = 0.0               # 進場時間（秒，場景內）
    dur: float = 0.6              # 進場動畫長度
    until: float = None           # 退場時間（None 表示留到場景結束）

    def progress(self, t):
        return ease_out((t - self.at) / self.dur) if self.dur > 0 else float(t >= self.at)

    def visible(self, t):
        return t >= self.at and (self.until is None or t < self.until + 0.4)

    def alpha(self, t):
        a = clamp((t - self.at) / min(self.dur, 0.5))
        if self.until is not None:
            a *= 1 - clamp((t - self.until) / 0.4)
        return a

    def done(self, t):
        return self.until is None and t >= self.at + self.dur

    def draw(self, d: ImageDraw.ImageDraw, p: float):
        raise NotImplementedError


@dataclass
class Text(El):
    text: str = ''
    xy: tuple = (MARGIN, 120)
    size: int = SIZE['body']
    color: str = 'fg'
    weight: str = 'regular'
    anchor: str = 'la'            # Pillow 錨點：la 左上、ma 中上、mm 正中
    rise: int = 24                # 進場時由下往上滑動的像素

    def draw(self, d, p):
        x, y = self.xy
        d.multiline_text((x, y + (1 - p) * self.rise), self.text, font=font(self.size, self.weight),
                         fill=THEME[self.color], anchor=self.anchor, spacing=14,
                         align='center' if self.anchor[0] == 'm' else 'left')


@dataclass
class Title(Text):
    size: int = SIZE['title']
    weight: str = 'bold'


@dataclass
class Line(El):
    p0: tuple = (0, 0)
    p1: tuple = (100, 0)
    color: str = 'blue'
    width: int = 6

    def draw(self, d, p):
        x = lerp(self.p0[0], self.p1[0], p)
        y = lerp(self.p0[1], self.p1[1], p)
        d.line([self.p0, (x, y)], fill=THEME[self.color], width=self.width)


@dataclass
class Arrow(Line):
    head: int = 22

    def draw(self, d, p):
        super().draw(d, p)
        if p < 0.95:
            return
        (x0, y0), (x1, y1) = self.p0, self.p1
        ang = math.atan2(y1 - y0, x1 - x0)
        pts = [(x1, y1)] + [(x1 - self.head * math.cos(ang + s * 0.45), y1 - self.head * math.sin(ang + s * 0.45))
                            for s in (1, -1)]
        d.polygon(pts, fill=THEME[self.color])


@dataclass
class Box(El):
    rect: tuple = (0, 0, 100, 100)
    color: str = 'blue'
    fill: bool = False
    width: int = 5
    radius: int = 18

    def draw(self, d, p):
        x0, y0, x1, y1 = self.rect
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        s = lerp(0.85, 1.0, p)
        r = (cx - (cx - x0) * s, cy - (cy - y0) * s, cx + (x1 - cx) * s, cy + (y1 - cy) * s)
        if self.fill:
            c = THEME[self.color]
            d.rounded_rectangle(r, self.radius, fill=(c[0], c[1], c[2], 60), outline=c, width=self.width)
        else:
            d.rounded_rectangle(r, self.radius, outline=THEME[self.color], width=self.width)


@dataclass
class Dot(El):
    xy: tuple = (0, 0)
    r: int = 14
    color: str = 'yellow'

    def draw(self, d, p):
        x, y = self.xy
        rr = self.r * (1 + 0.6 * math.sin(math.pi * p))   # 進場時彈一下
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=THEME[self.color])


@dataclass
class Timeline(El):
    """水平時間軸：軸線由左往右畫出，刻度依序出現。
    ticks = [(相對位置0~1, 上方標籤, 下方標籤)] 或 [(位置, 上, 下, 對齊)]，對齊用 'm' 置中、'r' 靠左側、'l' 靠右側。
    兩個刻度很近時，一個用 'r'、一個用 'l'，標籤就不會重疊。"""
    x0: int = MARGIN + 60
    x1: int = W - MARGIN - 60
    y: int = 560
    ticks: list = field(default_factory=list)
    color: str = 'blue'
    dur: float = 1.2

    def xpos(self, u):
        return lerp(self.x0, self.x1, u)

    def draw(self, d, p):
        xe = lerp(self.x0, self.x1, p)
        d.line([(self.x0, self.y), (xe, self.y)], fill=THEME[self.color], width=6)
        if p > 0.98:
            d.polygon([(self.x1 + 26, self.y), (self.x1, self.y - 14), (self.x1, self.y + 14)], fill=THEME[self.color])
        for tk in self.ticks:
            u, top, bottom = tk[:3]
            h = tk[3] if len(tk) > 3 else 'm'
            x = self.xpos(u) + {'m': 0, 'r': -8, 'l': 8}[h]
            if x > xe:
                continue
            xt = self.xpos(u)
            d.line([(xt, self.y - 18), (xt, self.y + 18)], fill=THEME['fg'], width=4)
            if top:
                d.text((x, self.y - 36), top, font=font(SIZE['label']), fill=THEME['muted'], anchor=h + 'd')
            if bottom:
                d.text((x, self.y + 36), bottom, font=font(SIZE['label']), fill=THEME['fg'], anchor=h + 'a')


@dataclass
class Span(El):
    """時間軸上的區間：色塊由右往左（或左往右）長出來，上方標名稱。"""
    xa: float = 0
    xb: float = 100
    y: int = 560
    label: str = ''
    color: str = 'yellow'
    grow: str = 'left'            # left：從 xb 往 xa 長（倒數計算日期用）
    height: int = 70

    def draw(self, d, p):
        c = THEME[self.color]
        if self.grow == 'left':
            a, b = lerp(self.xb, self.xa, p), self.xb
        else:
            a, b = self.xa, lerp(self.xa, self.xb, p)
        d.rectangle((a, self.y - self.height, b, self.y), fill=(c[0], c[1], c[2], 70), outline=c, width=3)
        if self.label and p > 0.6:
            d.text(((self.xa + self.xb) / 2, self.y - self.height - 16), self.label,
                   font=font(SIZE['label'], 'bold'), fill=c, anchor='md')


@dataclass
class Counter(El):
    """數字從 a 跑到 b，例如 0→30 日。"""
    a: float = 0
    b: float = 100
    fmt: str = '{:.0f}'
    xy: tuple = (W // 2, 400)
    size: int = 120
    color: str = 'yellow'

    def draw(self, d, p):
        d.text(self.xy, self.fmt.format(lerp(self.a, self.b, p)), font=font(self.size, 'bold'),
               fill=THEME[self.color], anchor='mm')


# ───────── 場景 ─────────
@dataclass
class Scene:
    sid: str
    heading: str
    lines: list                     # [(字幕, 讀音或 None)]
    cues: list = field(default_factory=list)      # 每句開始秒數（場景內）
    ends: list = field(default_factory=list)      # 每句結束秒數
    duration: float = 0.0
    els: list = field(default_factory=list)

    def add(self, *els):
        self.els.extend(els)
        return els[0] if len(els) == 1 else els


# ───────── 旁白稿解析 ─────────
def parse_script(md_path):
    """script.md 格式：
    # 影片標題
    ## S1 場景標題
    - 字幕句子〔讀：給語音念的寫法〕   ← 〔讀：〕可省略
    """
    title, scenes = '', []
    for raw in Path(md_path).read_text(encoding='utf-8').splitlines():
        s = raw.strip()
        if s.startswith('# '):
            title = s[2:].strip()
        elif s.startswith('## '):
            parts = s[3:].split(None, 1)
            scenes.append(Scene(parts[0], parts[1] if len(parts) > 1 else '', []))
        elif s.startswith('- ') and scenes:
            m = re.match(r'^(.*?)〔讀：(.*?)〕\s*$', s[2:])
            scenes[-1].lines.append((m.group(1).strip(), m.group(2).strip()) if m else (s[2:].strip(), None))
    return title, scenes


# ───────── 語音 ─────────
LEAD, GAP, TAIL = 0.4, 0.3, 0.9   # 場景開頭留白、句間停頓、場景結尾留白（秒）


def speech_text(sub, say):
    t = say or sub
    return t.replace('「', '').replace('」', '').replace('『', '').replace('』', '').replace('§', '第')


def tts_edge(text, mp3, voice, rate, volume):
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, voice, rate=rate, volume=volume).save(str(mp3)))


_melo = None


def tts_melo(text, wav, model_dir):
    """網路擋住 edge-tts 時的離線備用（大陸口音）。需 sherpa-onnx、soundfile、opencc-python-reimplemented。"""
    global _melo
    import sherpa_onnx, soundfile as sf
    from opencc import OpenCC
    d = str(model_dir).rstrip('/') + '/'
    if _melo is None:
        _melo = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=d + 'model.onnx', lexicon=d + 'lexicon.txt', tokens=d + 'tokens.txt', dict_dir=d + 'dict'),
                num_threads=4),
            rule_fsts=','.join(d + f for f in ['date.fst', 'number.fst', 'phone.fst', 'new_heteronym.fst'])))
    t = OpenCC('t2s').convert(text)
    for ch in '：；':
        t = t.replace(ch, '，')
    a = _melo.generate(t, sid=0, speed=1.0)
    sf.write(str(wav), a.samples, a.sample_rate)


def to_wav(src, dst, sr=44100):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(src), '-ar', str(sr), '-ac', '1',
                    '-sample_fmt', 's16', str(dst)], check=True)


def wav_seconds(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def synth_all(scenes, audio_dir, tts):
    """逐句合成語音並排出每個場景的時間軸。回傳 [(wav 路徑, 全片起點秒數)]。"""
    audio_dir.mkdir(parents=True, exist_ok=True)
    clips, offset = [], 0.0
    for si, sc in enumerate(scenes):
        t = LEAD
        sc.cues, sc.ends = [], []
        for li, (sub, say) in enumerate(sc.lines):
            stem = audio_dir / f'{si:02d}_{li:02d}'
            wav = stem.with_suffix('.wav')
            text = speech_text(sub, say)
            if tts['engine'] == 'edge':
                mp3 = stem.with_suffix('.mp3')
                tts_edge(text, mp3, tts['voice'], tts['rate'], tts['volume'])
                to_wav(mp3, wav)
            else:
                tmp = stem.with_name(stem.name + '_raw.wav')
                tts_melo(text, tmp, tts['model'])
                to_wav(tmp, wav)
            dur = wav_seconds(wav)
            sc.cues.append(t)
            sc.ends.append(t + dur)
            clips.append((wav, offset + t))
            print(f'  語音 {si:02d}_{li:02d}  {dur:4.1f} 秒  {sub[:24]}', flush=True)
            t += dur + GAP
        sc.duration = (t - GAP if sc.lines else t) + TAIL
        offset += sc.duration
    return clips, offset


def mix_audio(clips, total, out_wav, sr=44100):
    import array
    buf = array.array('h', [0]) * int(total * sr + sr)
    for wav, start in clips:
        with wave.open(str(wav)) as w:
            data = array.array('h', w.readframes(w.getnframes()))
        i0 = int(start * sr)
        buf[i0:i0 + len(data)] = data
    with wave.open(str(out_wav), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(buf.tobytes())


# ───────── 字幕 ─────────
def wrap(text, f, max_w):
    lines, cur = [], ''
    for ch in text:
        if f.getlength(cur + ch) > max_w and cur:
            # 標點不放行首
            if ch in '，。、；：！？」』）':
                cur, ch = cur[:-1], cur[-1] + ch
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def srt_time(s):
    ms = int(round(s * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def write_srt(scenes, path):
    n, offset, out = 1, 0.0, []
    f = font(SIZE['sub'])
    for sc in scenes:
        for (sub, _), a, b in zip(sc.lines, sc.cues, sc.ends):
            out.append(f'{n}\n{srt_time(offset + a)} --> {srt_time(offset + b + 0.2)}\n'
                       + '\n'.join(wrap(sub, f, W - 2 * MARGIN)) + '\n')
            n += 1
        offset += sc.duration
    Path(path).write_text('\n'.join(out), encoding='utf-8')


# ───────── 逐格繪製 ─────────
def base_frame(sc, brand):
    im = Image.new('RGB', (W, H), THEME['bg'])
    d = ImageDraw.Draw(im)
    for x in range(0, W, 120):                       # 3b1b 式淡格線
        d.line([(x, 0), (x, H)], fill=THEME['grid'], width=1)
    for y in range(0, H, 120):
        d.line([(0, y), (W, y)], fill=THEME['grid'], width=1)
    d.text((W - 60, 40), brand, font=font(SIZE['small']), fill=THEME['muted'], anchor='ra')
    return im


def draw_els(im, els, t):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for e in els:
        a = e.alpha(t)
        if a <= 0:
            continue
        one = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        e.draw(ImageDraw.Draw(one), e.progress(t))
        if a < 1:
            one.putalpha(one.getchannel('A').point(lambda v: int(v * a)))
        layer.alpha_composite(one)
    im.paste(layer, (0, 0), layer)


def draw_subtitle(im, sc, t):
    for (sub, _), a, b in zip(sc.lines, sc.cues, sc.ends):
        if a <= t < b + 0.2:
            f = font(SIZE['sub'])
            lines = wrap(sub, f, W - 2 * MARGIN)
            band = Image.new('RGBA', (W, SUB_BAND), THEME['sub_bg'])
            d = ImageDraw.Draw(band)
            lh = SIZE['sub'] + 18
            y0 = (SUB_BAND - lh * len(lines)) / 2 + lh / 2
            for i, ln in enumerate(lines):
                d.text((W / 2, y0 + i * lh), ln, font=f, fill=THEME['fg'], anchor='mm')
            im.paste(band, (0, H - SUB_BAND), band)
            return


def render(scenes, audio_wav, out_mp4, brand, burn_subs=True):
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-i', str(audio_wav), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '160k',
           '-ar', '44100', '-movflags', '+faststart', '-shortest', str(out_mp4)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for si, sc in enumerate(scenes):
        base = base_frame(sc, brand)
        static, done_n = base.copy(), 0
        nframes = int(round(sc.duration * FPS))
        print(f'  繪製 {sc.sid}  {nframes} 格', flush=True)
        for k in range(nframes):
            t = k / FPS
            done = [e for e in sc.els if e.done(t)]
            if len(done) != done_n:                  # 已完成進場的元素快取成靜態底圖
                static = base.copy()
                draw_els(static, done, t)
                done_n = len(done)
            im = static.copy()
            draw_els(im, [e for e in sc.els if e.visible(t) and not e.done(t)], t)
            if burn_subs:
                draw_subtitle(im, sc, t)
            ff.stdin.write(im.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError('ffmpeg 合成失敗')


# ───────── 預設場景（scenes.py 沒寫到的場景用這個） ─────────
def default_scene(sc):
    sc.add(Title(text=sc.heading, xy=(W // 2, 380), anchor='mm', at=0))
    sc.add(Line(p0=(W // 2 - 300, 460), p1=(W // 2 + 300, 460), color='yellow', at=0.3, dur=0.8))


# ───────── 主程式 ─────────
def build(project_dir, tts, brand='', burn_subs=True):
    project = Path(project_dir)
    sys.path.insert(0, str(project))
    import importlib
    scenes_mod = importlib.import_module('scenes')
    title, scenes = parse_script(project / 'script.md')
    slug = project.name
    out = project / 'out'
    out.mkdir(exist_ok=True)
    print(f'《{title}》共 {len(scenes)} 段，{sum(len(s.lines) for s in scenes)} 句')
    clips, total = synth_all(scenes, out / 'audio', tts)
    for sc in scenes:
        fn = getattr(scenes_mod, 'SCENES', {}).get(sc.sid)
        (fn or default_scene)(sc)
    mix = out / 'audio' / '_mix.wav'
    mix_audio(clips, total, mix)
    write_srt(scenes, out / f'{slug}.srt')
    render(scenes, mix, out / f'{slug}.mp4', brand or title, burn_subs)
    print(f'完成：{out / (slug + ".mp4")}（{total:.1f} 秒）＋ {slug}.srt')
