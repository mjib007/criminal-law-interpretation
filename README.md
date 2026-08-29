# 📖 蒸餾skill／自動共享／協力共筆｜Criminal Law Interpretation

![Profile views](https://komarev.com/ghpvc/?username=mjib007&label=Profile%20views&color=4c8eda&style=flat)
[![Stars](https://img.shields.io/github/stars/mjib007/criminal-law-interpretation?style=flat&color=yellow)](https://github.com/mjib007/criminal-law-interpretation/stargazers)
[![Forks](https://img.shields.io/github/forks/mjib007/criminal-law-interpretation?style=flat&color=blue)](https://github.com/mjib007/criminal-law-interpretation/network/members)
![Concept](https://img.shields.io/badge/核心概念-蒸餾skill%20%C2%B7%20自動共享%20%C2%B7%20協力共筆-1a3a5c)
![AI](https://img.shields.io/badge/AI-Claude%20(Anthropic)-blueviolet)
![Platform](https://img.shields.io/badge/Platform-claude.ai-orange)
![Language](https://img.shields.io/badge/Language-繁體中文-red)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)](LICENSE.md)
![Status](https://img.shields.io/badge/status-active-success)
[![總覽頁](https://img.shields.io/badge/總覽頁-GitHub%20Pages-1a3a5c)](https://mjib007.github.io/criminal-law-interpretation/)

> 貼上刑法條文，AI 主動討論、確認範圍，依三階段犯罪判斷產出結構化 HTML 教學講義，用理解取代死背。

---

## 這是什麼？

**Criminal Law Interpretation** 是一套專為法律系學生、教師設計的 AI 輔助條文解釋工具，架構比照姊妹專案 [civil-law-interpretation](https://github.com/mjib007/civil-law-interpretation)，但要件分析改用刑法特有的**三階段犯罪判斷**：構成要件該當性、違法性、有責性。

貼上一條或多條刑法條文，AI 會先主動建議關聯條文（如刑法總則中故意過失、正犯共犯、未遂等共用條文）、詢問是否有補充資料（學說、實務見解），討論到一定程度後，才產出一份包含條文結構、三階段判斷、教學案例、速查卡的完整講義。

---

## 📂 總覽頁：所有講義的目錄地圖

每產出一份講義，Skill 會自動把它加進本倉庫的 **`index.html`** 總覽頁，並同步推送到 GitHub Pages：

👉 **[https://mjib007.github.io/criminal-law-interpretation/](https://mjib007.github.io/criminal-law-interpretation/)**

總覽頁依刑法**總則編（§1–99）＋分則編（§100–363）**完整章節架構繪製教學進度地圖：

- 🔍 **搜尋 / 篩選**：依條號或罪名關鍵字搜尋，或用分類下拉選單篩選
- 🗺️ **分類覆蓋地圖**：把總則十二章、分則三十六章全部列出，每章旁標示已有幾篇講義
- 🃏 **講義卡片**：顯示條號、罪名、完成日期，點擊直接開啟對應 HTML 講義

---

## 適合誰使用？

| 對象 | 用途 |
|------|------|
| 📚 法律系學生 | 條文研讀、建立三階段判斷架構、速查卡複習 |
| 👨‍🏫 法律系教師 | 課堂講義製作、依授課對象調整深度 |
| ⚖️ 國考／司律考生 | 拆解常考罪名的構成要件與關鍵字，減少死背負擔 |
| 🔬 法學教育研究者 | 探索 AI 輔助條文教學的可能性 |

---

## 主要功能

| 步驟 | 內容 |
|------|------|
| 1️⃣ 收集條文 | 原文照錄，並主動分析、建議關聯條文（必要／建議／可跳過） |
| 2️⃣ 確認講義範圍 | 條文結構解析、三階段犯罪判斷（必選）、學說見解、實務見解、教學案例、申論練習題、速查卡，逐項確認 |
| 3️⃣ 產生 HTML 講義 | 固定九章節：封面、條文原文、條文結構、三階段判斷、學說見解、實務見解、教學案例、申論練習題、速查卡 |
| 3.5️⃣ 實務見解搜尋 | 涉及判決、大法官解釋時，主動搜尋並列表供使用者確認，附原始來源與查詢路徑 |
| 4️⃣ 審閱修正 | 局部修改用 str_replace，大幅重構才整份重新輸出 |
| 5️⃣ 推送與總覽頁同步 | 確認完成後可推送至 GitHub，並自動將講義加入 `index.html` 總覽頁的分類地圖 |

> 學說見解、實務見解為**必含章節**，不可省略，若使用者尚未提供或搜尋查無結果，會以虛線佔位樣式呈現（含「待補充」徽章），保留章節位置。

---

## 快速開始

### 第一步：準備工具
你需要一個 **Claude 帳號**（免費版即可使用）：
👉 [https://claude.ai](https://claude.ai)

### 第二步：安裝 Skill
下載本倉庫的 [`SKILL.md`](./SKILL.md)，依你使用之 Claude 介面的 Skill 安裝方式匯入
（例如放入 `/mnt/skills/user/criminal-law-interpretation/SKILL.md`）。

### 第三步：開始使用
1. 在 Claude 開啟一個新對話
2. 貼上你要解釋的刑法條文全文，或說「幫我解釋刑法第○條」
3. Skill 會先主動建議關聯條文、詢問補充資料，討論到位後才產出講義

---

## 使用限制與提醒

- AI 分析結果僅供研讀與教學參考，**不構成正式法律意見**
- 法條、判決字號請以官方資料庫（全國法規資料庫、司法院法學資料檢索系統）為準
- 「判例」制度已於民國108年法院組織法修正後不再選編，舊判例現僅作為裁判先例參考，本工具引用時會特別標註
- 涉及非官方網站節錄之實務見解，會標明原始來源網址，使用前請自行至官方資料庫核實

---

## 檔案結構

```
criminal-law-interpretation/
│
├── README.md        # 你現在看的這份說明文件
├── SKILL.md          # 完整 Skill 內容，依 Claude Skill 格式安裝即可使用
├── LICENSE.md         # CC BY-NC 4.0 授權條款（中英對照）
├── index.html         # 講義總覽頁（分類覆蓋地圖＋搜尋篩選），GitHub Pages 入口
└── 講義/               # 各講義 HTML 檔案存放處
```

---

## 授權

本專案以 [CC BY-NC 4.0](./LICENSE.md) 授權公開，僅限非商業用途，
歡迎自由使用、修改與分享，請保留原作者資訊。

---

## 聯絡與貢獻

歡迎：
- 提交 **Issue** 回報問題或建議
- 提交 **Pull Request** 貢獻使用範例或改善 Skill 內容

---

*Powered by Claude（Anthropic）*
