# 交接手冊：誤想防衛說明影片（換台灣配音）

> 給接手的 Claude 本機對話（或使用者本人）閱讀。讀完照「接手步驟」做即可。
> 最後更新：2026-10-06｜分支：`ccr-09ef2072-trjhrf`
> 影片製作通用規格：[`VIDEO-SPEC.md`](VIDEO-SPEC.md)

---

## 一、目前狀態

| 項目 | 狀態 |
|---|---|
| 影片 `videos/mistaken-self-defense.mp4` | ✅ 已完成（約5分30秒，1080p），但配音是**大陸腔**離線語音 |
| 旁白稿 `videos/mistaken-self-defense-script.md` | ✅ 完成 |
| 影片產生程式 `tools/video/` | ✅ 已放進 repo，雲端測試可跑 |
| 換成台灣配音 | ⏳ **待辦**：雲端環境擋住微軟語音（`speech.platform.bing.com` 回403），改由使用者另開的對話處理，本對話不再追蹤 |
| 使用者選定的聲音 | ❓ 尚未決定（A 曉臻／B 雲哲／C 曉雨） |

試聽頁（用 Microsoft Edge 開）：https://claude.ai/artifact/Nh7HZGqtEiENF7bP2DXQ1N

## 二、影片內容摘要

主題：誤想防衛（容許構成要件錯誤）的七個常見誤解。

1. 誤想防衛也算正當防衛 → 錯，客觀無現在不法侵害，不阻卻違法
2. 等於防衛過當、可依§23但書減免 → 錯，過當是真有侵害
3. 跟偶然防衛差不多 → 方向相反
4. 就是禁止錯誤、直接用§16 → 混淆「容許構成要件錯誤」與「容許錯誤」
5. 一定無罪 → 排除故意後仍檢討過失犯（§12Ⅱ）
6. 教唆、幫助者也不罰 → 限制法律效果之罪責理論下構成要件故意仍在
7. 誤想防衛過當直接當誤想防衛 → 雙重偏差，原則上檢討故意犯，類推§23但書有爭議

實務：最高法院29年上字第509號原判例（論以過失）。
未採用：27年上字第2879號（搜尋摘要稱採嚴格罪責理論，但未能查證原文）。

## 三、接手步驟（在使用者自己的電腦）

### 1. 取得程式

```bash
git clone https://github.com/mjib007/criminal-law-interpretation.git
cd criminal-law-interpretation
git checkout ccr-09ef2072-trjhrf
```

### 2. 安裝工具（只需一次）

```bash
pip install edge-tts playwright soundfile numpy
playwright install chromium
```

另需 **ffmpeg**（Windows：`winget install ffmpeg`；Mac：`brew install ffmpeg`）。
字型：Windows 會自動用「微軟正黑體」；若有安裝 Noto Sans/Serif TC 效果更好。

### 3. 產生影片（把聲音換成使用者選的）

```bash
python tools/video/build.py mistaken_self_defense --voice zh-TW-YunJheNeural --out videos/mistaken-self-defense.mp4
```

| 代號 | `--voice` 參數 | 特色 |
|---|---|---|
| A | `zh-TW-HsiaoChenNeural` | 曉臻（女），新聞主播感 |
| B | `zh-TW-YunJheNeural` | 雲哲（男），沉穩適合講課 |
| C | `zh-TW-HsiaoYuNeural` | 曉雨（女），較年輕口語 |

語速：加 `--rate +10%`（快一點）或 `--rate -5%`（慢一點）。

### 4. 檢查後推送

1. 播放新影片，確認發音與停頓（特別是「過當」「行為」「阻卻」及條號）。
2. 有讀錯的句子，到 `tools/video/mistaken_self_defense.py` 改該句字幕文字後重跑。
3. 推送：

```bash
git add videos/mistaken-self-defense.mp4
git commit -m "誤想防衛影片改用台灣配音"
git push origin ccr-09ef2072-trjhrf
```

## 四、程式說明

| 檔案 | 用途 |
|---|---|
| `tools/video/mistaken_self_defense.py` | 影片內容：每張投影片的畫面 HTML ＋ 旁白句子 |
| `tools/video/build.py` | 產生器：截圖（Playwright）→ 語音（Edge 或離線）→ ffmpeg 合成並正規化音量 |

- 旁白每句是 `(字幕, 讀音)`；「讀音」欄只給離線大陸模型用（簡體、中文數字），Edge 台灣語音直接讀字幕。
- 要做新主題影片：複製 `mistaken_self_defense.py` 改內容，執行時把模組名換掉即可。
- 離線備用：`--voice melo:<sherpa-onnx vits-melo-tts-zh_en 模型資料夾>`（大陸口音，僅網路受限時用）。

## 五、通用影片製作規格（已整合「停止過戶」影片的做法）

完整規格見 **[`VIDEO-SPEC.md`](VIDEO-SPEC.md)**，之後做任何教學影片都照它。重點：

| 項目 | 規格 |
|---|---|
| 畫面 | 1920×1080、30fps、深色背景＋淡格線、程式逐格繪製（3b1b風格） |
| 語音 | edge-tts 台灣華語，預設 `zh-TW-HsiaoChenNeural`，語速、音量 `+0%`，一句一檔 |
| 字幕 | 燒錄在畫面底部字幕帶（44px），另輸出 `out\<影片名>.srt` |
| 時間 | 每段畫面長度由語音長度決定，不手動設定 |
| 檔案 | `videos/<影片名>/script.md`（旁白稿）、`scenes.py`（動畫）、`out\`（產出） |
| 程式 | `tools/video/vidkit.py`（引擎）、`tools/video/make.py`（執行） |
| 範例 | `videos/example-stop-transfer/`，雲端實測可跑 |

兩套程式的分工：

| 程式 | 風格 | 用在 |
|---|---|---|
| `tools/video/make.py`＋`vidkit.py` | 3b1b式逐格動畫（**新標準**） | 之後所有新影片 |
| `tools/video/build.py` | 投影片截圖＋旁白（舊做法） | 目前的誤想防衛影片；換台灣配音時沿用即可 |

注意：takeover-timing 的原始程式沒有放在任何 repo，規格書中的色碼、字級、動畫秒數是本範本的設定，未能與原片逐一對照（規格書第〇節有標示）。手邊若有原片程式，請把不同的數值改進規格書與 `vidkit.py`。

## 六、未決事項

- [ ] 是否把影片加入 `index.html` 總覽頁、或另做成講義 HTML（尚未決定）
- [ ] 是否建立 PR（使用者尚未要求）
- [ ] 是否把誤想防衛影片改用新標準（3b1b式動畫）重做
- [ ] 取得 takeover-timing 原始程式後，校正 `VIDEO-SPEC.md` 第二至五節數值
