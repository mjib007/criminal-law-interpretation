# -*- coding: utf-8 -*-
"""產生影片。用法（在 repo 根目錄）：

  python tools/video/make.py videos/<影片資料夾>
  python tools/video/make.py videos/<影片資料夾> --voice zh-TW-YunJheNeural --rate +5%
  python tools/video/make.py videos/<影片資料夾> --melo <離線模型資料夾>   # 網路擋住 edge-tts 時

輸出：videos/<影片資料夾>/out/<資料夾名>.mp4、.srt、audio/
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vidkit

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('--voice', default='zh-TW-HsiaoChenNeural')
ap.add_argument('--rate', default='+0%')
ap.add_argument('--volume', default='+0%')
ap.add_argument('--melo', default=None, help='sherpa-onnx vits-melo-tts-zh_en 模型資料夾')
ap.add_argument('--brand', default='')
ap.add_argument('--no-burn', action='store_true', help='不燒錄字幕，只輸出 .srt')
a = ap.parse_args()

tts = {'engine': 'melo', 'model': a.melo} if a.melo else \
      {'engine': 'edge', 'voice': a.voice, 'rate': a.rate, 'volume': a.volume}
vidkit.build(a.project, tts, brand=a.brand, burn_subs=not a.no_burn)
