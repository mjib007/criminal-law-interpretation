---
name: tw-judgment-search
description: 到司法院裁判書系統（https://judgment.judicial.gov.tw/FJUD/default.aspx）查台灣法院判決，並核對全文、歷審與上訴範圍；也查法令判解系統的判例效力、全國法規資料庫的條文沿革。使用者說「查判決」「找判決」「有沒有判決」「實務見解」「最高法院怎麼說」「這個字號對不對」「有沒有上訴」「歷審」「判例還能用嗎」「條文什麼時候修的」，或製作法律教材、影片、講義需要引用判決時，務必使用。只分析使用者已提供的判決全文時，改用 legal-judgment-analysis。
---

# 台灣判決搜尋與核對

用內建瀏覽器操作司法院的公開網站，像人工查詢一樣找判決，再逐件打開核對。**所有字號都必須是實際打開過的，不能憑記憶寫。**

為什麼要這麼嚴格：法律教材給學生看，字號、見解或確定情形錯一個，學生就會照抄。這個流程裡的每一步，都是實際出錯過才加上的（見最後一節）。

## 0. 先決條件

- 用內建瀏覽器（`mcp__Claude_Browser__*`）。司法院網站用 Python 直接下載常失敗（憑證錯誤或回傳防爬蟲頁），一律在瀏覽器裡操作。
- 用 `fetch()` 抓同網域頁面前，先 `navigate` 到該網域任一頁（跨網域會失敗）。
- `javascript_tool` 單次45秒逾時：一次 `fetch` 最多約6件判決，多的分批。

## 1. 關鍵字找候選判決

1. `navigate` 到 `https://judgment.judicial.gov.tw/FJUD/default.aspx`。
2. 填關鍵字並送出（用 `setTimeout` 送出，直接 click 會讓腳本被換頁中斷）：
   ```javascript
   document.querySelector('#txtKW').value = '竊盜&不能未遂&口袋';
   setTimeout(() => document.querySelector('#btnSimpleQry').click(), 50); 'ok'
   ```
3. 下一次呼叫等1.5到2.5秒再讀結果。左側依法院分組，**先看最高法院**，沒有再看高等法院、地方法院。取得某法院的清單：
   ```javascript
   await new Promise(r => setTimeout(r, 2000));
   const a = [...document.querySelectorAll('a')].find(a => /^最高法院\d+/.test(a.textContent.trim()));
   const d = new DOMParser().parseFromString(await (await fetch(a.href)).text(), 'text/html');
   [...d.querySelectorAll('a')].filter(x => /data\.aspx/.test(x.getAttribute('href') || ''))
     .map(x => x.textContent.trim().replace(/\s+/g, '') + '|' + x.getAttribute('href')).slice(0, 20)
   ```

### 檢索語法（半形符號，見網站「檢索字詞說明」）
| 符號 | 意思 | 範例 |
|---|---|---|
| `&` | 且 | `中止犯&己意` |
| `+` | 或 | `中止犯+中止未遂` |
| `-` | 不含 | `不能未遂-毒品` |
| `( )` | 組合 | `(中止犯+中止未遂)&己意` |

### 選關鍵字的技巧
- **用法院的固定說法，比口語準**：例如「通常障礙事由」「客觀上通常一般人所認識」「容任」「確信其不發生」。找到一則判決後，從原文挑一段獨特詞句再搜，就能找到用同一套標準的其他判決。
- 口語問題先拆成「罪名＋爭點＋事實特徵」，例如「偷金融卡查餘額0」→ `不能未遂&金融卡&餘額`。
- 查不到最高法院時，明講「最高法院沒有找到」，改用下級審並標明法院層級。**不要說「沒有這種判決」**，只能說「用某某關鍵字沒有找到」。

### 指定字號查詢
- 簡易查詢框直接輸入字號也可以，例如「最高法院114台上1976」。結果左側若同時出現其他法院（例如「臺中高分院1」），代表有上、下級審。
- 精確查詢：`https://judgment.judicial.gov.tw/FJUD/Default_AD.aspx`：
  ```javascript
  const c = document.querySelector('#jud_court'); [...c.options].forEach(o => o.selected = (o.value === 'TPS'));
  document.querySelectorAll('input[name=jud_sys]').forEach(x => x.checked = (x.value === 'M')); // M＝刑事
  document.querySelector('#jud_year').value = '114';
  document.querySelector('#jud_case').value = '台上';
  document.querySelector('#jud_no').value = '1976';
  setTimeout(() => document.querySelector('#btnQry').click(), 50); 'ok'
  ```
  下一次呼叫讀結果 iframe 裡含 `data.aspx` 的連結。系統查無此號時，先檢查法院代碼、刑事／民事、年度、字別、號數有沒有填錯，重查一次；仍查無，才判定字號記錯，不要硬套。

## 2. 快速篩選（只用來挑案例）

對候選清單分批 `fetch` 全文，只擷取關鍵字前後段落比對：
```javascript
const out = [];
for (const [name, url] of 清單.slice(0, 6)) {
  const t = new DOMParser().parseFromString(await (await fetch(url)).text(), 'text/html').body.textContent.replace(/\s+/g, '');
  const i = t.indexOf('不能未遂');
  out.push(name + ' ⇒ ' + t.slice(Math.max(0, i - 260), i + 260));
}
out
```
**這一步只能挑案例，不能判斷歷審**（原因見第3步）。

## 3. 逐件打開核對（挑中的每一件都要做）

1. `navigate` 到判決全文頁，**等2到3秒**再讀：
   ```javascript
   await new Promise(r => setTimeout(r, 3000));
   const raw = document.body.innerText, t = raw.replace(/\s+/g, '');
   ({ 案由: t.slice(t.indexOf('案由'), t.indexOf('案由') + 20),
      主文: t.slice(t.indexOf('主文'), t.indexOf('主文') + 60),
      歷審: raw.slice(raw.indexOf('歷審裁判'), raw.indexOf('歷審裁判') + 500) })
   ```
2. **看右側「歷審裁判 N」**：這一欄是頁面載入後才由網頁程式補上的，用 `fetch` 抓原始 HTML 看不到，會誤以為「沒有上訴」。也可開「列印歷審清單」`/FJUD/printHistory.aspx?id=...`。
3. N 大於1：逐一打開各審。
4. **看上訴範圍**：一審常有數罪或有罪、無罪兩部分。讀二審「本院審理範圍」與主文，確認引用的部分是「未據上訴而告確定」、被維持，還是被撤銷改判。**被撤銷的見解不能當實務見解引用。**
5. **看清楚是誰說的**：
   - 起訴書、上訴書常列為「附件」，或在理由中引述當事人主張；這些不是法院見解。
   - 最高法院駁回上訴時，常引述「原判決認定……」，這是**原審見解**，最高法院只是維持。寫成「最高法院維持原審見解」。
   - 最高法院自己說明法律標準的段落（常以「按」「所謂」開頭），才寫「最高法院認為」。
   - 「從程序上駁回」（上訴不合法律上之程式，刑事訴訟法第395條前段）≠ 最高法院另作實體有罪判決。
6. 下級審寫「最高法院某號判決意旨參照」，也要回原判決核對；曾有多件高院判決把一段話標錯字號。

## 4. 判例效力（司法院法令判解系統）

判例制度108年7月4日廢止。查現在的狀態：
```javascript
// 先 navigate 到 https://legal.judicial.gov.tw/FINT/default.aspx
const u = '/FINT/data.aspx?id=' + encodeURIComponent('B,74,台上,4219,001') + '&ty=J';  // 刑事判例
const t = new DOMParser().parseFromString(await (await fetch(u)).text(), 'text/html').body.innerText.replace(/\s+/g, '');
t.slice(t.indexOf('編註'), t.indexOf('編註') + 200)
```
| 編註寫的 | 寫法 |
|---|---|
| 無裁判全文，依法院組織法第57條之1第1項停止適用 | 「原為判例，已停止適用」，不能當實務見解引用 |
| 依第57條之1第2項，效力與未經選編為判例之最高法院裁判相同 | 「原為判例」，可引用，效力同一般最高法院判決 |
| 依某次刑事庭會議決議不再援用 | 註明不再援用 |

## 5. 條文與沿革（全國法規資料庫）

- 現行條文：`https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=C0000001&flno=條號`（刑法 pcode `C0000001`；條號如 `315-1`）。
- 歷史條文（帶日期）：`/LawClass/LawOldVer.aspx?pcode=C0000001&lnndate=YYYYMMDD&lser=001`。抓幾個日期的版本比對，就能找出某段文字是哪次修正刪改的。
- 修正日期清單：`/LawClass/LawHistory.aspx?pcode=C0000001`。
- 網址參數不能有半形分號等字元，否則回「系統訊息」錯誤頁。

## 6. 網址與代碼

- 判決全文：`https://judgment.judicial.gov.tw/FJUD/data.aspx?ty=JD&id=<法院代碼>,<年度>,<字別>,<號>,<日期YYYYMMDD>,1`（逗號與中文要 URL 編碼）。
- 已確認的法院代碼（刑事）：最高法院 `TPSM`、臺灣高等法院 `TPHM`、臺中分院 `TCHM`、臺中地院 `TCDM`。其他法院從查詢結果的網址讀，不要猜。

## 7. 回報格式

用表格回報，每件都要有：

| 判決字號 | 法院層級 | 裁判日期 | 案由 | 見解原文摘錄（標明是法院、原審或當事人） | 歷審與確定情形 | 網址 |

並分三類說明來源：已打開全文核對的、只看過摘錄的、自己推論的（例如「依此標準推論」）。

## 8. 曾經出過的錯（每條都是規則的由來）

| 日期 | 錯誤 | 現在的規則 |
|---|---|---|
| 2026-10-08 | 把屏東地院判決「附件：起訴書」裡檢察官的話當成法院見解 | 確認引文位置，看主文 |
| 2026-10-13 | 講義說最高法院101台上3380「重申」闖空門見解，原文其實是原審理由 | 分辨原審與最高法院 |
| 2026-10-13 | 當時查「97台上351」得到查無此號，誤以為字號不存在；2026-10-15 用精確查詢（TPS、刑事、97、台上、351）查得到（97.01.24，不能未遂標準公式），當時應是輸入錯誤 | 不用記憶中的字號，以查得到、讀過全文為準；查無此號時，先用精確查詢重新確認法院、年度、字別、號數，再下結論 |
| 2026-10-14 | 用 fetch 抓臺中地院107易3258，看不到歷審，誤報「沒有上訴」；實際有二、三審 | 在瀏覽器開頁面、等載入，看右側歷審；有上訴看審理範圍 |
| 2026-10-14 | 把114台上2080寫成「最高法院維持原審認定」，實際是最高法院自行說明容任主義後程序駁回 | 讀到理由最後一段與主文依據條文 |