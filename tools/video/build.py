# -*- coding: utf-8 -*-
"""教學影片產生器：投影片 HTML → 截圖，旁白 → 語音，ffmpeg 合成 mp4。

用法（在 repo 根目錄）：
  python tools/video/build.py mistaken_self_defense --voice zh-TW-YunJheNeural --rate +0% \
      --out videos/mistaken-self-defense.mp4

--voice 可用：
  zh-TW-HsiaoChenNeural（A 曉臻，女）、zh-TW-YunJheNeural（B 雲哲，男）、zh-TW-HsiaoYuNeural（C 曉雨，女）
  melo:<模型資料夾>  離線 sherpa-onnx vits-melo-tts-zh_en（大陸口音，網路受限時備用）
需求：pip install edge-tts playwright soundfile numpy ；playwright install chromium ；系統需有 ffmpeg。
"""
import argparse, asyncio, html, importlib, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CSS = """
:root{--navy:#16233b;--blue:#2c4a76;--gold:#a9832f;--red:#9c2b3a;--paper:#fbf8f1;--line:#ddd3bf}
*{box-sizing:border-box;margin:0;padding:0}
body{width:1920px;height:1080px;background:var(--paper);font-family:'Noto Sans CJK TC','Noto Sans TC','Microsoft JhengHei',sans-serif;color:var(--navy);overflow:hidden}
.frame{position:absolute;inset:0;padding:70px 110px 0;display:flex;flex-direction:column}
.top{position:absolute;top:0;left:0;right:0;height:14px;background:linear-gradient(90deg,var(--navy),var(--blue),var(--gold))}
.brand{position:absolute;top:30px;right:60px;font-size:24px;color:#8a7a5a;letter-spacing:2px}
.page{position:absolute;top:30px;left:60px;font-size:24px;color:#8a7a5a}
.content{flex:1;padding-top:40px;font-size:40px;line-height:1.55}
h3{font-family:'Noto Serif CJK TC','Noto Serif TC','PMingLiU',serif;font-size:62px;margin-bottom:34px;color:var(--navy);border-left:14px solid var(--gold);padding-left:24px}
.cover{height:760px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;padding-left:40px}
.cover .tag{font-size:36px;color:var(--gold);letter-spacing:6px;margin-bottom:20px}
.cover h1{font-family:'Noto Serif CJK TC','Noto Serif TC','PMingLiU',serif;font-size:170px;line-height:1.1;color:var(--navy)}
.cover h2{font-family:'Noto Serif CJK TC','Noto Serif TC','PMingLiU',serif;font-size:80px;color:var(--red);margin:20px 0 40px}
.cover .sub{font-size:36px;color:var(--blue);border-top:3px solid var(--line);padding-top:20px}
.case{background:#fff;border:3px dashed var(--gold);border-radius:16px;padding:22px 30px;margin:10px 0 30px;font-size:38px}
table{border-collapse:collapse;width:100%;font-size:38px;background:#fff}
th,td{border:3px solid var(--line);padding:16px 22px;text-align:center;vertical-align:middle}
th{background:#f3ede0;color:var(--navy)}
table.quad td{font-size:50px;font-weight:700;height:150px;font-family:'Noto Serif CJK TC','Noto Serif TC','PMingLiU',serif}
td.ok{color:#2f6b3a}td.warn{color:#a9832f}td.bad{color:#666}
td.hl,tr.hl td{background:#fff3d6;color:var(--red);font-weight:700}
table.quad td small{font-size:28px;font-weight:400}
.myth{font-family:'Noto Serif CJK TC','Noto Serif TC','PMingLiU',serif;font-size:56px;font-weight:700;margin-bottom:34px;line-height:1.35}
.myth .no,.truth .yes{display:inline-block;font-family:'Noto Sans CJK TC';font-size:34px;color:#fff;background:var(--red);border-radius:10px;padding:6px 18px;margin-right:22px;vertical-align:middle}
.truth{background:#eef3fa;border-left:12px solid var(--blue);padding:20px 28px;margin-bottom:28px;border-radius:8px}
.truth .yes{background:var(--blue)}
ul,ol{padding-left:60px}
li{margin:10px 0}
b{color:var(--red)}
th b{color:var(--red)}
.court{margin-top:30px;background:#fff;border:3px solid var(--blue);border-radius:14px;padding:18px 28px;font-size:36px}
.flow{display:flex;align-items:center;gap:30px;margin-bottom:30px}
.step{background:var(--navy);color:#fff;padding:22px 36px;border-radius:14px;font-size:42px}
.step b{color:#ffd98a}
.arr{font-size:60px;color:var(--gold)}
ol.steps li{margin:18px 0;font-size:42px}
.big{font-family:'Noto Serif CJK TC','Noto Serif TC','PMingLiU',serif;font-size:66px;line-height:1.6;background:#fff;border:4px solid var(--gold);border-radius:20px;padding:40px 50px;margin-bottom:40px}
.src{font-size:28px;color:#6b6250;line-height:1.7}
.subbar{position:absolute;left:0;right:0;bottom:0;min-height:170px;background:rgba(22,35,59,.94);color:#fff;font-size:42px;line-height:1.5;padding:26px 120px;display:flex;align-items:center;justify-content:center;text-align:center}
.prog{position:absolute;left:0;bottom:0;height:8px;background:var(--gold)}
"""

def page(body, sub, idx, n):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="top"></div><div class="page">{'' if idx==0 else f'{idx} / {n-1}'}</div><div class="brand">刑法條文解釋｜Criminal Law Interpretation</div>
<div class="frame"><div class="content">{body}</div></div>
<div class="subbar">{html.escape(sub)}</div><div class="prog" style="width:{(idx+1)/n*100:.1f}%"></div></body></html>"""


def clean_for_speech(sub, say, simplified=False):
    t = say if say else sub
    if simplified and not say:
        from opencc import OpenCC
        t = OpenCC('t2s').convert(t)
    t = t.replace('「', '').replace('」', '').replace('§', '第')
    if simplified:
        for ch in '：；':
            t = t.replace(ch, '，')
    return t


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       check=True, capture_output=True, text=True)
    return float(r.stdout.strip())


class EdgeVoice:
    def __init__(self, voice, rate):
        import edge_tts
        self.edge_tts, self.voice, self.rate = edge_tts, voice, rate

    def synth(self, sub, say, mp3):
        # Edge 台灣語音直接讀繁體；say 欄位是給離線模型的簡體讀音，這裡不用
        text = clean_for_speech(sub, None)
        asyncio.run(self.edge_tts.Communicate(text, self.voice, rate=self.rate).save(mp3))


class MeloVoice:
    def __init__(self, model_dir):
        import sherpa_onnx
        d = model_dir.rstrip('/') + '/'
        cfg = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=d + 'model.onnx', lexicon=d + 'lexicon.txt',
                                                           tokens=d + 'tokens.txt', dict_dir=d + 'dict'),
                num_threads=4),
            rule_fsts=','.join(d + f for f in ['date.fst', 'number.fst', 'phone.fst', 'new_heteronym.fst']))
        self.tts = sherpa_onnx.OfflineTts(cfg)

    def synth(self, sub, say, wav):
        import soundfile as sf
        a = self.tts.generate(clean_for_speech(sub, say, simplified=True), sid=0, speed=1.0)
        sf.write(wav, a.samples, a.sample_rate)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('module', help='tools/video 底下的腳本模組名，例如 mistaken_self_defense')
    ap.add_argument('--voice', default='zh-TW-HsiaoChenNeural')
    ap.add_argument('--rate', default='+0%', help='Edge 語速，例如 +10%% 或 -5%%')
    ap.add_argument('--out', required=True)
    ap.add_argument('--work', default=None, help='暫存資料夾（預設系統暫存）')
    args = ap.parse_args()

    slides = importlib.import_module(args.module).SLIDES
    work = args.work or tempfile.mkdtemp(prefix='video-')
    os.makedirs(work, exist_ok=True)
    engine = MeloVoice(args.voice[5:]) if args.voice.startswith('melo:') else EdgeVoice(args.voice, args.rate)

    from playwright.sync_api import sync_playwright
    segs, n = [], len(slides)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None)
        pg = br.new_page(viewport={'width': 1920, 'height': 1080})
        for i, s in enumerate(slides):
            for j, (sub, say) in enumerate(s['lines']):
                tag = f'{i:02d}_{j:02d}'
                png = os.path.join(work, tag + '.png')
                pg.set_content(page(s['body'], sub, i, n))
                pg.wait_for_timeout(150)
                pg.screenshot(path=png)
                raw = os.path.join(work, tag + ('.wav' if isinstance(engine, MeloVoice) else '.mp3'))
                engine.synth(sub, say, raw)
                pad_end = 0.9 if j == len(s['lines']) - 1 else 0.35
                wav = os.path.join(work, tag + '_pad.wav')
                run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                     f'adelay=250|250,apad=pad_dur={pad_end}', '-ar', '44100', '-ac', '1', wav])
                segs.append((png, wav, probe_duration(wav)))
                print(tag, f'{segs[-1][2]:.1f}s', flush=True)
        br.close()

    parts = []
    for png, wav, dur in segs:
        mp4 = wav.replace('_pad.wav', '.mp4')
        run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', '25', '-i', png, '-i', wav,
             '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p', '-r', '25',
             '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-t', f'{dur:.3f}', mp4])
        parts.append(mp4)
    lst = os.path.join(work, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        for m in parts:
            f.write("file '" + m.replace('\\', '/') + "'\n")
    joined = os.path.join(work, 'joined.mp4')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', joined])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', joined, '-c:v', 'copy', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
         '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-movflags', '+faststart', args.out])
    print('total', round(sum(d for _, _, d in segs), 1), 's ->', args.out)


if __name__ == '__main__':
    main()
