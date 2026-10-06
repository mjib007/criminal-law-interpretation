# 教學解說影片製作規格書

> 給任何 Claude 對話照著做的通用規格。照本文件與 `tools/video/` 的程式，就能做出同一風格的影片。
> 風格：深色背景、逐格繪製動畫、元素跟著旁白一句一句出現（參考 Karpathy 推薦的 3b1b風格解說影片做法）。
> 最後更新：2026-10-06

---

## 〇、來源說明（先讀）

本規格整合兩個來源：

| 項目 | 來源 |
|---|---|
| 1920×1080、edge-tts 台灣華語、字幕燒錄＋另存 .srt、程式逐格繪製（3b1b 風格）、輸出到 `out\`、旁白稿存成 `script.md` | **已確認**：使用者「停止過戶」影片（takeover-timing）交接手冊 |
| fps、配色色碼、字型字級、語速音量、動畫秒數、資料夾細節、程式碼 | **本範本設定**：在雲端實測可跑（範例 `videos/example-stop-transfer/`） |

takeover-timing 的原始程式不在任何 repo 裡，第二列的數值**無法和原片逐一對照**。如果手邊有原片程式，請把不同的數值改進「二、畫面規格」與 `tools/video/vidkit.py` 開頭的常數，兩處保持一致。

---

## 一、工具與安裝

| 工具 | 用途 | 安裝 |
|---|---|---|
| Python 3.10以上 | 主程式 | python.org 或系統內建 |
| Pillow | 逐格繪製畫面 | `pip install pillow` |
| edge-tts | 微軟台灣華語語音（免費，需連網） | `pip install edge-tts` |
| ffmpeg（含 ffprobe） | 語音轉檔、合成 mp4、音量正規化 | Windows：`winget install ffmpeg`；Mac：`brew install ffmpeg`；Ubuntu：`apt install ffmpeg` |
| 中文字型 | 畫面文字 | Windows 用內建微軟正黑體；Linux：`apt install fonts-noto-cjk` |

一次安裝：

```bash
pip install pillow edge-tts
```

**網路受限時的離線備用**（雲端環境擋住 `speech.platform.bing.com` 時才需要，口音是大陸腔）：

```bash
pip install sherpa-onnx soundfile opencc-python-reimplemented
curl -L -o melo.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2
tar xjf melo.tar.bz2
```

**Claude 雲端環境注意**：預設網路會擋 edge-tts。要用台灣語音，請在環境設定 Network access 改 Custom，Allowed domains 加入 `speech.platform.bing.com`；或改在自己電腦開本機對話執行。

---

## 二、畫面規格

| 項目 | 數值 |
|---|---|
| 解析度 | 1920×1080 |
| 影格率 | 30fps |
| 編碼 | H.264（libx264，CRF 20，yuv420p），音訊 AAC 160kbps／44.1kHz |
| 安全邊界 | 左右各120px；底部190px 留給字幕帶 |
| 背景 | 純色 `#111418`，疊一層120px間距淡格線 `#20252C` |

**配色**（顏色固定代表意義，整支影片不混用）：

| 代號 | 色碼 | 用途 |
|---|---|---|
| `fg` | `#ECEFF4` | 主文字 |
| `muted` | `#8A93A3` | 次要文字、標籤、右上角品牌字 |
| `blue` | `#58C4DD` | 主色：概念框、時間軸 |
| `yellow` | `#F4D35E` | 強調：關鍵日期、數字、結論 |
| `green` | `#83C167` | 合法、可以、正確 |
| `red` | `#FC6255` | 違法、不可以、錯誤、禁止期間 |
| 字幕底板 | 黑色、不透明度170／255 | 字幕帶 |

**字型與字級**：

| 用途 | 字型 | 字級（px） |
|---|---|---|
| 場景標題 | Noto Sans CJK TC Bold（Windows：微軟正黑體粗體） | 76 |
| 小標題、大框文字 | Noto Sans CJK TC | 56 |
| 內文 | Noto Sans CJK TC | 46 |
| 圖表標籤、時間軸刻度 | Noto Sans CJK TC | 36 |
| 右上角品牌字 | Noto Sans CJK TC | 30 |
| 字幕 | Noto Sans CJK TC | 44 |
| 大數字（計數動畫） | Noto Sans CJK TC Bold | 96至120 |

---

## 三、語音

| 參數 | 預設值 | 說明 |
|---|---|---|
| 語音 | `zh-TW-HsiaoChenNeural` | 曉臻（女），咬字清楚 |
| 可替換 | `zh-TW-YunJheNeural`（雲哲，男）、`zh-TW-HsiaoYuNeural`（曉雨，女） | 用 `--voice` 指定 |
| 語速 | `+0%` | 用 `--rate +5%` 加快、`--rate -5%` 放慢 |
| 音量 | `+0%` | 用 `--volume`；最終再以 ffmpeg loudnorm 統一到 −16 LUFS |
| 合成單位 | 一句一個檔 | 方便依每句長度排時間軸 |

**讀音修正**：旁白稿某句念錯時，在句尾加〔讀：…〕，字幕照原文、語音念括號內文字。例：

```
- 依公司法第165條規定。〔讀：依公司法第一百六十五條規定。〕
```

語音念之前會自動拿掉「」『』，並把 § 換成「第」。

---

## 四、字幕

| 項目 | 規格 |
|---|---|
| 燒錄方式 | 程式逐格把字幕畫進畫面（不靠 ffmpeg subtitles 濾鏡，不用另外裝 libass） |
| 位置 | 畫面最底部，高190px的半透明黑色字幕帶，文字水平置中 |
| 字級 | 44px，行高62px，最多兩行 |
| 斷行 | 超過畫面寬度扣左右邊界（1680px）就換行；逗號、句號等標點不放行首 |
| 顯示時間 | 該句語音開始到結束後0.2秒 |
| .srt | 與燒錄字幕同一份時間軸，輸出到 `out\<影片名>.srt`，UTF-8編碼 |
| 只要 .srt、不燒錄 | 加 `--no-burn` |

---

## 五、動畫風格

**原則**（3b1b 式）：

1. 一個畫面只講一件事；畫面上的字越少越好，細節交給旁白。
2. 元素跟著旁白出現：第 k 句開始時，與該句相關的元素才進場。
3. 東西是「畫出來」的：線條由起點畫到終點，時間軸由左往右長，區間色塊慢慢展開。
4. 顏色固定代表意義（見配色表），觀眾不用重新學。
5. 已出現的元素留在畫面上累積，到下一個場景才清空。

**動畫元素與預設秒數**（`tools/video/vidkit.py`）：

| 元素 | 進場方式 | 預設長度 |
|---|---|---|
| `Title`／`Text` | 淡入＋由下往上滑24px | 0.6秒（淡入0.5秒） |
| `Box` | 從85%放大到100%＋淡入 | 0.6秒 |
| `Line`／`Arrow` | 由起點畫到終點；箭頭在畫完時出現 | 0.6秒 |
| `Timeline` | 軸線由左往右畫出，刻度隨軸線經過時出現 | 1.2秒 |
| `Span` | 區間色塊由右往左展開（適合「往前倒數」） | 建議2.0秒 |
| `Dot` | 彈一下出現 | 0.6秒 |
| `Counter` | 數字由 a 跑到 b | 建議1.2秒 |
| 退場（設 `until`） | 淡出 | 0.4秒 |

緩動一律用 ease-out cubic（快進慢停）。

**時間軸怎麼畫**：

```python
tl = sc.add(Timeline(at=c[0], ticks=[(0.2, '', '9月9日', 'r'), (0.22, '', '9月10日', 'l'), (0.87, '', '10月9日')]))
sc.add(Span(xa=tl.xpos(0.22), xb=tl.xpos(0.87), y=tl.y - 4, label='停止過戶30日', color='red', at=c[1], dur=2.0))
```

- 刻度位置用0到1的相對值，先把日期換成天數再除以總天數。
- 兩個刻度太近時，一個標籤用 `'r'`（往左擺）、一個用 `'l'`（往右擺），避免重疊。
- 重要的日期點用 `Dot`（黃色），期間用 `Span`，結論用 `Arrow` 指過去。

**每段畫面停留多久**：不手動設定，全部由語音長度決定：

| 時段 | 秒數 |
|---|---|
| 場景開頭留白 | 0.4 |
| 每句語音 | 實際語音長度 |
| 句與句之間 | 0.3 |
| 場景結尾留白 | 0.9 |

場景長度＝0.4＋各句長度總和＋0.3×（句數−1）＋0.9。

---

## 六、製作流程

1. **寫旁白稿** `videos/<影片名>/script.md`：一個 `##` 是一個場景，一個 `-` 是一句旁白（也是一句字幕）。每句控制在40字以內，最多兩行字幕。
2. **寫動畫** `videos/<影片名>/scenes.py`：每個場景一個函式，用 `c[k]`（第 k 句開始秒數）決定元素何時進場。沒寫函式的場景會自動顯示「標題＋底線」。
3. **執行**：
   ```bash
   python tools/video/make.py videos/<影片名>
   ```
   程式依序：逐句合成語音 → 量每句長度排出時間軸 → 執行 scenes.py 放元素 → 混音 → 輸出 .srt → 逐格繪製並交給 ffmpeg 合成 mp4。
4. **檢查**：抽幾格截圖確認排版（`ffmpeg -ss 秒數 -i 影片 -frames:v 1 檢查.png`），完整聽一次確認讀音；念錯的句子加〔讀：〕重跑。
5. **交付**：把 `script.md`、`scenes.py`、`out\` 裡的 mp4與srt 交給使用者；需要的話推送到 GitHub。

製作時間參考：40秒範例在雲端約1分鐘；5分鐘影片約8至10分鐘。

---

## 七、資料夾結構與檔名

```
repo/
├── VIDEO-SPEC.md                 本規格書
├── tools/video/
│   ├── vidkit.py                 引擎（畫面規格、動畫元素、語音、字幕、合成）
│   └── make.py                   命令列入口
└── videos/
    └── <影片名>/                 英文小寫、用連字號，例如 takeover-timing、mistaken-self-defense
        ├── script.md             旁白稿（唯一的文字來源）
        ├── scenes.py             動畫
        └── out/                  產出（不進版控）
            ├── <影片名>.mp4
            ├── <影片名>.srt
            └── audio/            每句語音 00_00.wav（場景序_句序）與混音 _mix.wav
```

- 資料夾與檔名一律英文，避免中文路徑在網址出現亂碼。
- 場景代號用 `S1`、`S2`……，與 `scenes.py` 的 `SCENES = {'S1': s1, ...}` 對應。

---

## 八、程式碼範本

完整程式在 repo：

- 引擎：[`tools/video/vidkit.py`](tools/video/vidkit.py)
- 命令列：[`tools/video/make.py`](tools/video/make.py)
- 可直接跑的範例：[`videos/example-stop-transfer/`](videos/example-stop-transfer/)（停止過戶期間計算，3個場景、約40秒）

### （一）script.md 範本

```markdown
# 停止過戶怎麼算

## S1 停止過戶是什麼
- 公司開股東會之前，會有一段期間停止辦理股票過戶。
- 這段期間買進的股票照樣可以交易，但不能在這次股東會投票。

## S3 實例：往前倒數
- 以股東臨時會訂在10月9日為例。
- 從10月9日往前算30日，停止過戶從9月10日開始。
- 想在這次臨時會投票，股份最晚要在9月9日完成過戶。
```

### （二）scenes.py 範本

```python
# -*- coding: utf-8 -*-
from vidkit import *


def s1(sc):
    c = sc.cues                                   # c[k]：第 k 句旁白開始的秒數
    sc.add(Title(text='停止過戶是什麼？', xy=(MARGIN, 110), at=0))
    sc.add(Box(rect=(MARGIN, 300, W // 2 - 40, 640), color='blue', at=c[0]),
           Text(text='股東會之前\n停止辦理過戶', xy=(W // 4 + 30, 470), anchor='mm', size=SIZE['h2'], at=c[0] + 0.2))
    sc.add(Box(rect=(W // 2 + 40, 300, W - MARGIN, 470), color='green', fill=True, at=c[1]),
           Text(text='○ 可以買賣', xy=(W * 3 // 4 - 30, 385), anchor='mm', size=SIZE['h2'], at=c[1] + 0.2))
    sc.add(Box(rect=(W // 2 + 40, 490, W - MARGIN, 640), color='red', fill=True, at=c[1] + 1.2),
           Text(text='× 這次不能投票', xy=(W * 3 // 4 - 30, 565), anchor='mm', size=SIZE['h2'], at=c[1] + 1.4))


def s3(sc):
    c = sc.cues
    sc.add(Title(text='實例：從開會日往前倒數', xy=(MARGIN, 110), at=0))
    span = 45                                     # 8月31日到10月15日
    def u(m, d):
        return (d if m == 9 else 30 + d) / span
    tl = sc.add(Timeline(at=c[0], ticks=[(u(9, 9), '', '9月9日', 'r'), (u(9, 10), '', '9月10日', 'l'),
                                          (u(10, 9), '', '10月9日')]))
    x = tl.xpos
    sc.add(Dot(xy=(x(u(10, 9)), tl.y), color='yellow', at=c[0] + 1.0))
    sc.add(Span(xa=x(u(9, 10)), xb=x(u(10, 9)), y=tl.y - 4, label='停止過戶30日', color='red', at=c[1], dur=2.0))
    sc.add(Arrow(p0=(x(u(9, 9)) - 260, tl.y + 220), p1=(x(u(9, 9)) - 60, tl.y + 95), color='green', at=c[2]))


SCENES = {'S1': s1, 'S3': s3}
```

### （三）執行指令

```bash
# 台灣語音（需連得到 speech.platform.bing.com）
python tools/video/make.py videos/example-stop-transfer --voice zh-TW-HsiaoChenNeural --rate +0%

# 換男聲、稍快
python tools/video/make.py videos/example-stop-transfer --voice zh-TW-YunJheNeural --rate +5%

# 離線備用（大陸口音）
python tools/video/make.py videos/example-stop-transfer --melo ./vits-melo-tts-zh_en
```

### （四）新增動畫元素

在 `vidkit.py` 繼承 `El`，實作 `draw(self, d, p)`；`d` 是 Pillow 的 ImageDraw，`p` 是0到1的進場進度（已套緩動）。淡入淡出由引擎處理，不用自己寫。

---

## 九、文字規範

適用旁白稿、字幕、畫面文字與本類文件：

1. 繁體中文。
2. 全形標點：，。、；：？！「」（）。
3. 不使用破折號（——、—）；需要補充說明時改用逗號、冒號或括號。
4. 中文與數字之間不加空格：寫「30日」「第165條」「9月10日」，不寫「30 日」。
5. 條號用阿拉伯數字（例：§165、第23條）；語音念不好時用〔讀：〕修正，不改字幕。

---

## 十、交接給下一個 Claude 對話時

請對方依序：

1. 讀本檔（`VIDEO-SPEC.md`）。
2. 跑一次範例確認環境可用：`python tools/video/make.py videos/example-stop-transfer`。
3. 在 `videos/<新影片名>/` 寫 `script.md`，先給使用者確認旁白，再寫 `scenes.py` 並產生影片。
